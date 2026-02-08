"""Integration tests for the practice session flow."""
import pytest
from app.models.classroom import Classroom, ClassEnrollment
from app.models.skill import Skill
from app.models.assignment import Assignment
from app.services.adaptation import SESSION_TOTAL, GROUP_SIZE, get_session_config


@pytest.fixture()
def classroom_with_assignment(db, teacher, student):
    """Set up a classroom, enrollment, skill, and active assignment."""
    classroom = Classroom(
        name="Test Class", class_code="TEST01", teacher_id=teacher.id,
    )
    db.add(classroom)
    db.flush()

    db.add(ClassEnrollment(classroom_id=classroom.id, student_id=student.id))
    db.flush()

    skill = Skill(
        domain="integers", name="Adding Integers", slug="test-int-add",
        description="Test", grade_level=5, difficulty_min=1, difficulty_max=5,
        problem_type="integer_addition", display_order=1,
    )
    db.add(skill)
    db.flush()

    assignment = Assignment(
        classroom_id=classroom.id, skill_id=skill.id,
        assigned_by=teacher.id, visual_supports=True,
    )
    db.add(assignment)
    db.flush()

    return {"classroom": classroom, "skill": skill, "assignment": assignment}


class TestPracticeFlow:
    def test_start_session(self, client, auth_student, classroom_with_assignment):
        aid = classroom_with_assignment["assignment"].id
        resp = client.post("/api/practice/start", json={"assignment_id": aid}, headers=auth_student)
        assert resp.status_code == 200
        data = resp.json()
        assert data["difficulty_level"] == 1
        assert data["visual_support_level"] == 3  # default with visuals on
        assert data["is_complete"] is False

    def test_get_problem(self, client, auth_student, classroom_with_assignment):
        aid = classroom_with_assignment["assignment"].id
        session = client.post("/api/practice/start", json={"assignment_id": aid}, headers=auth_student).json()
        resp = client.get(f"/api/practice/problem/{session['id']}", headers=auth_student)
        assert resp.status_code == 200
        data = resp.json()
        assert data["sequence_number"] == 1
        assert data["group_number"] == 1
        assert "prompt" in data["problem_data"]
        assert "correct_answer" not in data["problem_data"]  # stripped

    def test_submit_answer(self, client, auth_student, classroom_with_assignment):
        aid = classroom_with_assignment["assignment"].id
        session = client.post("/api/practice/start", json={"assignment_id": aid}, headers=auth_student).json()
        problem = client.get(f"/api/practice/problem/{session['id']}", headers=auth_student).json()

        resp = client.post("/api/practice/answer", json={
            "session_id": session["id"],
            "problem_id": problem["problem_id"],
            "student_answer": "999",  # almost certainly wrong
            "response_time_ms": 5000,
        }, headers=auth_student)
        assert resp.status_code == 200
        fb = resp.json()
        assert "is_correct" in fb
        assert "correct_answer" in fb
        assert "session_progress" in fb
        assert fb["session_progress"]["total"] == SESSION_TOTAL
        assert fb["session_progress"]["answered"] == 1  # no off-by-one

    def test_full_session_completes_at_15(self, client, auth_student, classroom_with_assignment):
        """Run a full 15-problem session and verify it completes correctly."""
        aid = classroom_with_assignment["assignment"].id
        session = client.post("/api/practice/start", json={"assignment_id": aid}, headers=auth_student).json()
        sid = session["id"]

        for i in range(SESSION_TOTAL):
            problem = client.get(f"/api/practice/problem/{sid}", headers=auth_student).json()
            assert problem["sequence_number"] == i + 1
            # Submit correct answer
            correct = problem["problem_data"].get("correct_answer")
            # correct_answer is stripped, so just submit something
            client.post("/api/practice/answer", json={
                "session_id": sid,
                "problem_id": problem["problem_id"],
                "student_answer": "0",
                "response_time_ms": 3000,
            }, headers=auth_student)

        # Trying to get problem 16 should fail
        resp = client.get(f"/api/practice/problem/{sid}", headers=auth_student)
        assert resp.status_code == 400
        assert "complete" in resp.json()["detail"].lower()

    def test_adaptation_fires_at_group_boundary(self, client, auth_student, classroom_with_assignment):
        """After answering problem 3, the adaptation should run."""
        aid = classroom_with_assignment["assignment"].id
        session = client.post("/api/practice/start", json={"assignment_id": aid}, headers=auth_student).json()
        sid = session["id"]
        initial_vis = session["visual_support_level"]

        # Answer 3 problems correctly (we need the actual correct answers)
        for i in range(GROUP_SIZE):
            problem = client.get(f"/api/practice/problem/{sid}", headers=auth_student).json()
            # We can't see the correct answer from the API, so we'll query it differently.
            # Submit the answer; we'll check that adaptation_reason appears on problem 3
            resp = client.post("/api/practice/answer", json={
                "session_id": sid,
                "problem_id": problem["problem_id"],
                "student_answer": "0",  # likely wrong
                "response_time_ms": 3000,
            }, headers=auth_student)

        fb = resp.json()
        # After problem 3 (group boundary), adaptation_reason should be non-empty
        # (regardless of whether student was right or wrong, adaptation runs)
        assert "adaptation_reason" in fb
        # The reason string should be non-empty since it's a boundary
        assert len(fb["adaptation_reason"]) > 0

    def test_unenrolled_student_rejected(self, client, db, classroom_with_assignment):
        """A student not in the class can't start a session."""
        from app.models.user import User
        from app.core.security import hash_password, create_access_token

        outsider = User(
            first_name="Outside", last_name="Kid", username="outsider",
            hashed_password=hash_password("pass"), role="student",
        )
        db.add(outsider)
        db.flush()
        token = create_access_token({"sub": str(outsider.id), "role": "student"})

        aid = classroom_with_assignment["assignment"].id
        resp = client.post("/api/practice/start",
            json={"assignment_id": aid},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
