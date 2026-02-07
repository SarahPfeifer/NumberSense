import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, hash_password, create_access_token, get_current_user
from app.models.user import User
from app.models.classroom import Classroom, ClassEnrollment
from app.schemas.user import (
    LoginRequest, ClassCodeLogin, TokenResponse, UserOut, UserCreate,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Standard username/password login for teachers and students."""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/class-code-login", response_model=TokenResponse)
def class_code_login(req: ClassCodeLogin, db: Session = Depends(get_db)):
    """Fallback login: student enters class code + their identifier."""
    classroom = db.query(Classroom).filter(
        Classroom.class_code == req.class_code.upper(),
        Classroom.is_active == True,
    ).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")

    # Find student in that class by matching identifier
    identifier = req.student_identifier.strip().lower()
    enrollments = (
        db.query(ClassEnrollment)
        .filter(ClassEnrollment.classroom_id == classroom.id, ClassEnrollment.is_active == True)
        .all()
    )
    for enrollment in enrollments:
        student = db.query(User).filter(User.id == enrollment.student_id).first()
        if student:
            full = f"{student.first_name} {student.last_name[0]}".lower()
            uname = (student.username or "").lower()
            if identifier == full or identifier == uname or identifier == student.first_name.lower():
                token = create_access_token({"sub": str(student.id), "role": "student"})
                return TokenResponse(access_token=token, user=UserOut.model_validate(student))

    raise HTTPException(status_code=401, detail="Student not found in this class")


@router.get("/clever/redirect")
def clever_redirect():
    """Return the Clever OAuth URL to redirect the user to."""
    url = (
        f"https://clever.com/oauth/authorize"
        f"?response_type=code"
        f"&client_id={settings.CLEVER_CLIENT_ID}"
        f"&redirect_uri={settings.CLEVER_REDIRECT_URI}"
    )
    return {"redirect_url": url}


@router.get("/clever/callback", response_model=TokenResponse)
async def clever_callback(code: str, db: Session = Depends(get_db)):
    """Handle Clever OAuth callback, create/update user, return JWT."""
    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://clever.com/oauth/tokens",
            json={
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.CLEVER_REDIRECT_URI,
            },
            auth=(settings.CLEVER_CLIENT_ID, settings.CLEVER_CLIENT_SECRET),
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Clever token exchange failed")
        clever_token = token_resp.json().get("access_token")

        # Get user info from Clever
        me_resp = await client.get(
            "https://api.clever.com/v3.0/me",
            headers={"Authorization": f"Bearer {clever_token}"},
        )
        if me_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Clever user info")
        me_data = me_resp.json()["data"]
        clever_id = me_data["id"]
        user_type = me_data["type"]  # "teacher" or "student"

        # Get detailed info
        detail_resp = await client.get(
            f"https://api.clever.com/v3.0/{user_type}s/{clever_id}",
            headers={"Authorization": f"Bearer {clever_token}"},
        )
        detail = detail_resp.json()["data"]

    # Upsert user
    user = db.query(User).filter(User.clever_id == clever_id).first()
    role = "teacher" if user_type == "teacher" else "student"
    if not user:
        user = User(
            clever_id=clever_id,
            first_name=detail.get("name", {}).get("first", ""),
            last_name=detail.get("name", {}).get("last", ""),
            email=detail.get("email"),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.first_name = detail.get("name", {}).get("first", user.first_name)
        user.last_name = detail.get("name", {}).get("last", user.last_name)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.post("/register", response_model=TokenResponse)
def register_teacher(req: UserCreate, db: Session = Depends(get_db)):
    """Register a teacher account (fallback, non-Clever)."""
    if req.role != "teacher":
        raise HTTPException(status_code=400, detail="Only teacher registration is allowed here")
    if not req.password or not req.username:
        raise HTTPException(status_code=400, detail="Username and password required")
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")
    user = User(
        first_name=req.first_name,
        last_name=req.last_name,
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        role="teacher",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))
