from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime


class StartSessionRequest(BaseModel):
    assignment_id: str


class SessionOut(BaseModel):
    id: str
    assignment_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_problems: int
    correct_count: int
    avg_response_time_ms: Optional[float] = None
    visual_support_level: int
    difficulty_level: int
    is_complete: bool

    class Config:
        from_attributes = True


class ProblemOut(BaseModel):
    problem_id: str
    problem_data: dict
    difficulty_level: int
    show_visual_support: bool
    visual_support_level: int  # 1-5 for frontend scaffolding decisions
    sequence_number: int
    session_id: str
    group_number: int = 1       # which group (1-5)
    group_size: int = 3         # problems per group
    total_groups: int = 5       # total groups in session


class SubmitAnswerRequest(BaseModel):
    session_id: str
    problem_id: str
    student_answer: str
    response_time_ms: int


class AnswerFeedback(BaseModel):
    is_correct: bool
    correct_answer: str
    feedback: dict
    show_visual: bool
    next_difficulty: int
    next_visual_level: int
    adaptation_reason: str = ""   # human-readable explanation of any adaptation
    session_progress: dict


class SessionSummary(BaseModel):
    session_id: str
    total_problems: int
    correct_count: int
    accuracy_pct: float
    avg_response_time_ms: float
    improvement_message: str
    visual_support_trend: str


class ProgressSummary(BaseModel):
    student_id: str
    student_name: str
    skill_name: str
    sessions_completed: int
    overall_accuracy: float
    avg_response_time_ms: float
    fluency_status: str
    visual_support_trend: str
    recent_sessions: List[SessionOut]

    class Config:
        from_attributes = True


class ClassProgressOut(BaseModel):
    classroom_id: str
    classroom_name: str
    skill_id: str
    skill_name: str
    students: List[ProgressSummary]
    class_accuracy: float
    class_avg_time_ms: float
