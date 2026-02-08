"""
Practice session endpoints — the core student-facing API.
Handles starting sessions, generating problems, submitting answers,
and applying adaptation logic.
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.assignment import Assignment
from app.models.skill import Skill
from app.models.attempt import PracticeSession, StudentAttempt
from app.models.classroom import ClassEnrollment
from app.schemas.practice import (
    StartSessionRequest, SessionOut, ProblemOut,
    SubmitAnswerRequest, AnswerFeedback, SessionSummary,
)
from app.services.problem_generator import generate_problem
from app.services.adaptation import (
    adapt_after_group, compute_visual_trend,
    SESSION_TOTAL, GROUP_SIZE, NUM_GROUPS, get_group_number, is_group_boundary,
)

router = APIRouter(prefix="/api/practice", tags=["practice"])

SESSION_PROBLEM_COUNT = SESSION_TOTAL  # 15 problems, 5 groups of 3


@router.post("/start", response_model=SessionOut)
def start_session(
    req: StartSessionRequest,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_user),
):
    if student.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")

    assignment = db.query(Assignment).filter(
        Assignment.id == req.assignment_id, Assignment.is_active == True
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check enrollment
    enrolled = db.query(ClassEnrollment).filter(
        ClassEnrollment.classroom_id == assignment.classroom_id,
        ClassEnrollment.student_id == student.id,
        ClassEnrollment.is_active == True,
    ).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="Not enrolled in this class")

    # Determine starting levels from previous sessions.
    # First check this exact assignment, then fall back to ANY assignment
    # with the same skill for this student (cross-assignment memory).
    prev_sessions = (
        db.query(PracticeSession)
        .filter(
            PracticeSession.student_id == student.id,
            PracticeSession.assignment_id == assignment.id,
            PracticeSession.is_complete == True,
        )
        .order_by(PracticeSession.started_at.desc())
        .limit(3)
        .all()
    )

    if not prev_sessions:
        # Look for completed sessions on the same SKILL from other assignments
        same_skill_assignments = (
            db.query(Assignment.id)
            .filter(Assignment.skill_id == assignment.skill_id)
            .all()
        )
        same_skill_ids = [a[0] for a in same_skill_assignments]
        if same_skill_ids:
            prev_sessions = (
                db.query(PracticeSession)
                .filter(
                    PracticeSession.student_id == student.id,
                    PracticeSession.assignment_id.in_(same_skill_ids),
                    PracticeSession.is_complete == True,
                )
                .order_by(PracticeSession.started_at.desc())
                .limit(3)
                .all()
            )

    start_difficulty = 1
    start_visual = 3 if assignment.visual_supports else 1
    if prev_sessions:
        last = prev_sessions[0]
        start_difficulty = last.difficulty_level
        start_visual = last.visual_support_level

    session = PracticeSession(
        student_id=student.id,
        assignment_id=assignment.id,
        difficulty_level=start_difficulty,
        visual_support_level=start_visual,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionOut.model_validate(session)


@router.get("/problem/{session_id}", response_model=ProblemOut)
def get_next_problem(
    session_id: str,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_user),
):
    if student.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")

    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.student_id == student.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.is_complete:
        raise HTTPException(status_code=400, detail="Session already complete")

    assignment = db.query(Assignment).filter(Assignment.id == session.assignment_id).first()
    skill = db.query(Skill).filter(Skill.id == assignment.skill_id).first()

    # Current sequence
    attempt_count = (
        db.query(StudentAttempt)
        .filter(StudentAttempt.session_id == session.id)
        .count()
    )
    sequence = attempt_count + 1

    # Hard stop: do not generate beyond the session limit
    if sequence > SESSION_PROBLEM_COUNT:
        session.is_complete = True
        db.commit()
        raise HTTPException(status_code=400, detail="Session already complete")

    # ── Group-based difficulty & visual support ──
    # Every problem in a group uses the SAME difficulty and visual level.
    # The session's difficulty_level and visual_support_level are updated
    # at group boundaries (after answering the last problem in a group).
    # This means within a group the student gets a consistent experience,
    # and changes only happen between groups.
    difficulty = session.difficulty_level
    vis_level = session.visual_support_level
    show_visual = vis_level >= 2  # level 1 = no visual

    problem = generate_problem(skill.problem_type, difficulty, skill.config)
    problem_id = str(uuid.uuid4())

    # Store problem in the attempt (unanswered)
    attempt = StudentAttempt(
        id=problem_id,
        session_id=session.id,
        student_id=student.id,
        skill_id=skill.id,
        problem_data=problem,
        correct_answer=problem["correct_answer"],
        difficulty_level=difficulty,
        visual_support_shown=show_visual,
        sequence_number=sequence,
    )
    db.add(attempt)
    db.commit()

    # Strip correct answer and feedback explanation from response
    # (feedback_explanation is only shown after answering, via the feedback object)
    problem_display = {k: v for k, v in problem.items() if k not in ("correct_answer", "feedback_explanation")}
    if not show_visual:
        problem_display.pop("visual_hint", None)

    group = get_group_number(sequence)

    return ProblemOut(
        problem_id=problem_id,
        problem_data=problem_display,
        difficulty_level=difficulty,
        show_visual_support=show_visual,
        visual_support_level=vis_level,
        sequence_number=sequence,
        session_id=session.id,
        group_number=group,
        group_size=GROUP_SIZE,
        total_groups=NUM_GROUPS,
    )


@router.post("/answer", response_model=AnswerFeedback)
def submit_answer(
    req: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_user),
):
    if student.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")

    session = db.query(PracticeSession).filter(
        PracticeSession.id == req.session_id,
        PracticeSession.student_id == student.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    attempt = db.query(StudentAttempt).filter(
        StudentAttempt.id == req.problem_id,
        StudentAttempt.session_id == session.id,
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Record answer
    is_correct = req.student_answer.strip() == attempt.correct_answer.strip()
    attempt.student_answer = req.student_answer
    attempt.is_correct = is_correct
    attempt.response_time_ms = req.response_time_ms

    # Build instructional feedback
    problem_data = attempt.problem_data
    # Build a complete visual hint for feedback (may include answer data)
    feedback_hint = dict(problem_data.get("visual_hint", {}))
    ptype = problem_data.get("type", "")
    if ptype == "equivalent_fractions":
        # For feedback, always include full target fraction so bar renders correctly
        if problem_data.get("missing") == "numerator":
            feedback_hint["right_numerator"] = int(attempt.correct_answer)
        else:
            feedback_hint["right_denominator"] = int(attempt.correct_answer)
            if "right_numerator" not in feedback_hint:
                feedback_hint["right_numerator"] = problem_data.get("target_numerator")

    feedback = {
        "explanation": problem_data.get("feedback_explanation", ""),
        "visual_hint": feedback_hint,
    }
    if not is_correct:
        feedback["correction"] = f"The correct answer is {attempt.correct_answer}."
        feedback["show_visual"] = True
    else:
        feedback["encouragement"] = "That's right!"
        feedback["show_visual"] = False

    attempt.feedback_given = feedback

    # Update session stats
    session.total_problems = (
        db.query(StudentAttempt)
        .filter(StudentAttempt.session_id == session.id, StudentAttempt.student_answer.isnot(None))
        .count()
    )
    session.correct_count = (
        db.query(StudentAttempt)
        .filter(StudentAttempt.session_id == session.id, StudentAttempt.is_correct == True)
        .count()
    )

    total_answered = session.total_problems
    seq = attempt.sequence_number

    # ── Adaptation at group boundaries ──
    # After the last problem in each group (every GROUP_SIZE answers),
    # evaluate THAT GROUP's performance and adjust for the next group.
    adaptation_reason = ""
    if is_group_boundary(seq) and seq < SESSION_PROBLEM_COUNT:
        # Get this group's attempts
        group_start = seq - GROUP_SIZE + 1
        group_attempts = (
            db.query(StudentAttempt)
            .filter(
                StudentAttempt.session_id == session.id,
                StudentAttempt.is_correct.isnot(None),
                StudentAttempt.sequence_number >= group_start,
                StudentAttempt.sequence_number <= seq,
            )
            .order_by(StudentAttempt.sequence_number)
            .all()
        )
        group_correct = [a.is_correct for a in group_attempts]
        group_times = [a.response_time_ms for a in group_attempts if a.response_time_ms]

        assignment = db.query(Assignment).filter(Assignment.id == session.assignment_id).first()
        skill = db.query(Skill).filter(Skill.id == assignment.skill_id).first()
        max_diff = skill.difficulty_max if skill else 5

        result = adapt_after_group(
            group_correct, group_times,
            session.difficulty_level, session.visual_support_level, max_diff,
        )
        session.difficulty_level = result.new_difficulty
        session.visual_support_level = result.new_visual_level
        adaptation_reason = result.reason

    # Check completion
    remaining = max(0, SESSION_PROBLEM_COUNT - total_answered)
    if remaining == 0:
        session.is_complete = True
        session.completed_at = datetime.now(timezone.utc)
        all_times = (
            db.query(StudentAttempt.response_time_ms)
            .filter(
                StudentAttempt.session_id == session.id,
                StudentAttempt.response_time_ms.isnot(None),
            )
            .all()
        )
        times = [t[0] for t in all_times if t[0]]
        session.avg_response_time_ms = sum(times) / len(times) if times else None

    db.commit()

    return AnswerFeedback(
        is_correct=is_correct,
        correct_answer=attempt.correct_answer,
        feedback=feedback,
        show_visual=not is_correct or session.visual_support_level >= 2,
        next_difficulty=session.difficulty_level,
        next_visual_level=session.visual_support_level,
        adaptation_reason=adaptation_reason,
        session_progress={
            "total": SESSION_PROBLEM_COUNT,
            "correct": session.correct_count,
            "answered": total_answered,
            "remaining": remaining,
        },
    )


@router.get("/session/{session_id}/summary", response_model=SessionSummary)
def get_session_summary(
    session_id: str,
    db: Session = Depends(get_db),
    student: User = Depends(get_current_user),
):
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.student_id == student.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    accuracy = session.correct_count / session.total_problems if session.total_problems else 0
    avg_time = session.avg_response_time_ms or 0

    # Compare with previous sessions
    prev = (
        db.query(PracticeSession)
        .filter(
            PracticeSession.student_id == student.id,
            PracticeSession.assignment_id == session.assignment_id,
            PracticeSession.is_complete == True,
            PracticeSession.id != session.id,
        )
        .order_by(PracticeSession.completed_at.desc())
        .first()
    )

    if prev and prev.avg_response_time_ms and avg_time < prev.avg_response_time_ms:
        message = "You're faster than last time! Great work!"
    elif prev and prev.correct_count and session.correct_count > prev.correct_count:
        message = "More correct answers than last time — keep it up!"
    elif accuracy >= 0.85:
        message = "Excellent work! You really know this!"
    elif accuracy >= 0.6:
        message = "Good effort! You're getting better!"
    else:
        message = "Keep practicing — you'll get there!"

    # Visual support trend
    visual_levels = (
        db.query(PracticeSession.visual_support_level)
        .filter(
            PracticeSession.student_id == student.id,
            PracticeSession.assignment_id == session.assignment_id,
            PracticeSession.is_complete == True,
        )
        .order_by(PracticeSession.completed_at)
        .all()
    )
    levels = [v[0] for v in visual_levels]
    trend = compute_visual_trend(levels)

    return SessionSummary(
        session_id=session.id,
        total_problems=session.total_problems,
        correct_count=session.correct_count,
        accuracy_pct=round(accuracy * 100, 1),
        avg_response_time_ms=round(avg_time, 0),
        improvement_message=message,
        visual_support_trend=trend,
    )
