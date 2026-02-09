# NumberSense

**Making the fundamentals of math fast, flexible, and intuitive.**

NumberSense is a teacher-driven math fluency and number sense platform for grades 4–5, designed for real classroom use — bell ringers, centers, and intervention. Teachers assign skills; students complete short, focused practice sessions that build speed, accuracy, and intuition.

## Features

- **Three core domains**: Fractions, Combining Integers, Multiplication Fluency
- **Teacher dashboard**: Assign skills, view class progress heat maps, drill into individual students with six-tier fluency status (not started, needs data, needs support, developing, progressing, fluent)
- **Student practice**: Focused sessions with group-based adaptation — 15 problems (5 groups of 3) for most skills, 25 problems (5 groups of 5) for multiplication facts
- **Visual scaffolding**: SVG fraction bars (with interactive click-to-shade), interactive number lines (with place-the-start-point scaffolding), counter models (yellow/red for integer operations), array models (with distributive property highlighting), and scaling bars — all scaffolding fades as fluency grows
- **Spiral scaffolding**: When difficulty increases, visual support resets so students get scaffolding on harder content before it fades again
- **Coverage-aware multiplication**: A fact picker ensures sessions cover unseen fact families before repeating, with 70% focus on new facts and 30% review of previously mastered ones
- **Rules-based adaptation**: Transparent logic adjusts difficulty and visual support after each group — no black-box AI
- **Cross-assignment memory**: Difficulty and visual support carry over when a student revisits the same skill
- **Flexible student login**: Students can log in with full name, first name, first name + last initial, username, or "last, first" format
- **Clever SSO**: Login via Clever with automatic roster sync
- **Fallback login**: Class code + student name for pilots/testing
- **COPPA-friendly**: No ads, minimal PII, role-based access control
- **CI pipeline**: GitHub Actions runs unit and integration tests on every push

## Architecture

| Layer    | Technology              |
|----------|-------------------------|
| Frontend | React 18, React Router 6 |
| Backend  | Python, FastAPI         |
| Database | PostgreSQL 16           |
| Auth     | JWT + Clever SSO        |
| Deploy   | Docker Compose          |
| CI       | GitHub Actions          |

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

| Role    | Credentials |
|---------|-------------|
| Teacher | Username `demo.teacher`, password `teacher123` |
| Student | Class code `DEMO01`, name `Alex J` (or `Alex Johnson`, `alex`, `alex.johnson`) |

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

## Math Domains & Skills

### Fractions (Grade 4)
| Skill | Description |
|-------|-------------|
| Compare Fractions | Compare two fractions using reasoning and visual fraction bar models |
| Compare Fractions to Benchmarks (0, 1/2, 1) | Determine if a fraction is less than, equal to, or greater than benchmark values |
| Equivalent Fractions | Find equivalent fractions by identifying multiplying patterns |
| Fractions on a Number Line | Place and identify fractions on a number line between 0 and 1 |

### Combining Integers (Grade 5)
| Skill | Description |
|-------|-------------|
| Integers on a Number Line | Identify integers on a number line including negative values |
| Adding Integers | Add positive and negative integers (including minus-a-negative) using number line and counter models |
| Subtracting Integers | Subtract integers, reasoning about direction on a number line |

### Multiplication Fluency (Grade 4)
| Skill | Description |
|-------|-------------|
| Multiplication Facts (0–12) | Build fluency with basic facts; structured progression through fact families (0s-2s → 3s → 4s-5s → 6s-7s → 8s-9s → 10s-12s) with distributive property visualization |

## Visual Scaffolding Models

| Model | Used For | Scaffolding Tiers |
|-------|----------|-------------------|
| **Fraction Bar** | Fraction comparison, benchmarks, equivalence | Full bar with shading → student clicks to shade → no visual |
| **Number Line** | Fraction/integer placement, integer operations | Start point shown → student places start point (no visual cue) → no visual |
| **Counter Model** | Integer addition/subtraction (when \|a\| + \|b\| ≤ 20) | Yellow (positive) and red (negative) counters with zero pairs |
| **Array Model** | Multiplication facts | Dot array with distributive property split shown in purple/gold → no visual |

## Adaptation Logic

Sessions are divided into groups. After each group, the system evaluates accuracy and speed, then adjusts two independent axes:

- **Difficulty level** (1–5): Controls problem complexity (operand size, fact families, denominator range)
- **Visual support level** (1–5): Controls scaffolding intensity (5 = full static visuals → 3-2 = interactive/student-built → 1 = no visuals)

| Group Result | Criteria | Action |
|---|---|---|
| **Perfect** | All correct | Advance: reduce visual support first, then increase difficulty |
| **Strong** | ≥ 67% correct + fast (< 12s avg) | Advance scaffolding |
| **Accurate but slow** | ≥ 67% correct, ≥ 12s avg | Hold steady |
| **Struggling** | < 45% correct | Retreat: increase visual support, decrease difficulty |
| **Mixed** | 45–66% correct | Hold steady |

**Spiral scaffolding**: When difficulty increases, visual support resets to level 4 so students get scaffolding on harder content before it fades again. This creates the cycle: visuals on → visuals off → harder content with visuals on → ...

**Cross-assignment memory**: Starting levels carry over from the student's last completed session on the same skill, even across different assignments.

### Multiplication Fact Progression

| Difficulty | Focus Facts | Review Pool |
|------------|-------------|-------------|
| 1 | 0s, 1s, 2s | — |
| 2 | 3s | 0s, 1s, 2s |
| 3 | 4s, 5s | 0s–3s |
| 4 | 6s, 7s, 8s, 9s | 0s–5s |
| 5 | 10s, 11s, 12s | 0s–9s |

Sessions use a **coverage-aware picker**: ~70% of problems feature the focus fact family, ~30% are review. Within each category, unseen facts are prioritized so every session covers new ground.

### Teacher Dashboard Fluency Statuses

| Status | Criteria | Badge Color |
|--------|----------|-------------|
| **Not Started** | 0 completed sessions | Gray |
| **Needs Data** | < 2 completed sessions | Orange |
| **Needs Support** | Accuracy < 50% | Red |
| **Developing** | 50–84% accuracy, or < 3 sessions | Yellow |
| **Progressing** | ≥ 85% accuracy but hasn't reached max difficulty | Blue |
| **Fluent** | ≥ 85% accuracy, ≤ 20s avg, reached max difficulty | Green |

For multiplication facts, a student cannot reach "fluent" until they have practiced through 10s–12s (difficulty 5).

## Running Tests

Tests run automatically on every push via GitHub Actions. To run them locally:

**Backend (unit + integration) via Docker:**
```bash
docker compose exec backend python -m pytest tests/ -v
```

**Backend (local):**
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
| Backend — adaptation | 39 | Adaptation engine rules (3-problem and 5-problem groups), spiral scaffolding, session config, fluency status computation |
| Backend — problem generation | 51 | Problem generation for all 9 skill types, difficulty scaling, negative integer guarantees, coverage-aware multiplication picker |
| Backend — auth API | 9 | Login, registration, access control, class code login |
| Backend — practice API | 8 | Full practice session lifecycle, adaptation at group boundaries, session progress tracking |
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
│   │   │   └── analytics.py    # Teacher analytics, fluency tracking
│   │   ├── services/
│   │   │   ├── problem_generator.py  # Problem generation for all domains
│   │   │   ├── adaptation.py         # Rules-based difficulty & visual adaptation
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
│   │   │   └── student/    # VisualModels (SVG fraction bars, number lines,
│   │   │                   #   counter models, array models, scaling bars)
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
