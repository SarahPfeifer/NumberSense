import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False)
    class_code = Column(String(10), unique=True, nullable=False)
    teacher_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    clever_section_id = Column(String(255), unique=True, nullable=True)
    google_course_id = Column(String(255), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    teacher = relationship("User", back_populates="taught_classes", foreign_keys=[teacher_id])
    enrollments = relationship("ClassEnrollment", back_populates="classroom", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="classroom", cascade="all, delete-orphan")


class ClassEnrollment(Base):
    __tablename__ = "class_enrollments"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    classroom_id = Column(String(36), ForeignKey("classrooms.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    enrolled_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    classroom = relationship("Classroom", back_populates="enrollments")
    student = relationship("User", back_populates="enrollments")
