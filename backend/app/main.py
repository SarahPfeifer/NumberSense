from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.routers import auth, classrooms, skills, assignments, practice, analytics, google_classroom
from app.models import google_classroom as _gc_models  # noqa: ensure tables are created

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Making the fundamentals of math fast, flexible, and intuitive.",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(classrooms.router)
app.include_router(skills.router)
app.include_router(assignments.router)
app.include_router(practice.router)
app.include_router(analytics.router)
app.include_router(google_classroom.router)


@app.on_event("startup")
def on_startup():
    """Seed skills and demo data on first run."""
    from app.services.seed_data import seed_skills, seed_demo_data
    db = SessionLocal()
    try:
        seed_skills(db)
        seed_demo_data(db)
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
