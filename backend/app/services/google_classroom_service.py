"""
Google Classroom API service for Level 2 integration.

Responsibilities:
  - Fetch teacher's Classroom courses
  - Import Classroom courses as NumberSense classrooms
  - Post a NumberSense assignment as Classroom coursework
  - Prevent duplicate posts for the same assignment + course

All calls are logged for observability.
"""
import logging
import random
import string
from typing import List, Optional
from datetime import datetime

from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.google_classroom import GoogleClassroomLink
from app.models.classroom import Classroom, ClassEnrollment
from app.models.assignment import Assignment
from app.models.user import User
from app.models.skill import Skill
from app.services.google_auth_service import get_credentials

logger = logging.getLogger("numbersense.google_classroom")


def _build_service(db: Session, teacher_id: str):
    """Build a Google Classroom API service using the teacher's credentials."""
    creds = get_credentials(db, teacher_id)
    return build("classroom", "v1", credentials=creds, cache_discovery=False)


# ---------------------------------------------------------------------------
# Fetch courses
# ---------------------------------------------------------------------------

def list_courses(db: Session, teacher_id: str, *, _service=None) -> List[dict]:
    """Return a list of the teacher's active Google Classroom courses.

    Each item has: id, name, section, descriptionHeading.
    """
    service = _service or _build_service(db, teacher_id)
    logger.info("Fetching Classroom courses for teacher %s", teacher_id)

    courses = []
    page_token = None
    while True:
        resp = service.courses().list(
            teacherId="me",
            courseStates=["ACTIVE"],
            pageSize=50,
            pageToken=page_token,
        ).execute()

        for c in resp.get("courses", []):
            courses.append({
                "id": c["id"],
                "name": c.get("name", ""),
                "section": c.get("section", ""),
                "description_heading": c.get("descriptionHeading", ""),
            })

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    logger.info("Found %d active courses for teacher %s", len(courses), teacher_id)
    return courses


# ---------------------------------------------------------------------------
# Post assignment
# ---------------------------------------------------------------------------

def post_assignment(
    db: Session,
    teacher_id: str,
    assignment_id: str,
    course_id: str,
    due_date: Optional[datetime] = None,
) -> dict:
    """Post a NumberSense assignment to Google Classroom as coursework.

    Returns a dict with the created coursework details.
    Raises ValueError on duplicate or missing data.
    """
    # Check for duplicate
    existing = db.query(GoogleClassroomLink).filter(
        GoogleClassroomLink.assignment_id == assignment_id,
        GoogleClassroomLink.classroom_course_id == course_id,
    ).first()
    if existing:
        raise ValueError(
            "This assignment has already been posted to this Google Classroom course."
        )

    # Look up the NumberSense assignment + skill
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise ValueError("Assignment not found")

    skill = db.query(Skill).filter(Skill.id == assignment.skill_id).first()
    skill_name = skill.name if skill else "Practice"

    # Build the deep link using the share token (no login required)
    share_token = assignment.share_token
    if not share_token:
        # Backfill share_token if missing
        import secrets as _secrets
        share_token = _secrets.token_urlsafe(16)
        assignment.share_token = share_token
        db.flush()

    deep_link = f"{settings.NUMBERSENSE_BASE_URL}/go/{share_token}"

    # Build coursework body
    coursework_body = {
        "title": f"NumberSense: {skill_name}",
        "description": (
            "Complete the assigned NumberSense practice. "
            "Click the link below to begin."
        ),
        "materials": [
            {"link": {"url": deep_link, "title": f"Open NumberSense: {skill_name}"}}
        ],
        "workType": "ASSIGNMENT",
        "state": "PUBLISHED",
    }

    # Optional due date
    if due_date:
        coursework_body["dueDate"] = {
            "year": due_date.year,
            "month": due_date.month,
            "day": due_date.day,
        }
        coursework_body["dueTime"] = {
            "hours": 23,
            "minutes": 59,
        }

    # Post to Google Classroom
    service = _build_service(db, teacher_id)
    logger.info(
        "Posting assignment %s to Classroom course %s (teacher %s)",
        assignment_id, course_id, teacher_id,
    )

    try:
        coursework = service.courses().courseWork().create(
            courseId=course_id,
            body=coursework_body,
        ).execute()
    except Exception as exc:
        logger.error(
            "Failed to post assignment %s to course %s: %s",
            assignment_id, course_id, exc,
        )
        raise ValueError(
            "Failed to post to Google Classroom. Please try again or reconnect."
        ) from exc

    coursework_id = coursework["id"]

    # Get course name for display
    course_name = ""
    try:
        course = service.courses().get(id=course_id).execute()
        course_name = course.get("name", "")
    except Exception:
        pass

    # Store the link
    link = GoogleClassroomLink(
        assignment_id=assignment_id,
        classroom_course_id=course_id,
        classroom_coursework_id=coursework_id,
        course_name=course_name,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    logger.info(
        "Successfully posted coursework %s to course %s for assignment %s",
        coursework_id, course_id, assignment_id,
    )

    return {
        "coursework_id": coursework_id,
        "course_id": course_id,
        "course_name": course_name,
        "title": coursework.get("title", ""),
        "link": deep_link,
    }


def get_links_for_assignment(db: Session, assignment_id: str) -> List[dict]:
    """Return all Google Classroom links for a given assignment."""
    links = db.query(GoogleClassroomLink).filter(
        GoogleClassroomLink.assignment_id == assignment_id
    ).all()
    return [
        {
            "id": link.id,
            "course_id": link.classroom_course_id,
            "coursework_id": link.classroom_coursework_id,
            "course_name": link.course_name,
            "created_at": link.created_at.isoformat() if link.created_at else None,
        }
        for link in links
    ]


# ---------------------------------------------------------------------------
# Import courses as NumberSense classrooms
# ---------------------------------------------------------------------------

def _generate_class_code(db: Session) -> str:
    """Generate a unique 6-character class code."""
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not db.query(Classroom).filter(Classroom.class_code == code).first():
            return code


def _fetch_roster(service, course_id: str) -> List[dict]:
    """Fetch all students in a Google Classroom course.

    Returns a list of dicts with name and email.
    """
    students = []
    page_token = None
    while True:
        try:
            resp = service.courses().students().list(
                courseId=course_id,
                pageSize=100,
                pageToken=page_token,
            ).execute()
        except Exception as exc:
            logger.warning("Failed to fetch roster for course %s: %s", course_id, exc)
            break

        for s in resp.get("students", []):
            profile = s.get("profile", {})
            name = profile.get("name", {})
            students.append({
                "google_id": profile.get("id", ""),
                "email": profile.get("emailAddress", ""),
                "first_name": name.get("givenName", ""),
                "last_name": name.get("familyName", ""),
            })

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return students


def _enroll_students(db: Session, classroom_id: str, roster: List[dict]) -> int:
    """Create User records and enroll students in a NumberSense classroom.

    - Matches existing users by username (first.last) to avoid duplicates.
    - Students get a default password of 'student' (they use class code login).
    - Returns the number of newly enrolled students.
    """
    enrolled_count = 0

    for s in roster:
        first = s.get("first_name", "").strip()
        last = s.get("last_name", "").strip()
        if not first or not last:
            continue

        username = f"{first.lower()}.{last.lower()}"

        # Find or create user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(
                first_name=first,
                last_name=last,
                username=username,
                hashed_password=hash_password("student"),
                role="student",
            )
            db.add(user)
            db.flush()

        # Check if already enrolled
        existing_enrollment = db.query(ClassEnrollment).filter(
            ClassEnrollment.classroom_id == classroom_id,
            ClassEnrollment.student_id == user.id,
        ).first()

        if existing_enrollment:
            if not existing_enrollment.is_active:
                existing_enrollment.is_active = True
                enrolled_count += 1
        else:
            db.add(ClassEnrollment(
                classroom_id=classroom_id,
                student_id=user.id,
            ))
            enrolled_count += 1

    return enrolled_count


