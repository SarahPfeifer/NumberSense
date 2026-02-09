"""
Models for Google Classroom integration (Level 2).

GoogleAccount stores OAuth tokens for teachers who have connected their Google account.
GoogleClassroomLink tracks assignments that have been posted to Google Classroom.
"""
import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class GoogleAccount(Base):
    """Stores a teacher's Google OAuth credentials (encrypted at rest)."""
    __tablename__ = "google_accounts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    teacher_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    google_user_id = Column(String(255), nullable=False)
    google_email = Column(String(255), nullable=True)
    access_token_enc = Column(Text, nullable=False)       # Fernet-encrypted
    refresh_token_enc = Column(Text, nullable=False)       # Fernet-encrypted
    token_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class GoogleClassroomLink(Base):
    """Maps a NumberSense assignment to a Google Classroom coursework item."""
    __tablename__ = "google_classroom_links"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    assignment_id = Column(String(36), ForeignKey("assignments.id"), nullable=False)
    classroom_course_id = Column(String(255), nullable=False)
    classroom_coursework_id = Column(String(255), nullable=False)
    course_name = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("assignment_id", "classroom_course_id",
                         name="uq_assignment_course"),
    )
