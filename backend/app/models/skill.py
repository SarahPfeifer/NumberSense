import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Skill(Base):
    """
    Represents a specific math skill that can be assigned and practiced.
    Domains: fractions, integers, multiplication
    """
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    domain = Column(String(50), nullable=False)        # fractions, integers, multiplication
    name = Column(String(200), nullable=False)          # e.g. "Compare fractions to 1/2"
    slug = Column(String(200), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    grade_level = Column(Integer, nullable=False)       # 4 or 5
    difficulty_min = Column(Integer, default=1)         # 1-5 scale
    difficulty_max = Column(Integer, default=5)
    problem_type = Column(String(100), nullable=False)  # comparison, equivalence, number_line, etc.
    config = Column(JSON, nullable=True)                # domain-specific generation parameters
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    assignments = relationship("Assignment", back_populates="skill")
