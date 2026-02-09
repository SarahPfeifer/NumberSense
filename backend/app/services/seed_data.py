"""
Seed the database with math skills for all three MVP domains.
Also creates a demo teacher and demo class for testing.
"""
from sqlalchemy.orm import Session
from app.models.skill import Skill
from app.models.user import User
from app.models.classroom import Classroom, ClassEnrollment
from app.core.security import hash_password

SKILLS = [
    # ── FRACTIONS ──────────────────────────────────────────
    {
        "domain": "fractions",
        "name": "Compare Fractions",
        "slug": "fraction-comparison",
        "description": "Compare two fractions using reasoning and visual models.",
        "grade_level": 4,
        "difficulty_min": 1,
        "difficulty_max": 5,
        "problem_type": "fraction_comparison",
        "display_order": 1,
    },
    {
        "domain": "fractions",
        "name": "Compare Fractions to Benchmarks (0, ½, 1)",
        "slug": "fraction-benchmark",
        "description": "Determine if a fraction is less than, equal to, or greater than benchmark values.",
        "grade_level": 4,
        "difficulty_min": 1,
        "difficulty_max": 5,
        "problem_type": "fraction_comparison_benchmark",
        "display_order": 2,
    },
    {
        "domain": "fractions",
        "name": "Equivalent Fractions",
        "slug": "equivalent-fractions",
        "description": "Find equivalent fractions by identifying multiplying patterns.",
        "grade_level": 4,
        "difficulty_min": 1,
        "difficulty_max": 5,
        "problem_type": "equivalent_fractions",
        "display_order": 3,
    },
    {
        "domain": "fractions",
        "name": "Fractions on a Number Line",
        "slug": "fraction-number-line",
        "description": "Place and identify fractions on a number line between 0 and 1.",
        "grade_level": 4,
        "difficulty_min": 1,
        "difficulty_max": 5,
        "problem_type": "fraction_number_line",
        "display_order": 4,
    },

    # ── COMBINING INTEGERS ─────────────────────────────────
    # Conceptual foundations first, then operations
    {
        "domain": "integers",
        "name": "Integers on a Number Line",
        "slug": "integer-number-line",
        "description": "Identify integers on a number line including negative values.",
        "grade_level": 5,
        "difficulty_min": 1,
        "difficulty_max": 5,
        "problem_type": "integer_number_line",
        "display_order": 1,
    },
    {
        "domain": "integers",
        "name": "Adding Integers",
        "slug": "integer-addition",
        "description": "Add positive and negative integers using number line reasoning.",
        "grade_level": 5,
        "difficulty_min": 1,
        "difficulty_max": 5,
        "problem_type": "integer_addition",
        "display_order": 2,
    },
    {
        "domain": "integers",
        "name": "Subtracting Integers",
        "slug": "integer-subtraction",
        "description": "Subtract integers, reasoning about direction on a number line.",
        "grade_level": 5,
        "difficulty_min": 1,
        "difficulty_max": 5,
        "problem_type": "integer_subtraction",
        "display_order": 3,
    },

    # ── MULTIPLICATION FLUENCY ─────────────────────────────
    {
        "domain": "multiplication",
        "name": "Multiplication Facts (0–12)",
        "slug": "multiplication-facts",
        "description": "Build fluency with basic multiplication facts from 0×0 to 12×12.",
        "grade_level": 4,
        "difficulty_min": 1,
        "difficulty_max": 5,
        "problem_type": "multiplication_facts",
        "display_order": 1,
    },
]


REMOVED_SLUGS = ["multiplication-related-facts", "integer-magnitude", "multiplication-scaling"]


def seed_skills(db: Session):
    """Insert skills if not already present, and update display_order for existing ones."""
    from app.models.assignment import Assignment

    for skill_data in SKILLS:
        existing = db.query(Skill).filter(Skill.slug == skill_data["slug"]).first()
        if not existing:
            db.add(Skill(**skill_data))
        else:
            # Keep display_order in sync with seed data
            if existing.display_order != skill_data["display_order"]:
                existing.display_order = skill_data["display_order"]

    # Clean up removed skills and their dependent data
    from app.models.attempt import PracticeSession, StudentAttempt

    for slug in REMOVED_SLUGS:
        old = db.query(Skill).filter(Skill.slug == slug).first()
        if old:
            assignments = db.query(Assignment).filter(Assignment.skill_id == old.id).all()
            for a in assignments:
                sessions = db.query(PracticeSession).filter(PracticeSession.assignment_id == a.id).all()
                for s in sessions:
                    db.query(StudentAttempt).filter(StudentAttempt.session_id == s.id).delete()
                    db.delete(s)
                db.delete(a)
            db.delete(old)

    db.commit()


def seed_demo_data(db: Session):
    """Create demo teacher, students, and a class for testing."""
    # Demo teacher
    teacher = db.query(User).filter(User.username == "demo.teacher").first()
    if not teacher:
        teacher = User(
            first_name="Sarah",
            last_name="Pfeifer",
            username="demo.teacher",
            email="teacher@numbersense.dev",
            hashed_password=hash_password("teacher123"),
            role="teacher",
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)

    # Demo class
    classroom = db.query(Classroom).filter(Classroom.class_code == "DEMO01").first()
    if not classroom:
        classroom = Classroom(
            name="Mrs. Pfeifer's 4th Grade Math",
            class_code="DEMO01",
            teacher_id=teacher.id,
        )
        db.add(classroom)
        db.commit()
        db.refresh(classroom)

    # Demo students
    demo_students = [
        ("Alex", "Johnson"), ("Maria", "Garcia"), ("James", "Wilson"),
        ("Emma", "Brown"), ("Liam", "Davis"), ("Sophia", "Martinez"),
        ("Noah", "Anderson"), ("Olivia", "Taylor"),
    ]
    for first, last in demo_students:
        username = f"{first.lower()}.{last.lower()}"
        student = db.query(User).filter(User.username == username).first()
        if not student:
            student = User(
                first_name=first,
                last_name=last,
                username=username,
                hashed_password=hash_password("student"),
                role="student",
            )
            db.add(student)
            db.commit()
            db.refresh(student)

        # Enroll
        existing = db.query(ClassEnrollment).filter(
            ClassEnrollment.classroom_id == classroom.id,
            ClassEnrollment.student_id == student.id,
        ).first()
        if not existing:
            db.add(ClassEnrollment(classroom_id=classroom.id, student_id=student.id))
    db.commit()
