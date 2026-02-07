from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AssignmentCreate(BaseModel):
    skill_id: str
    classroom_id: str
    title: Optional[str] = None
    time_limit_seconds: Optional[int] = None
    visual_supports: bool = True
    target_student_ids: Optional[List[str]] = None
    due_date: Optional[datetime] = None


class AssignmentOut(BaseModel):
    id: str
    classroom_id: str
    skill_id: str
    skill_name: Optional[str] = None
    skill_domain: Optional[str] = None
    title: Optional[str] = None
    time_limit_seconds: Optional[int] = None
    visual_supports: bool
    is_active: bool
    created_at: datetime
    due_date: Optional[datetime] = None
    completion_count: Optional[int] = 0
    total_students: Optional[int] = 0

    class Config:
        from_attributes = True


class StudentAssignmentOut(BaseModel):
    id: str
    skill_name: str
    skill_domain: str
    skill_slug: str
    problem_type: str
    visual_supports: bool
    time_limit_seconds: Optional[int] = None
    is_completed: bool = False

    class Config:
        from_attributes = True
