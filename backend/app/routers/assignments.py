from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_teacher, get_current_user
from app.models.user import User
from app.models.classroom import Classroom, ClassEnrollment
from app.models.skill import Skill
from app.models.assignment import Assignment
from app.models.attempt import PracticeSession
from app.schemas.assignment import AssignmentCreate, AssignmentOut, StudentAssignmentOut

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


@router.post("", response_model=AssignmentOut)
def create_assignment(
    req: AssignmentCreate,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    classroom = db.query(Classroom).filter(
        Classroom.id == str(req.classroom_id), Classroom.teacher_id == teacher.id
    ).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    skill = db.query(Skill).filter(Skill.id == str(req.skill_id)).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Build title
    title = req.title or f"{skill.name}"

    target_ids = None
    if req.target_student_ids:
        target_ids = [str(sid) for sid in req.target_student_ids]

    assignment = Assignment(
        classroom_id=str(req.classroom_id),
        skill_id=str(req.skill_id),
        assigned_by=teacher.id,
        title=title,
        time_limit_seconds=req.time_limit_seconds,
        visual_supports=req.visual_supports,
        target_student_ids=target_ids,
        due_date=req.due_date,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    total_students = (
        db.query(ClassEnrollment)
        .filter(ClassEnrollment.classroom_id == str(req.classroom_id), ClassEnrollment.is_active == True)
        .count()
    )

    return AssignmentOut(
        id=assignment.id,
        classroom_id=assignment.classroom_id,
        skill_id=assignment.skill_id,
        skill_name=skill.name,
        skill_domain=skill.domain,
        title=assignment.title,
        time_limit_seconds=assignment.time_limit_seconds,
        visual_supports=assignment.visual_supports,
        is_active=assignment.is_active,
        created_at=assignment.created_at,
        due_date=assignment.due_date,
        completion_count=0,
        total_students=total_students,
    )


@router.get("/classroom/{classroom_id}", response_model=List[AssignmentOut])
def list_assignments(
    classroom_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id, Classroom.teacher_id == teacher.id
    ).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    assignments = (
        db.query(Assignment)
        .filter(Assignment.classroom_id == classroom_id, Assignment.is_active == True)
        .order_by(Assignment.created_at.desc())
        .all()
    )
    total_students = (
        db.query(ClassEnrollment)
        .filter(ClassEnrollment.classroom_id == classroom_id, ClassEnrollment.is_active == True)
        .count()
    )

    result = []
    for a in assignments:
        skill = db.query(Skill).filter(Skill.id == a.skill_id).first()
        completed = (
            db.query(PracticeSession.student_id)
            .filter(PracticeSession.assignment_id == a.id, PracticeSession.is_complete == True)
            .distinct()
            .count()
        )
        result.append(AssignmentOut(
            id=a.id, classroom_id=a.classroom_id, skill_id=a.skill_id,
            skill_name=skill.name if skill else "", skill_domain=skill.domain if skill else "",
            title=a.title, time_limit_seconds=a.time_limit_seconds,
            visual_supports=a.visual_supports, is_active=a.is_active,
            created_at=a.created_at, due_date=a.due_date,
            completion_count=completed, total_students=total_students,
        ))
    return result


@router.get("/my", response_model=List[StudentAssignmentOut])
def my_assignments(
    db: Session = Depends(get_db),
    student: User = Depends(get_current_user),
):
    """Get assignments for the current student."""
    if student.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")

    # Find student's classes
    enrollments = (
        db.query(ClassEnrollment)
        .filter(ClassEnrollment.student_id == student.id, ClassEnrollment.is_active == True)
        .all()
    )
    class_ids = [e.classroom_id for e in enrollments]

    assignments = (
        db.query(Assignment)
        .filter(Assignment.classroom_id.in_(class_ids), Assignment.is_active == True)
        .order_by(Assignment.created_at.desc())
        .all()
    )

    result = []
    for a in assignments:
        # Check if targeted
        if a.target_student_ids and str(student.id) not in a.target_student_ids:
            continue
        skill = db.query(Skill).filter(Skill.id == a.skill_id).first()
        if not skill:
            continue
        # Check completion
        completed_session = (
            db.query(PracticeSession)
            .filter(
                PracticeSession.assignment_id == a.id,
                PracticeSession.student_id == student.id,
                PracticeSession.is_complete == True,
            )
            .first()
        )
        result.append(StudentAssignmentOut(
            id=a.id,
            skill_name=skill.name,
            skill_domain=skill.domain,
            skill_slug=skill.slug,
            problem_type=skill.problem_type,
            visual_supports=a.visual_supports,
            time_limit_seconds=a.time_limit_seconds,
            is_completed=completed_session is not None,
        ))
    return result


@router.delete("/{assignment_id}")
def deactivate_assignment(
    assignment_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    classroom = db.query(Classroom).filter(
        Classroom.id == assignment.classroom_id, Classroom.teacher_id == teacher.id
    ).first()
    if not classroom:
        raise HTTPException(status_code=403, detail="Not your classroom")
    assignment.is_active = False
    db.commit()
    return {"ok": True}
