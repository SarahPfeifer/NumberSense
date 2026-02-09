"""
Google Classroom integration endpoints.

All endpoints require teacher authentication.
"""
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_teacher
from app.models.user import User
from app.services import google_auth_service, google_classroom_service

logger = logging.getLogger("numbersense.google_classroom_api")

router = APIRouter(prefix="/api/google", tags=["google-classroom"])


# ── Schemas ────────────────────────────────────────────────

class OAuthCallbackRequest(BaseModel):
    code: str

class PostAssignmentRequest(BaseModel):
    assignment_id: str
    course_id: str
    due_date: Optional[datetime] = None


# ── OAuth endpoints ────────────────────────────────────────

@router.get("/oauth/url")
def get_oauth_url(teacher: User = Depends(require_teacher)):
    """Return the Google OAuth consent URL for the teacher to visit."""
    url = google_auth_service.build_oauth_url(state=teacher.id)
    return {"redirect_url": url}


@router.post("/oauth/callback")
def oauth_callback(
    req: OAuthCallbackRequest,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """Exchange the authorization code for tokens, store them, and import courses."""
    try:
        token_data = google_auth_service.exchange_code(req.code)
    except Exception as exc:
        logger.error("Google OAuth exchange failed for teacher %s: %s", teacher.id, exc)
        raise HTTPException(
            status_code=400,
            detail="Failed to connect Google Classroom. Please try again.",
        )

    google_auth_service.save_tokens(db, teacher.id, token_data)
    logger.info("Teacher %s connected Google Classroom (email=%s)",
                teacher.id, token_data.get("google_email"))

    # Auto-import courses as NumberSense classrooms
    imported = []
    try:
        imported = google_classroom_service.import_courses(db, teacher.id)
    except Exception as exc:
        logger.warning("Auto-import courses failed for teacher %s: %s", teacher.id, exc)

    return {
        "connected": True,
        "google_email": token_data.get("google_email", ""),
        "imported_courses": imported,
    }


@router.get("/status")
def connection_status(
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """Check if the teacher has connected Google Classroom."""
    return google_auth_service.is_connected(db, teacher.id)


@router.post("/disconnect")
def disconnect(
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """Revoke tokens and disconnect Google Classroom."""
    google_auth_service.disconnect(db, teacher.id)
    return {"connected": False}


# ── Classroom API endpoints ────────────────────────────────

@router.get("/classroom/courses")
def list_courses(
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """Fetch the teacher's active Google Classroom courses."""
    try:
        courses = google_classroom_service.list_courses(db, teacher.id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to fetch courses for teacher %s: %s", teacher.id, exc)
        raise HTTPException(
            status_code=502,
            detail="Could not fetch courses from Google Classroom. Please try again.",
        )
    return {"courses": courses}


@router.post("/classroom/post-assignment")
def post_assignment(
    req: PostAssignmentRequest,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """Post a NumberSense assignment to Google Classroom."""
    try:
        result = google_classroom_service.post_assignment(
            db=db,
            teacher_id=teacher.id,
            assignment_id=req.assignment_id,
            course_id=req.course_id,
            due_date=req.due_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to post assignment for teacher %s: %s", teacher.id, exc)
        raise HTTPException(
            status_code=502,
            detail="Failed to post to Google Classroom. Please try again.",
        )
    return result


@router.post("/classroom/import-courses")
def import_courses(
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """Import Google Classroom courses as NumberSense classes.

    Skips courses that have already been imported. Can be called
    multiple times safely to pick up newly created courses.
    """
    try:
        results = google_classroom_service.import_courses(db, teacher.id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to import courses for teacher %s: %s", teacher.id, exc)
        raise HTTPException(
            status_code=502,
            detail="Could not import courses from Google Classroom. Please try again.",
        )
    return {"courses": results}


@router.get("/classroom/assignment-links/{assignment_id}")
def get_assignment_links(
    assignment_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """Get Google Classroom links for a specific assignment."""
    links = google_classroom_service.get_links_for_assignment(db, assignment_id)
    return {"links": links}
