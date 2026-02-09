import random, string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_teacher, hash_password
from app.models.user import User
from app.models.classroom import Classroom, ClassEnrollment
from app.schemas.classroom import ClassroomCreate, ClassroomOut, EnrollStudentRequest, EnrollmentOut

router = APIRouter(prefix="/api/classrooms", tags=["classrooms"])


def _generate_class_code(db: Session) -> str:
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not db.query(Classroom).filter(Classroom.class_code == code).first():
            return code


@router.post("", response_model=ClassroomOut)
def create_classroom(
    req: ClassroomCreate,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    classroom = Classroom(
        name=req.name,
        class_code=_generate_class_code(db),
        teacher_id=teacher.id,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return ClassroomOut(
        id=classroom.id,
        name=classroom.name,
        class_code=classroom.class_code,
        teacher_id=classroom.teacher_id,
        is_active=classroom.is_active,
        created_at=classroom.created_at,
        student_count=0,
    )


@router.get("", response_model=List[ClassroomOut])
def list_classrooms(
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    classrooms = (
        db.query(Classroom)
        .filter(Classroom.teacher_id == teacher.id, Classroom.is_active == True)
        .all()
    )
    result = []
    for c in classrooms:
        count = (
            db.query(ClassEnrollment)
            .filter(ClassEnrollment.classroom_id == c.id, ClassEnrollment.is_active == True)
            .count()
        )
        result.append(ClassroomOut(
            id=c.id, name=c.name, class_code=c.class_code,
            teacher_id=c.teacher_id, is_active=c.is_active,
            created_at=c.created_at, student_count=count,
        ))
    return result


@router.get("/{classroom_id}", response_model=ClassroomOut)
def get_classroom(
    classroom_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    c = db.query(Classroom).filter(
        Classroom.id == classroom_id, Classroom.teacher_id == teacher.id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Classroom not found")
    count = (
        db.query(ClassEnrollment)
        .filter(ClassEnrollment.classroom_id == c.id, ClassEnrollment.is_active == True)
        .count()
    )
    return ClassroomOut(
        id=c.id, name=c.name, class_code=c.class_code,
        teacher_id=c.teacher_id, is_active=c.is_active,
        created_at=c.created_at, student_count=count,
    )


@router.delete("/{classroom_id}")
def delete_classroom(
    classroom_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """Soft-delete a classroom (sets is_active = False)."""
    c = db.query(Classroom).filter(
        Classroom.id == classroom_id, Classroom.teacher_id == teacher.id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Classroom not found")
    c.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/{classroom_id}/students", response_model=EnrollmentOut)
def enroll_student(
    classroom_id: str,
    req: EnrollStudentRequest,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id, Classroom.teacher_id == teacher.id
    ).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    # Create student user if not exists
    username = req.username or f"{req.first_name.lower()}.{req.last_name.lower()}"
    student = db.query(User).filter(User.username == username).first()
    if not student:
        student = User(
            first_name=req.first_name,
            last_name=req.last_name,
            username=username,
            hashed_password=hash_password("student"),  # default password
            role="student",
        )
        db.add(student)
        db.commit()
        db.refresh(student)

    # Check already enrolled
    existing = db.query(ClassEnrollment).filter(
        ClassEnrollment.classroom_id == classroom_id,
        ClassEnrollment.student_id == student.id,
    ).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
        return EnrollmentOut(
            id=existing.id, student_id=student.id,
            student_name=f"{student.first_name} {student.last_name}",
            enrolled_at=existing.enrolled_at, is_active=existing.is_active,
        )

    enrollment = ClassEnrollment(
        classroom_id=classroom_id,
        student_id=student.id,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return EnrollmentOut(
        id=enrollment.id, student_id=student.id,
        student_name=f"{student.first_name} {student.last_name}",
        enrolled_at=enrollment.enrolled_at, is_active=enrollment.is_active,
    )


@router.get("/{classroom_id}/students", response_model=List[EnrollmentOut])
def list_students(
    classroom_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id, Classroom.teacher_id == teacher.id
    ).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    enrollments = (
        db.query(ClassEnrollment)
        .filter(ClassEnrollment.classroom_id == classroom_id, ClassEnrollment.is_active == True)
        .all()
    )
    result = []
    for e in enrollments:
        student = db.query(User).filter(User.id == e.student_id).first()
        if student:
            result.append(EnrollmentOut(
                id=e.id, student_id=student.id,
                student_name=f"{student.first_name} {student.last_name}",
                enrolled_at=e.enrolled_at, is_active=e.is_active,
            ))
    return result


@router.delete("/{classroom_id}/students/{student_id}")
def remove_student(
    classroom_id: str,
    student_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id, Classroom.teacher_id == teacher.id
    ).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    enrollment = db.query(ClassEnrollment).filter(
        ClassEnrollment.classroom_id == classroom_id,
        ClassEnrollment.student_id == student_id,
    ).first()
    if enrollment:
        enrollment.is_active = False
        db.commit()
    return {"ok": True}