def import_courses(db: Session, teacher_id: str) -> List[dict]:
    """Fetch Google Classroom courses, create NumberSense classrooms, and
    import student rosters.

    Skips courses that have already been imported (matched by google_course_id),
    but still syncs their rosters to pick up new students.
    Returns a list of dicts describing each imported or existing classroom.
    """
    service = _build_service(db, teacher_id)
    google_courses = list_courses(db, teacher_id, _service=service)
    results = []

    for gc in google_courses:
        course_id = gc["id"]
        course_name = gc["name"]
        section = gc.get("section", "")
        display_name = f"{course_name} — {section}" if section else course_name

        # Check if already imported
        existing = db.query(Classroom).filter(
            Classroom.google_course_id == course_id
        ).first()

        if existing:
            # Still sync roster for existing classrooms
            roster = _fetch_roster(service, course_id)
            new_students = _enroll_students(db, existing.id, roster)

            student_count = (
                db.query(ClassEnrollment)
                .filter(ClassEnrollment.classroom_id == existing.id,
                        ClassEnrollment.is_active == True)
                .count()
            )
            if new_students > 0:
                logger.info("Synced %d new students into existing class %s",
                            new_students, existing.name)

            results.append({
                "id": existing.id,
                "name": existing.name,
                "class_code": existing.class_code,
                "google_course_id": course_id,
                "status": "already_imported",
                "student_count": student_count,
                "new_students": new_students,
            })
            continue

        # Create new classroom
        classroom = Classroom(
            name=display_name,
            class_code=_generate_class_code(db),
            teacher_id=teacher_id,
            google_course_id=course_id,
        )
        db.add(classroom)
        db.flush()

        # Import roster
        roster = _fetch_roster(service, course_id)
        new_students = _enroll_students(db, classroom.id, roster)

        logger.info(
            "Imported course '%s' (id=%s) with %d students for teacher %s",
            display_name, course_id, new_students, teacher_id,
        )

        results.append({
            "id": classroom.id,
            "name": classroom.name,
            "class_code": classroom.class_code,
            "google_course_id": course_id,
            "status": "imported",
            "student_count": new_students,
            "new_students": new_students,
        })

    db.commit()
    return results
