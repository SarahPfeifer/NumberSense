"""
Teacher analytics endpoints — progress tracking and fluency indicators.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import require_teacher
from app.models.user import User
from app.models.classroom import Classroom, ClassEnrollment
from app.models.assignment import Assignment
from app.models.skill import Skill
from app.models.attempt import PracticeSession, StudentAttempt
from app.services.adaptation import compute_fluency_status, compute_visual_trend

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/classroom/{classroom_id}/overview")
def classroom_overview(
    classroom_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """High-level classroom stats: per-skill accuracy heat map."""
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id, Classroom.teacher_id == teacher.id
    ).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    assignments = db.query(Assignment).filter(
        Assignment.classroom_id == classroom_id, Assignment.is_active == True
    ).all()

    enrollments = db.query(ClassEnrollment).filter(
        ClassEnrollment.classroom_id == classroom_id, ClassEnrollment.is_active == True
    ).all()
    student_ids = [e.student_id for e in enrollments]
    students = {s.id: s for s in db.query(User).filter(User.id.in_(student_ids)).all()} if student_ids else {}

    skill_stats = []
    for a in assignments:
        skill = db.query(Skill).filter(Skill.id == a.skill_id).first()
        if not skill:
            continue

        sessions = db.query(PracticeSession).filter(
            PracticeSession.assignment_id == a.id,
            PracticeSession.is_complete == True,
        ).all()

        per_student = []
        for sid in student_ids:
            s_sessions = [s for s in sessions if s.student_id == sid]
            if not s_sessions:
                per_student.append({
                    "student_id": str(sid),
                    "student_name": f"{students[sid].first_name} {students[sid].last_name}" if sid in students else "Unknown",
                    "accuracy": None,
                    "avg_time_ms": None,
                    "fluency_status": "red",
                    "sessions_completed": 0,
                })
                continue
            total_correct = sum(s.correct_count for s in s_sessions)
            total_problems = sum(s.total_problems for s in s_sessions)
            acc = total_correct / total_problems if total_problems else 0
            times = [s.avg_response_time_ms for s in s_sessions if s.avg_response_time_ms]
            avg_t = sum(times) / len(times) if times else 0
            per_student.append({
                "student_id": str(sid),
                "student_name": f"{students[sid].first_name} {students[sid].last_name}" if sid in students else "Unknown",
                "accuracy": round(acc * 100, 1),
                "avg_time_ms": round(avg_t, 0),
                "fluency_status": compute_fluency_status(acc, avg_t),
                "sessions_completed": len(s_sessions),
            })

        total_acc = 0
        total_count = 0
        for ps in per_student:
            if ps["accuracy"] is not None:
                total_acc += ps["accuracy"]
                total_count += 1
        class_acc = total_acc / total_count if total_count else 0

        skill_stats.append({
            "assignment_id": str(a.id),
            "skill_id": str(skill.id),
            "skill_name": skill.name,
            "skill_domain": skill.domain,
            "class_accuracy": round(class_acc, 1),
            "completion_rate": f"{sum(1 for p in per_student if p['sessions_completed'] > 0)}/{len(student_ids)}",
            "students": per_student,
        })

    return {
        "classroom_id": str(classroom_id),
        "classroom_name": classroom.name,
        "total_students": len(student_ids),
        "skills": skill_stats,
    }


@router.get("/student/{student_id}/progress")
def student_progress(
    student_id: str,
    classroom_id: str,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """Detailed drill-down for a single student in a classroom."""
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id, Classroom.teacher_id == teacher.id
    ).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    assignments = db.query(Assignment).filter(
        Assignment.classroom_id == classroom_id, Assignment.is_active == True
    ).all()

    skill_progress = []
    for a in assignments:
        skill = db.query(Skill).filter(Skill.id == a.skill_id).first()
        if not skill:
            continue

        sessions = (
            db.query(PracticeSession)
            .filter(
                PracticeSession.assignment_id == a.id,
                PracticeSession.student_id == student_id,
                PracticeSession.is_complete == True,
            )
            .order_by(PracticeSession.completed_at)
            .all()
        )

        if not sessions:
            skill_progress.append({
                "skill_name": skill.name,
                "skill_domain": skill.domain,
                "sessions_completed": 0,
                "overall_accuracy": 0,
                "avg_response_time_ms": 0,
                "fluency_status": "red",
                "visual_support_trend": "stable",
                "growth": [],
            })
            continue

        total_correct = sum(s.correct_count for s in sessions)
        total_problems = sum(s.total_problems for s in sessions)
        acc = total_correct / total_problems if total_problems else 0
        times = [s.avg_response_time_ms for s in sessions if s.avg_response_time_ms]
        avg_t = sum(times) / len(times) if times else 0
        visual_levels = [s.visual_support_level for s in sessions]

        growth = []
        for s in sessions:
            s_acc = s.correct_count / s.total_problems if s.total_problems else 0
            growth.append({
                "session_date": s.completed_at.isoformat() if s.completed_at else s.started_at.isoformat(),
                "accuracy": round(s_acc * 100, 1),
                "avg_time_ms": round(s.avg_response_time_ms or 0, 0),
                "difficulty": s.difficulty_level,
                "visual_level": s.visual_support_level,
            })

        skill_progress.append({
            "skill_name": skill.name,
            "skill_domain": skill.domain,
            "sessions_completed": len(sessions),
            "overall_accuracy": round(acc * 100, 1),
            "avg_response_time_ms": round(avg_t, 0),
            "fluency_status": compute_fluency_status(acc, avg_t),
            "visual_support_trend": compute_visual_trend(visual_levels),
            "growth": growth,
        })

    return {
        "student_id": str(student_id),
        "student_name": f"{student.first_name} {student.last_name}",
        "classroom_name": classroom.name,
        "skills": skill_progress,
    }
