"""
Shared assignment endpoints — no authentication required.

Students arriving from Google Classroom click a link containing a share_token.
They pick their name from the roster and receive a temporary JWT that lets
them complete the assignment through the normal practice endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.assignment import Assignment
from app.models.skill import Skill
from app.models.user import User
from app.models.classroom import Classroom, ClassEnrollment

router = APIRouter(prefix="/api/shared", tags=["shared"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SharedAssignmentInfo(BaseModel):
    assignment_id: str
    title: str
    skill_name: str
    skill_domain: str
    class_name: str
    students: list  # [{id, name}]


class ClaimRequest(BaseModel):
    student_id: str


class ClaimResponse(BaseModel):
    access_token: str
    student_name: str
    assignment_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/{share_token}", response_model=SharedAssignmentInfo)
def get_shared_assignment(share_token: str, db: Session = Depends(get_db)):
    """Return assignment info and student roster for a shared link.

    No authentication required — the share_token acts as the credential.
    """
    assignment = db.query(Assignment).filter(
        Assignment.share_token == share_token,
        Assignment.is_active == True,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    skill = db.query(Skill).filter(Skill.id == assignment.skill_id).first()
    classroom = db.query(Classroom).filter(Classroom.id == assignment.classroom_id).first()

    # Get enrolled students
    enrollments = (
        db.query(ClassEnrollment)
        .filter(
            ClassEnrollment.classroom_id == assignment.classroom_id,
            ClassEnrollment.is_active == True,
        )
        .all()
    )

    students = []
    for e in enrollments:
        # Respect target_student_ids if set
        if assignment.target_student_ids and str(e.student_id) not in assignment.target_student_ids:
            continue
        student = db.query(User).filter(User.id == e.student_id).first()
        if student:
            students.append({
                "id": student.id,
                "name": f"{student.first_name} {student.last_name}",
            })

    # Sort alphabetically by last name (second word)
    students.sort(key=lambda s: s["name"].split()[-1].lower())

    return SharedAssignmentInfo(
        assignment_id=assignment.id,
        title=assignment.title or (skill.name if skill else "Practice"),
        skill_name=skill.name if skill else "",
        skill_domain=skill.domain if skill else "",
        class_name=classroom.name if classroom else "",
        students=students,
    )


@router.post("/{share_token}/claim", response_model=ClaimResponse)
def claim_assignment(
    share_token: str,
    req: ClaimRequest,
    db: Session = Depends(get_db),
):
    """Student picks their name — returns a JWT so they can use the
    normal practice endpoints without a separate login.

    No authentication required.
    """
    assignment = db.query(Assignment).filter(
        Assignment.share_token == share_token,
        Assignment.is_active == True,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify student is enrolled
    enrollment = db.query(ClassEnrollment).filter(
        ClassEnrollment.classroom_id == assignment.classroom_id,
        ClassEnrollment.student_id == req.student_id,
        ClassEnrollment.is_active == True,
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="Student not enrolled in this class")

    student = db.query(User).filter(User.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Issue a JWT for this student
    token = create_access_token({"sub": str(student.id), "role": "student"})

    return ClaimResponse(
        access_token=token,
        student_name=f"{student.first_name} {student.last_name}",
        assignment_id=assignment.id,
    )
