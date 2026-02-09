"""
Google Classroom API service for Level 2 integration.

Responsibilities:
  - Fetch teacher's Classroom courses
  - Post a NumberSense assignment as Classroom coursework
  - Prevent duplicate posts for the same assignment + course

All calls are logged for observability.
"""
import logging
from typing import List, Optional
from datetime import datetime

from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.google_classroom import GoogleClassroomLink
from app.models.assignment import Assignment
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

def list_courses(db: Session, teacher_id: str) -> List[dict]:
    """Return a list of the teacher's active Google Classroom courses.

    Each item has: id, name, section, descriptionHeading.
    """
    service = _build_service(db, teacher_id)
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

    # Build the deep link
    deep_link = f"{settings.NUMBERSENSE_BASE_URL}/student/practice/{assignment_id}?source=classroom"

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
