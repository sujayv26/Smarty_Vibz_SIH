# Smarty Vibz / CONSight — Schedule Intelligence Platform

**Phases 1–12 Implemented** (see `STATE.json` and `docs/STABILIZATION_REPORT_P0-P12.md` for verified status)

## Overview

CONSight is a schedule intelligence platform that connects field progress reports (voice, text, Excel, WhatsApp, scanned diaries) with Primavera P6 / MS Project schedules through a complete matching, confidence, and planner-review workflow. It extends through ML-based delay prediction, institutional-memory analytics, delay-ripple analysis, multilingual extraction, voice, and OCR.

**Source of truth for implemented features:** `STATE.json` and `docs/STABILIZATION_REPORT_P0-P12.md` — check these before assuming a feature exists.

## Quick Links

- **Setup & Operations:** `SETUP.md` (cross-platform, step-by-step)
- **Verified Status Report:** `docs/STABILIZATION_REPORT_P0-P12.md`
- **Feature Tracker:** `STATE.json`
- **API Docs (local):** `http://localhost:8000/docs` (when running)

## Phases Implemented (P0–P12)

| Phase | Name | Key Deliverables |
|-------|------|------------------|
| **P0** | Infra & Foundations | Postgres+pgvector, Redis, Celery, JWT/RBAC (5 roles), Alembic, SQLite backup, synthetic data, design system, frontend shell, landing page |
| **P1** | Schedule & Progress Core | Excel schedule upload, free-text/Excel progress extraction, Time-Agent chat |
| **P2** | Matching Engine | Exact, fuzzy, semantic, context, temporal matchers; benchmark suite |
| **P3** | Confidence & Review | Confidence scoring (HIGH/MEDIUM/LOW), planner review queue (approve/correct/reject/new), audit trail |
| **P4** | P6/XER Round-Trip | XER import/export, predecessor-successor (FS/SS/FF/SF+lag), MPP via mpxj, actuals write-back on approval |
| **P5** | WhatsApp Ingestion | Business Cloud API webhook, same extraction→matching pipeline, live Inbound Channels panel |
| **P6** | Multilingual Extraction | Hi/En, Ta/En, Te/En, Kn/En code-mixed; 38 benchmarks @ 85% |
| **P7** | Delay Ripple | CPM-based graph traversal over P4 predecessor/successor; critical-path exposure; DelayImpact records |
| **P8** | Institutional Memory | Discipline summary, delay patterns, productivity benchmarks, variance trends; Insights dashboard (recharts) |
| **P9** | ML Delay Prediction | RandomForest (32 features), daily retrain, 6-hr predictions; RiskWatchlist with confidence bars |
| **P10** | Voice Agent | Whisper STT (5 langs), waveform viz, Time-Agent integration; press-to-talk UI |
| **P11** | OCR Scanned Diaries | Tesseract (PDF/PNG/JPG/TIFF/BMP/WebP, 5 langs); confidence routing to review |

**P13+ (Advanced RAG, Weather, BIM, Multi-project, PWA, Observability, E2E) — NOT IMPLEMENTED**

## Architecture

```
backend/                          # FastAPI (Python 3.11+ in Docker, 3.9 local)
├── app/
│   ├── api/v1/                   # Versioned routers (auth, schedule, progress, agent, matching, confidence, reviews, xer, webhooks, delay_impact, analytics, delay_prediction, voice, ocr)
│   ├── core/                     # config, security, auth, celery_app
│   ├── matching/                 # engine, matchers (exact/fuzzy/semantic/context/temporal), benchmark
│   ├── models/                   # SQLAlchemy models (all PRD §9 tables + P4–P12 extensions)
│   ├── schemas/                  # Pydantic v2 request/response models
│   ├── services/                 # Business logic (schedule, progress, confidence, delay_ripple, analytics, ML, voice, OCR, XER, WhatsApp, backup)
│   ├── workers/                  # Celery tasks (backup, ML retrain, delay-ripple recompute)
│   ├── database.py               # SQLAlchemy async/sync engines, Alembic
│   └── main.py                   # FastAPI entrypoint
├── alembic/                      # Migrations (P0 schema + P4–P12 additions)
├── tests/                        # 196 backend tests (all passing)
└── scripts/
    ├── generate_synthetic_data.py    # Full P0–P12 dataset
    └── seed_demo_project.py

frontend/                         # React + Vite + TypeScript
├── src/
│   ├── app/                      # Routed screens (Dashboard, Schedule, Planner Queue, Time Agent, Inbound, Insights, Risk, BIM, Admin, Settings)
│   ├── components/               # Design-system primitives (Button, Badge, Card, Input, Select, DataTable, Skeleton, EmptyState)
│   ├── features/                 # Feature-specific components
│   ├── hooks/                    # Custom React hooks
│   └── lib/                      # API client, auth context
└── package.json

infrastructure/
└── docker-compose.yml            # postgres:pgvector, redis, api, celery-worker, celery-beat
```

