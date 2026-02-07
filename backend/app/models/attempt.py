import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class PracticeSession(Base):
    """A single practice session (5-10 minutes) by a student for an assignment."""
    __tablename__ = "practice_sessions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    assignment_id = Column(String(36), ForeignKey("assignments.id"), nullable=False)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    total_problems = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, nullable=True)
    visual_support_level = Column(Integer, default=3)  # 1-5, starts at assigned level
    difficulty_level = Column(Integer, default=1)       # current adapted difficulty
    is_complete = Column(Boolean, default=False)

    # Relationships
    student = relationship("User")
    assignment = relationship("Assignment", back_populates="sessions")
    attempts = relationship("StudentAttempt", back_populates="session", cascade="all, delete-orphan")


class StudentAttempt(Base):
    """Individual problem attempt within a practice session."""
    __tablename__ = "student_attempts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    session_id = Column(String(36), ForeignKey("practice_sessions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    skill_id = Column(String(36), ForeignKey("skills.id"), nullable=False)
    problem_data = Column(JSON, nullable=False)         # the generated problem
    student_answer = Column(String(500), nullable=True)
    correct_answer = Column(String(500), nullable=False)
    is_correct = Column(Boolean, nullable=True)
    response_time_ms = Column(Integer, nullable=True)   # milliseconds
    difficulty_level = Column(Integer, nullable=False)
    visual_support_shown = Column(Boolean, default=False)
    feedback_given = Column(JSON, nullable=True)        # instructional feedback data
    sequence_number = Column(Integer, nullable=False)   # order within session
    attempted_at = Column(DateTime, server_default=func.now())

    # Relationships
    session = relationship("PracticeSession", back_populates="attempts")
    student = relationship("User", back_populates="attempts")
    skill = relationship("Skill")
