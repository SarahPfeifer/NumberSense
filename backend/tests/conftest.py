"""
Shared test fixtures.

Unit tests use no database.
Integration tests use an in-memory SQLite database with the full FastAPI
app wired to it, plus helper fixtures for creating users and tokens.
"""
import os, pytest

# Force SQLite BEFORE any app imports touch settings / engine
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["CORS_ORIGINS"] = "http://localhost"

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.main import app

# ── SQLite test engine ────────────────────────────────────
TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def _sqlite_fk(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Create all tables once for the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clean up test db file
    import pathlib
    pathlib.Path("test.db").unlink(missing_ok=True)


@pytest.fixture()
def db():
    """Provide a clean database session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestSession(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """FastAPI TestClient wired to the test database session."""
    def _override():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def teacher(db):
    """Create and return a teacher user."""
    from app.models.user import User
    user = User(
        first_name="Test",
        last_name="Teacher",
        username="test.teacher",
        email="teacher@test.com",
        hashed_password=hash_password("password"),
        role="teacher",
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture()
def student(db):
    """Create and return a student user."""
    from app.models.user import User
    user = User(
        first_name="Test",
        last_name="Student",
        username="test.student",
        hashed_password=hash_password("password"),
        role="student",
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture()
def teacher_token(teacher):
    return create_access_token({"sub": str(teacher.id), "role": "teacher"})


@pytest.fixture()
def student_token(student):
    return create_access_token({"sub": str(student.id), "role": "student"})


@pytest.fixture()
def auth_teacher(teacher_token):
    """Return Authorization header dict for teacher."""
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture()
def auth_student(student_token):
    """Return Authorization header dict for student."""
    return {"Authorization": f"Bearer {student_token}"}