## Requirements

- **Docker Desktop** (or Podman) + Docker Compose v2
- **Python 3.11+** (for local dev without Docker; Docker image uses 3.11-slim)
- **Node.js 20+** (for frontend)
- **Git**

## Quick Start (Docker - Recommended)

```bash
# 1. Clone & configure
git clone <repo-url>
cd Smarty_Vibz_SIH
cp backend/.env.example backend/.env   # NEVER commit the filled .env

# 2. Launch full stack (Postgres+pgvector, Redis, API, Celery worker, Celery beat)
docker compose -f infrastructure/docker-compose.yml up -d --build

# 3. Run migrations & seed synthetic data
docker compose -f infrastructure/docker-compose.yml exec api python -m alembic upgrade head
docker compose -f infrastructure/docker-compose.yml exec api python scripts/generate_synthetic_data.py --project DEMO-001 --org demo --weeks 4 --seed 42

# 4. Verify
curl http://localhost:8000/health
open http://localhost:5173   # Frontend dev server (if running separately) or use Docker Compose override
```

**Demo credentials** (from synthetic data): `supervisor@demo.com` / `supervisor123` (role: SITE_SUPERVISOR)

## Local Development (Without Docker)

### Prerequisites
- Python 3.9+ (3.11+ recommended; Docker uses 3.11)
- Node.js 20+
- Postgres 16 + pgvector extension
- Redis 7+

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Edit with your Postgres/Redis credentials
python -m alembic upgrade head
python scripts/generate_synthetic_data.py --project DEMO-001 --org demo --weeks 4 --seed 42
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
# For production build: npm run build && npm run preview
```

### Celery (separate terminals)
```bash
# Terminal 1: Worker
cd backend && .venv/bin/celery -A app.core.celery_app worker --loglevel=info

# Terminal 2: Beat (scheduler)
cd backend && .venv/bin/celery -A app.core.celery_app beat --loglevel=info
```

## Running Tests

```bash
# Backend (196 tests)
cd backend
python -m pytest tests/ -v

