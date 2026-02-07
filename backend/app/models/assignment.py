import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    classroom_id = Column(String(36), ForeignKey("classrooms.id"), nullable=False)
    skill_id = Column(String(36), ForeignKey("skills.id"), nullable=False)
    assigned_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=True)
    time_limit_seconds = Column(Integer, nullable=True)       # optional time limit
    visual_supports = Column(Boolean, default=True)           # teacher can toggle
    target_student_ids = Column(JSON, nullable=True)          # null = entire class
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    due_date = Column(DateTime, nullable=True)

    # Relationships
    classroom = relationship("Classroom", back_populates="assignments")
    skill = relationship("Skill", back_populates="assignments")
    teacher = relationship("User", foreign_keys=[assigned_by])
    sessions = relationship("PracticeSession", back_populates="assignment", cascade="all, delete-orphan")
