from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    first_name: str
    last_name: str
    role: str


class UserCreate(UserBase):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: str
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class ClassCodeLogin(BaseModel):
    class_code: str
    student_identifier: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