# Frontend
cd frontend
npm run build
npm run lint
```

## Three-Case Core Demo (Verified Live)

1. **Clean Auto-Match** → confidence ≥ 0.85 → `AUTO_MATCH` (no human review)
   - Upload schedule with `PIP-1023`
   - Submit: `"Today at 9:30 AM, the piping team started erection of the PIP-1023 line 24-XX-101 spool in Area B"`
   - Result: `AUTO_MATCH`, confidence 0.8975, AuditRecord(action=AUTO_MATCH, actor=SYSTEM)

2. **Ambiguous Match + Planner Correction** → `REVIEW_REQUIRED` → planner corrects
   - Submit: `"Work on XX-101 piping"`
   - Two 0.7 candidates → planner `POST /reviews/{id}/correct` with `activity_id=2`
   - Result: Review status `CORRECTED`, activity `PIP-1027`

3. **Unmatched → New Activity** → `REVIEW_REQUIRED` → planner creates new
   - Submit: `"Office furniture delivery received at warehouse"`
   - 0 matches → planner `POST /reviews/{id}/create-new` with new activity
   - Result: `NEW_ACTIVITY_CREATED`, new activity in schedule (`is_unplanned=true`)

## Key API Endpoints (v1)

| Domain | Endpoints |
|--------|-----------|
| Auth | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`, `POST /auth/csrf-token` |
| Schedule | `POST /schedule/upload` (Excel), `POST /schedule/import/p6` (XER/MPP), `POST /schedule/export/p6/{id}`, `GET /schedule/activities` |
| Progress | `POST /progress/extract`, `POST /progress/upload-excel`, `GET /progress/events`, `GET /progress/inbound/recent` |
| Agent | `POST /agent/chat`, `GET /agent/sessions/{id}/events` |
| Matching | `POST /matching/run/{event_id}`, `POST /matching/benchmark` |
| Confidence | `POST /confidence/evaluate/{event_id}` |
| Reviews | `GET /reviews/pending`, `GET /reviews/{id}`, `POST /reviews/{id}/approve`, `POST /reviews/{id}/correct`, `POST /reviews/{id}/reject`, `POST /reviews/{id}/create-new` |
| Delay Impact | `GET /delay-impacts/event/{id}`, `GET /delay-impacts/activity/{id}`, `GET /delay-impacts/project/{id}/critical` |
| Analytics | `GET /analytics/discipline-summary`, `GET /analytics/delay-patterns`, `GET /analytics/benchmarks`, `GET /analytics/variance-trend`, `GET /analytics/matching-quality`, `GET /analytics/confidence-distribution` |
| Delay Prediction | `GET /delay-predictions/project/{id}`, `GET /delay-predictions/project/{id}/watchlist`, `POST /delay-predictions/train` |
| Voice | `POST /voice/transcribe`, `POST /voice/process`, `GET /voice/model-info` |
| OCR | `POST /ocr/upload`, `POST /ocr/process`, `GET /ocr/model-info` |
| WhatsApp | `GET /webhooks/whatsapp/inbound` (verify), `POST /webhooks/whatsapp/inbound` (ingest) |

## Environment Variables (backend/.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | `postgresql+psycopg://user:pass@host:5432/db` (or `sqlite:///./local.db` for dev) |
| `REDIS_URL` | Yes | `redis://host:6379/0` |
| `JWT_SECRET_KEY` | Yes | Strong random string (≥32 chars) |
| `JWT_ALGORITHM` | No | `HS256` (default) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` (default) |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` (default) |
| `CORS_ORIGINS` | No | `http://localhost:3000,http://localhost:5173` |
| `LLM_PROVIDER` | No | `mock` (default; set to `openai`/`anthropic` for real LLM) |
| `LLM_API_KEY` | If LLM_PROVIDER≠mock | Provider API key |
| `WHATSAPP_*` | If WhatsApp enabled | Cloud API credentials |
| `TESSERACT_CMD` | If OCR enabled | Path to tesseract binary |

**⚠️ Never commit a filled `.env`** — `.gitignore` covers `.env`, `.env.*`, secrets, backups, build artifacts.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `alembic upgrade head` fails | Postgres not ready / wrong URL | Check `DATABASE_URL`, ensure pgvector extension exists |
| `pytest` fails with `IntegrityError: organization_id` | Test DB not overridden | Ensure `conftest.py` overrides `get_db` |
| `uvicorn` import errors | Missing deps / wrong venv | Re-create venv, `pip install -r requirements.txt` |
| Frontend `npm run build` fails | Node version mismatch | Use Node 20+ (`nvm use 20`) |
| Celery tasks not running | Redis not reachable | Check `REDIS_URL`, ensure Redis running |
| `gitleaks` finds secrets | Secret in history | Rotate secret, rewrite history or accept risk |
| `python-multipart` SpooledTemporaryFile error | Python 3.9 file upload | Fixed in code (read file content first) |

## OS-Specific Notes

| OS | Notes |
|----|-------|
| **macOS** | Docker Desktop works natively. Use `brew install postgresql@16 redis node@20 python@3.11` for local services. |
| **Linux** | Native Docker/Podman works. Install `postgresql-16`, `postgresql-16-pgvector`, `redis`, `nodejs`, `python3.11` via package manager. |
| **Windows** | **Use WSL2** (Docker Desktop backend). Native Windows Postgres pgvector support is limited; WSL2 provides full Linux compatibility. Run all commands inside WSL2 Ubuntu. |

## License

SIH26122 Project — Smarty Vibz Team

See `STATE.json` and `docs/STABILIZATION_REPORT_P0-P12.md` for verified implementation status.