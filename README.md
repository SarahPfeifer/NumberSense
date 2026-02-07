# NumberSense

**Making the fundamentals of math fast, flexible, and intuitive.**

NumberSense is a teacher-driven math fluency and number sense platform for grades 4–5, designed for real classroom use — bell ringers, centers, and intervention. Teachers assign skills; students complete short, focused practice sessions that build speed, accuracy, and intuition.

## Features

- **Three core domains**: Fractions, Combining Integers, Multiplication Fluency
- **Teacher dashboard**: Assign skills, view class progress heat maps, drill into individual students
- **Student practice**: Distraction-free sessions with warm-up → core → checkpoint flow
- **Visual scaffolding**: Fraction bars, number lines, array models that fade as fluency grows
- **Rules-based adaptation**: Transparent logic adjusts difficulty and visual support — no black-box AI
- **Clever SSO**: Login via Clever with automatic roster sync
- **Fallback login**: Class code + student name for pilots/testing
- **COPPA-friendly**: No ads, minimal PII, role-based access control

## Architecture

| Layer    | Technology        |
|----------|-------------------|
| Frontend | React 18, React Router 6 |
| Backend  | Python, FastAPI   |
| Database | PostgreSQL 16     |
| Auth     | JWT + Clever SSO  |
| Deploy   | Docker Compose    |

## Quick Start

### Prerequisites
- Docker & Docker Compose

### Run with Docker

```bash
docker compose up --build
```

The app will be available at:
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API docs**: http://localhost:8000/docs

### Demo Credentials

| Role    | Username        | Password    |
|---------|-----------------|-------------|
| Teacher | `demo.teacher`  | `teacher123`|
| Student | Class code `DEMO01`, name `Alex J` |

### Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit DATABASE_URL if needed
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

## Project Structure

```
NumberSense/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, database, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── routers/        # API endpoints
│   │   │   ├── auth.py         # Login, register, Clever SSO
│   │   │   ├── classrooms.py   # Class CRUD, enrollment
│   │   │   ├── skills.py       # Skill catalog
│   │   │   ├── assignments.py  # Assignment management
│   │   │   ├── practice.py     # Practice sessions, problem delivery
│   │   │   └── analytics.py    # Teacher analytics, progress tracking
│   │   ├── services/
│   │   │   ├── problem_generator.py  # Problem generation for all domains
│   │   │   ├── adaptation.py         # Rules-based difficulty adaptation
│   │   │   └── seed_data.py          # Skill definitions + demo data
│   │   └── main.py
│   ├── alembic/            # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/     # Navbar
│   │   │   └── student/    # VisualModels (fraction bars, number lines, arrays)
│   │   ├── contexts/       # AuthContext
│   │   ├── pages/          # All page components
│   │   ├── services/       # API client
│   │   └── styles/         # Global CSS
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Math Domains & Skills

### Fractions
- Compare Fractions (visual + numeric)
- Compare Fractions to Benchmarks (0, ½, 1)
- Equivalent Fractions
- Fractions on a Number Line

### Combining Integers
- Adding Integers
- Subtracting Integers
- Magnitude & Distance from Zero
- Integers on a Number Line

### Multiplication Fluency
- Multiplication Facts (0–12)
- Related Facts & Fact Families
- Multiplication as Scaling

## Adaptation Logic

The system uses transparent, rules-based adaptation:

| Student Performance | Action |
|---|---|
| **Fast + Accurate** (≥85%, <5s avg) | Reduce visual supports, then increase difficulty |
| **Accurate + Slow** (≥85%, >5s avg) | Maintain difficulty, encourage efficiency |
| **Inaccurate** (<60%) | Lower difficulty, increase visual scaffolding |
| **Developing** (60-85%) | Small adjustments based on speed |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Teacher/student login |
| POST | `/api/auth/class-code-login` | Student class code login |
| POST | `/api/auth/register` | Teacher registration |
| GET | `/api/auth/me` | Current user |
| GET | `/api/auth/clever/redirect` | Clever SSO redirect URL |
| GET | `/api/auth/clever/callback` | Clever OAuth callback |
| GET/POST | `/api/classrooms` | List/create classrooms |
| GET/POST | `/api/classrooms/:id/students` | List/enroll students |
| GET | `/api/skills` | List all skills |
| GET | `/api/skills/domains` | Skills grouped by domain |
| POST | `/api/assignments` | Create assignment |
| GET | `/api/assignments/classroom/:id` | List class assignments |
| GET | `/api/assignments/my` | Student's assignments |
| POST | `/api/practice/start` | Start practice session |
| GET | `/api/practice/problem/:id` | Get next problem |
| POST | `/api/practice/answer` | Submit answer, get feedback |
| GET | `/api/practice/session/:id/summary` | Session results |
| GET | `/api/analytics/classroom/:id/overview` | Class progress heat map |
| GET | `/api/analytics/student/:id/progress` | Student drill-down |

## License

Private — all rights reserved.
