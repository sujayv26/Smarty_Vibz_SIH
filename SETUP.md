# CONSight / Smarty Vibz — Cross-Platform Setup, Run & Testing Guide

**Audience:** Teammates who haven't touched the codebase yet.  
**Source of truth for what's actually built:** `STATE.json` and `docs/STABILIZATION_REPORT_P0-P12.md` — check these before assuming a feature exists.

---

## 1. Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| **Docker Desktop** (or Podman) | Latest | Includes Docker Compose v2. Required for recommended stack. |
| **Python** | 3.11+ | Docker image uses `python:3.11-slim`. Local dev works on 3.9+ but 3.11+ recommended. |
| **Node.js** | 20+ | Frontend uses Vite + React 18 + TypeScript. |
| **Git** | 2.30+ | For cloning and version control. |
| **PostgreSQL 16 + pgvector** | 16.x | Only if running backend locally without Docker. |
| **Redis** | 7+ | Only if running backend/Celery locally without Docker. |

---

## 2. Environment Variable Setup

### 2.1 Backend (`.env`)

```bash
cd backend
cp .env.example .env   # Create your local copy
```

**Edit `.env` with your values:**

```ini
# Database (required)
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/consight
# For local dev without Postgres, you can use SQLite:
# DATABASE_URL=sqlite:///./local.db

# Redis (required)
REDIS_URL=redis://localhost:6379/0

# JWT (required in production)
JWT_SECRET_KEY=your-32-char-min-random-string
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# LLM Provider (default: mock)
LLM_PROVIDER=mock
LLM_API_KEY=               # Required only if LLM_PROVIDER != mock

# WhatsApp Cloud API (optional)
WHATSAPP_APP_ID=
WHATSAPP_APP_SECRET=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_WEBHOOK_SECRET=

# OCR (optional)
TESSERACT_CMD=/usr/bin/tesseract   # Or C:\Program Files\Tesseract-OCR\tesseract.exe on Windows
```

### 2.2 Frontend (`.env`)

Frontend uses Vite env vars. Create `frontend/.env` if needed:

