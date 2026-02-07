from pydantic import BaseModel
from typing import Optional


class SkillOut(BaseModel):
    id: str
    domain: str
    name: str
    slug: str
    description: Optional[str] = None
    grade_level: int
    difficulty_min: int
    difficulty_max: int
    problem_type: str
    display_order: int

    class Config:
        from_attributes = True


class SkillBrief(BaseModel):
    id: str
    domain: str
    name: str
    slug: str
    problem_type: str

    class Config:
        from_attributes = True
