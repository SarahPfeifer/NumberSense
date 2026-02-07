from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.skill import Skill
from app.schemas.skill import SkillOut

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("", response_model=List[SkillOut])
def list_skills(
    domain: Optional[str] = None,
    grade_level: Optional[int] = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = db.query(Skill)
    if domain:
        q = q.filter(Skill.domain == domain)
    if grade_level:
        q = q.filter(Skill.grade_level == grade_level)
    return q.order_by(Skill.domain, Skill.display_order).all()


@router.get("/domains")
def list_domains(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Return available domains with skill counts."""
    skills = db.query(Skill).all()
    domains = {}
    for s in skills:
        if s.domain not in domains:
            domains[s.domain] = {"domain": s.domain, "skill_count": 0, "skills": []}
        domains[s.domain]["skill_count"] += 1
        domains[s.domain]["skills"].append({"id": str(s.id), "name": s.name, "slug": s.slug})
    return list(domains.values())
