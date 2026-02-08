# NumberSense

**Making the fundamentals of math fast, flexible, and intuitive.**

NumberSense is a teacher-driven math fluency and number sense platform for grades 4–5, designed for real classroom use — bell ringers, centers, and intervention. Teachers assign skills; students complete short, focused practice sessions that build speed, accuracy, and intuition.

## Features

- **Three core domains**: Fractions, Combining Integers, Multiplication Fluency
- **Teacher dashboard**: Assign skills, view class progress heat maps, drill into individual students
- **Student practice**: Distraction-free 15-problem sessions (5 groups of 3) with group-based adaptation
- **Visual scaffolding**: SVG fraction bars, interactive number lines, array models — scaffolding fades as fluency grows
- **Rules-based adaptation**: Transparent logic adjusts difficulty and visual support after each group — no black-box AI
- **Cross-assignment memory**: Difficulty and visual support carry over when a student revisits the same skill
- **Clever SSO**: Login via Clever with automatic roster sync
- **Fallback login**: Class code + student name for pilots/testing
- **COPPA-friendly**: No ads, minimal PII, role-based access control
- **CI pipeline**: GitHub Actions runs unit and integration tests on every push

## Architecture

| Layer    | Technology        |
|----------|-------------------|
| Frontend | React 18, React Router 6 |
| Backend  | Python, FastAPI   |
| Database | PostgreSQL 16     |
| Auth     | JWT + Clever SSO  |
| Deploy   | Docker Compose    |
| CI       | GitHub Actions    |

## Quick Start

### Prerequisites
- Docker & Docker Compose

### Run with Docker

```bash
docker compose up --build
```

The app will be available at:
- **Frontend**: http://localhost:3001
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

## Running Tests

Tests run automatically on every push via GitHub Actions. To run them locally:

**Backend (unit + integration):**
```bash
cd backend
pip install -r requirements.txt
DATABASE_URL=sqlite:///./test.db SECRET_KEY=test python -m pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm install
npx react-scripts test --watchAll=false --verbose
```

### Test Coverage

| Suite | Tests | What it covers |
|-------|-------|----------------|
| Backend unit | 72 | Adaptation engine rules, problem generation for all 11 skill types, difficulty scaling, negative integer guarantees |
| Backend integration | 15 | Auth flow (login, register, access control), full 15-problem practice session lifecycle, adaptation at group boundaries, enrollment checks |
| Frontend | 11 | FractionBar rendering, InteractiveFractionBar click events, VisualModel dispatcher, App smoke test |

## Project Structure

```
NumberSense/
├── .github/workflows/
│   └── ci.yml              # GitHub Actions CI pipeline
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
│   ├── tests/              # pytest unit + integration tests
│   ├── alembic/            # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/     # Navbar
│   │   │   └── student/    # VisualModels (SVG fraction bars, number lines, arrays)
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
- Compare Fractions to Benchmarks (0, 1/2, 1)
- Equivalent Fractions
- Fractions on a Number Line

### Combining Integers
- Adding Integers (including minus-a-negative)
- Subtracting Integers
- Magnitude & Distance from Zero
- Integers on a Number Line

### Multiplication Fluency
- Multiplication Facts (0-12)
- Related Facts & Fact Families
- Multiplication as Scaling

## Adaptation Logic

Each 15-problem session is divided into **5 groups of 3**. After each group, the system evaluates that group's accuracy and speed, then adjusts two independent axes for the next group:

- **Difficulty level** (1-5): Controls problem complexity (operand size, denominator range, etc.)
- **Visual support level** (1-5): Controls scaffolding (5 = full static visuals, 3-2 = interactive/student-built visuals, 1 = no visuals)

| Group Result | Action |
|---|---|
| **Perfect** (3/3 correct) | Always advance: reduce visual support first, then increase difficulty |
| **Strong** (>=2/3 correct + fast, <12s avg) | Advance scaffolding |
| **Accurate but slow** (>=2/3 correct, >=12s avg) | Hold steady |
| **Struggling** (0/3 or 1/3 correct) | Retreat: increase visual support, decrease difficulty |

Starting levels carry over from the student's last completed session on the same skill, even across different assignments.

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
