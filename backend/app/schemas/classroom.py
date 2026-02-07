from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ClassroomCreate(BaseModel):
    name: str


class ClassroomOut(BaseModel):
    id: str
    name: str
    class_code: str
    teacher_id: str
    is_active: bool
    created_at: datetime
    student_count: Optional[int] = 0

    class Config:
        from_attributes = True


class EnrollStudentRequest(BaseModel):
    first_name: str
    last_name: str
    username: Optional[str] = None


class EnrollmentOut(BaseModel):
    id: str
    student_id: str
    student_name: str
    enrolled_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