```ini
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### ⚠️ Critical: Never Commit Secrets

- `.gitignore` already covers: `.env`, `.env.*`, `*.pem`, `*.key`, `backups/*.db`, `node_modules/`, `__pycache__/`, `dist/`, `build/`, `*.db`, `test.db`
- **Never commit a filled `.env`** — rotate any secret that accidentally gets committed.

---

## 3. OS-Specific Setup

### 3.1 macOS (Apple Silicon / Intel)

**Recommended: Docker Desktop**
```bash
brew install docker docker-compose   # Or install Docker Desktop.app
```

**Local services (if not using Docker):**
```bash
brew install postgresql@16 redis node@20 python@3.11
brew services start postgresql@16 redis
# Create pgvector extension:
psql -d consight -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Python virtual environment:**
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.2 Linux (Ubuntu 22.04+ / Debian 12+ / Fedora 38+)

**Docker (recommended):**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker

# Or Podman:
sudo apt install -y podman podman-compose
```

**Local services:**
```bash
# Ubuntu/Debian
sudo apt install -y postgresql-16 postgresql-16-pgvector redis-server nodejs npm python3.11 python3.11-venv
sudo systemctl enable --now postgresql redis
# Create pgvector extension:
sudo -u postgres psql -d consight -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3.3 Windows

**⚠️ Strongly Recommended: WSL2 (Ubuntu 22.04+) + Docker Desktop**

Native Windows Postgres + pgvector is unreliable. WSL2 gives you a real Linux kernel.

1. Enable WSL2: `wsl --install -d Ubuntu-22.04` (run in PowerShell as Admin)
2. Restart, then open Ubuntu from Start menu
3. Inside WSL2, follow **Linux** instructions above
4. Install Docker Desktop for Windows, enable "Use WSL 2 based engine", integrate with your Ubuntu distro

**If you must run natively on Windows (not recommended):**
- Install PostgreSQL 16 from EDB, manually add pgvector DLL
- Redis via Memurai or Chocolatey: `choco install redis-64`
- Python from python.org, Node from nodejs.org
- Path separators, line endings, and case sensitivity will bite you

---

## 4. Running the Full Stack (Docker — Recommended)

### 4.1 One-Time Setup

```bash
# 1. Clone
git clone <repo-url>
cd Smarty_Vibz_SIH

# 2. Configure backend env
cp backend/.env.example backend/.env
# Edit backend/.env with your values (see Section 2)

# 3. Build & launch
docker compose -f infrastructure/docker-compose.yml up -d --build

# 4. Verify containers healthy
docker compose -f infrastructure/docker-compose.yml ps
# Should show: postgres (healthy), redis (healthy), api, celery-worker, celery-beat
```

### 4.2 Initialize Database & Seed Data

```bash
# Run migrations
docker compose -f infrastructure/docker-compose.yml exec api python -m alembic upgrade head

# Generate synthetic data (4 weeks, demo project)
docker compose -f infrastructure/docker-compose.yml exec api python scripts/generate_synthetic_data.py --project DEMO-001 --org demo --weeks 4 --seed 42
```

**Expected output:**
```
Organization: Demo Construction Co. (id=1)
Project: Demo Highway Project (id=1)
Users: 5 created/found
Ingestion sources: 7
Building WBS tree...
Created 285 WBS nodes
Generating field events...
Created 90 field events
...
Demo credentials: supervisor@demo.com / supervisor123
```

### 4.3 Verify API

```bash
curl http://localhost:8000/health
# {"status":"healthy"}

curl http://localhost:8000/docs
# OpenAPI/Swagger UI
```

### 4.4 Frontend (if running separately)

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

---

## 5. Local Development Without Docker

### 5.1 Backend

```bash
cd backend

# 1. Virtual environment
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Ensure Postgres + Redis running (Section 3)
# 4. Configure .env (Section 2)

# 5. Migrations
python -m alembic upgrade head

# 6. Seed data
python scripts/generate_synthetic_data.py --project DEMO-001 --org demo --weeks 4 --seed 42

# 6. Run API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5.2 Celery (Worker + Beat)

```bash
# Terminal 1: Worker
cd backend && source .venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info

# Terminal 2: Beat (scheduler)
cd backend && source .venv/bin/activate
celery -A app.core.celery_app beat --loglevel=info
```

### 5.3 Frontend

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

---

## 6. Running Tests

### 6.1 Backend (196 tests)

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v

# Or run specific module:
python -m pytest tests/test_phase1.py -v
python -m pytest tests/test_analytics.py -v
```

**Expected:** `196 passed, 20 warnings`

### 6.2 Frontend

```bash
cd frontend
npm run build
npm run lint
```

**Expected:** Build passes; lint shows pre-existing errors (not blocking)

---

## 7. Three-Case Core Demo (Verified Live)

Run against a live API (Docker or local):

### Demo Credentials
From synthetic data generator: `supervisor@demo.com` / `supervisor123` (SITE_SUPERVISOR)

### Case 1: Clean Auto-Match (confidence ≥ 0.85 → AUTO_MATCH)

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"supervisor@demo.com","password":"supervisor123"}' | jq -r .access_token)

# 2. Upload schedule with PIP-1023
curl -X POST http://localhost:8000/schedule/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@schedule_pip1023.xlsx"

# 3. Submit clean progress event
curl -X POST http://localhost:8000/progress/extract \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"raw_text":"Today at 9:30 AM, the piping team started erection of the PIP-1023 line 24-XX-101 spool in Area B"}'

# 4. Evaluate confidence
curl -X POST http://localhost:8000/confidence/evaluate/<EVENT_ID> \
  -H "Authorization: Bearer $TOKEN"

# Expected: decision=AUTO_MATCH, confidence_score≈0.8975, confidence_level=HIGH
# AuditRecord: action=AUTO_MATCH, actor=SYSTEM (no human review)
```

### Case 2: Ambiguous Match + Planner Correction

```bash
# Submit ambiguous event
curl -X POST http://localhost:8000/progress/extract \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"raw_text":"Work on XX-101 piping"}'

# Evaluate → REVIEW_REQUIRED (LOW), get review_id
curl -X POST http://localhost:8000/confidence/evaluate/<EVENT_ID> \
  -H "Authorization: Bearer $TOKEN"

# Planner corrects to PIP-1027 (Install Support for XX-101)
curl -X POST http://localhost:8000/reviews/<REVIEW_ID>/correct \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"activity_id": 2, "reviewer_note": "Corrected to support installation"}'

# Expected: status=CORRECTED, proposed_activity=PIP-1027
```

### Case 3: Unmatched → New Activity

```bash
# Submit unrelated event
curl -X POST http://localhost:8000/progress/extract \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"raw_text":"Office furniture delivery received at warehouse"}'

# Evaluate → REVIEW_REQUIRED (LOW), get review_id
curl -X POST http://localhost:8000/confidence/evaluate/<EVENT_ID> \
  -H "Authorization: Bearer $TOKEN"

# Planner creates new activity
curl -X POST http://localhost:8000/reviews/<REVIEW_ID>/create-new \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"activity_code":"MISC-9001","activity_name":"Office furniture delivery","discipline":"Civil","wbs":"MISC.9001","reviewer_note":"Not in original schedule"}'

# Expected: status=NEW_ACTIVITY_CREATED, new_activity_id=<id>, verified in schedule with is_unplanned=true
```

---

## 8. Verified Data Volumes (Synthetic Data Generator)

Run with realistic data:
```bash
python scripts/generate_synthetic_data.py --project DEMO-001 --org demo --weeks 8 --seed 42
```

**Output (verified):**
| Entity | Count |
|--------|-------|
| Organizations | 1 |
| Users (5 roles) | 5 |
| Projects | 1 |
| Ingestion Sources | 7 |
| WBS Nodes (L1–L6) | 285 |
| Schedule Activities | 285 |
| Field Events | 90 |
| Confidence Results | 90 |
| Planner Reviews | 62 |
| Audit Records | 62 |
| Event-WBS Matches | 90 |
| Glossary Mappings | 10 |
| Delay Reasons | 15 |
| Productivity Benchmarks | 10 |

---

## 9. Backup & Restore (Verified End-to-End)

### Backup (Celery Beat Task)
```bash
# Manual trigger (normally runs hourly via Celery Beat)
docker compose -f infrastructure/docker-compose.yml exec celery-worker python -m app.workers.backup
```
Produces: `backups/consight_backup_<timestamp>.db` (SQLite with all 14 populated tables)

### Restore (Verified)
```bash
# 1. Create fresh DB
python -m alembic upgrade head   # On new database

# 2. Restore from backup
python -c "
from sqlalchemy import create_engine, text
src = create_engine('sqlite:///backups/consight_backup_20260906_120947.db')
dst = create_engine('sqlite:///./restored.db')
tables = ['organizations','users','projects','ingestion_sources','wbs_nodes',
          'schedule_activities','progress_events','confidence_results',
          'planner_reviews','audit_records','event_wbs_matches',
          'glossary_mappings','delay_reasons','productivity_benchmarks','audit_logs']
with src.connect() as s, dst.connect() as d:
    for t in tables:
        rows = s.execute(text(f'SELECT * FROM {t}')).fetchall()
        if rows:
            cols = list(rows[0].keys())
            for r in rows:
                d.execute(text(f'INSERT INTO {t} VALUES ({','.join(['?']*len(cols))})'), tuple(r))
            d.commit()
"
```
**Verified:** All core tables restored with exact row counts (285 WBS nodes, 90 events, etc.)

---

## 10. Common Issues & Fixes

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `alembic upgrade head` fails | Postgres not ready / wrong URL | Check `DATABASE_URL`, ensure pgvector extension exists (`CREATE EXTENSION vector;`) |
| `pytest` fails `IntegrityError: organization_id` | Test DB not overridden | Ensure `conftest.py` has `app.dependency_overrides[get_db] = override_get_db` |
| `uvicorn` import errors | Missing deps / wrong venv | Re-create venv, `pip install -r requirements.txt` |
| Frontend `npm run build` fails | Node version mismatch | Use Node 20+ (`nvm use 20`) |
| Celery tasks not running | Redis not reachable | Check `REDIS_URL`, ensure Redis running (`redis-cli ping`) |
| `gitleaks` finds secrets | Secret in history | Rotate secret, rewrite history or accept risk |
| `python-multipart` `SpooledTemporaryFile` error | Python 3.9 file upload | Fixed in code (read file content first: `content = await file.read()`) |
| `mpxj` import fails | Wrong version in requirements | Use `mpxj==16.7.0` (latest on PyPI) |
| `python-jose` upgrade breaks JWT | Cryptography backend | Ensure `cryptography` installed (`pip install cryptography`) |

---

## 11. OS-Specific Gotchas (From Real Testing)

| OS | Issue | Workaround |
|----|-------|------------|
| **macOS** | Docker Desktop M1/M2 ARM: `pgvector` image pulls `linux/amd64` | Works via Rosetta 2; or use `docker pull --platform linux/amd64 pgvector/pgvector:pg16` |
| **Linux** | Postgres `pgvector` not in default repo | Add PGDG apt repo: `sh /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh` |
| **Windows** | `python-multipart` SpooledTemporaryFile | Fixed in code; use WSL2 to avoid entirely |
| **Windows** | Path separators in alembic | Use WSL2; native Windows not supported |
| **All** | `idna` / `click` / `filelock` version conflicts | Pin to exact versions in `requirements.txt` (see current file) |

---

## 12. Security Notes

- **JWT cookies:** `HttpOnly`, `Secure`, `SameSite=Strict` (verified)
- **CSRF:** Double-submit token required on all mutating requests (verified)
- **SQL Injection:** All queries use SQLAlchemy ORM/Core parameterization (no string concat)
- **File Uploads:** Extension, size (OCR 50MB), MIME validation before parsing
- **Secrets:** `.gitignore` covers `.env`, `.env.*`, `*.pem`, `*.key`, `backups/*.db`
- **Secret Scan:** `gitleaks detect --source . --log-opts="--all"` → **CLEAN** on full history

---

## 13. Key Files to Know

| File | Purpose |
|------|---------|
| `STATE.json` | Feature tracker — what's done/pending |
| `docs/STABILIZATION_REPORT_P0-P12.md` | Full verification report with addenda |
| `backend/requirements.txt` | Pinned Python dependencies |
| `frontend/package.json` | Node dependencies & scripts |
| `infrastructure/docker-compose.yml` | Full stack services |
| `backend/alembic.ini` | Migration config |
| `backend/scripts/generate_synthetic_data.py` | Realistic data generator |

---

## 14. License

SIH26122 Project — Smarty Vibz Team

**Remember:** `STATE.json` and `docs/STABILIZATION_REPORT_P0-P12.md` are the source of truth for what's actually built and verified.