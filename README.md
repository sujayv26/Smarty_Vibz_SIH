<!--
  Smarty Vibz / CONSight
  Smart Construction Progress & Schedule Intelligence
-->

<div align="center">

# 🏗️ CONSight
### From Field Progress to Schedule Intelligence

**An AI-assisted planning-to-execution platform that connects real-world construction updates with project schedules.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SIH](https://img.shields.io/badge/Smart%20India%20Hackathon-SIH%2026122-7C3AED?style=for-the-badge)](#)

<br/>

[**Repository**](https://github.com/sujayv26/Smarty_Vibz_SIH) · [**Setup Guide**](SETUP.md) · [**API Docs**](http://localhost:8000/docs)

</div>

---

## 📌 Overview

Construction projects rely on schedules such as **Primavera P6** and **Microsoft Project**, while actual site progress is often reported through daily reports, spreadsheets, supervisor messages, voice updates, and scanned diaries. Translating these updates into reliable schedule changes can be slow, fragmented, and difficult to audit.

**CONSight** bridges that gap. It turns field updates into structured progress events, matches them to schedule activities, evaluates confidence, and routes uncertain matches to a planner for review. Approved changes can then flow back into the schedule, with an audit trail.

The platform is developed for **Smart India Hackathon problem statement 26122** by the **Smarty Vibz** team.

> **Core principle:** AI assists the planner; uncertain schedule changes remain reviewable by a human.

---

## 🎯 The Problem

- Field progress information arrives in different formats and levels of detail.
- Reports may refer to activities using informal names, tags, locations, or partial descriptions.
- Manually mapping updates to schedule activities creates repetitive work and opportunities for error.
- Unplanned work and schedule changes need to remain visible and traceable.
- Planners need more than a prediction: they need evidence, confidence, and control over updates.

## 💡 The Solution

CONSight provides a structured workflow:

```text
Field Updates
(text · Excel · voice · scanned diaries · WhatsApp)
                    │
                    ▼
       Structured Progress Event
                    │
                    ▼
          Schedule Matching
   (exact · fuzzy · semantic · context · time)
                    │
                    ▼
          Confidence Evaluation
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
   High Confidence      Review Required
    Auto-match          Planner review
          │          approve / correct /
          │            reject / create
          └─────────┬─────────┘
                    ▼
       Schedule Update + Audit Trail
                    │
                    ▼
       Progress & Schedule Insights
```

---

## ✨ Core Capabilities

| Capability | What it does |
|---|---|
| **Schedule ingestion** | Imports schedule data from spreadsheets and supports Primavera P6 / Microsoft Project workflows. |
| **Progress extraction** | Converts text and spreadsheet updates into structured progress events. |
| **Multi-signal matching** | Uses exact, fuzzy, semantic, contextual, and temporal signals to identify candidate activities. |
| **Confidence-based routing** | Separates high-confidence matches from cases that need planner attention. |
| **Planner review** | Supports approving, correcting, rejecting, or creating an activity for unmatched work. |
| **Schedule integration** | Supports P6/XER import-export workflows and schedule actuals write-back on approval. |
| **Delay impact analysis** | Traces schedule relationships to understand potential downstream impact. |
| **Project analytics** | Surfaces discipline summaries, delay patterns, productivity benchmarks, and schedule variance trends. |
| **Delay prediction** | Provides ML-based project delay predictions and a risk watchlist. |
| **Voice and OCR** | Supports voice transcription and OCR processing for scanned site records. |
| **Auditability** | Keeps review decisions and schedule actions traceable. |

Feature status and implementation boundaries are documented in `STATE.json` and the stabilization report. See [Verified Implementation Status](docs/STABILIZATION_REPORT_P0-P12.md).

---

## 🔁 Confidence & Human Review

CONSight does not treat every model match as automatically correct. Matching results are routed according to confidence and review requirements.

| Scenario | System behaviour |
|---|---|
| Strong, unambiguous match | Can be routed as an automatic match according to configured thresholds. |
| Ambiguous candidates | Sent to the planner review queue. |
| No suitable activity | Planner can create a new activity and mark it as unplanned. |
| Incorrect candidate | Planner can correct or reject the proposed match. |

This workflow is designed to keep schedule updates explainable and under planner control.

---

## 🧪 Example Workflow

The repository documents three core end-to-end cases:

1. **Clear match:** a detailed field update matches a known schedule activity and passes the configured confidence threshold.
2. **Ambiguous match:** a short or underspecified update is sent for planner correction.
3. **Unmatched work:** an update with no suitable schedule match is reviewed and can become a new, explicitly unplanned activity.

For the exact sample inputs and verified outcomes, see the **Three-Case Core Demo** section in the repository documentation and the stabilization report.

---

## 🧠 Extended Intelligence

Beyond the core progress-to-schedule workflow, the implementation includes additional capabilities:

- **Schedule dependency analysis:** predecessor/successor relationships and critical-path exposure.
- **Institutional-memory analytics:** recurring delay patterns, discipline-level summaries, and productivity benchmarks.
- **ML delay prediction:** a Random Forest-based prediction workflow using engineered project features.
- **Multilingual extraction:** support for documented mixed-language input scenarios.
- **Voice processing:** speech-to-text integrated with the progress workflow.
- **Scanned-document processing:** OCR with confidence-aware review routing.

These capabilities depend on configuration, data, and external services where applicable. Consult the setup and status documentation before enabling them.

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     React + Vite Frontend                   │
│  Dashboard · Schedule · Planner Queue · Insights · Risk     │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST API
┌──────────────────────────────▼──────────────────────────────┐
│                       FastAPI Backend                        │
│ Auth/RBAC · Schedule · Progress · Matching · Reviews         │
│ Analytics · Delay Impact · Prediction · Voice · OCR          │
└───────────────┬──────────────────────┬──────────────────────┘
                │                      │
       ┌────────▼────────┐    ┌────────▼────────┐
       │ PostgreSQL      │    │ Redis + Celery  │
       │ + pgvector      │    │ Background work │
       └─────────────────┘    └─────────────────┘
                │
       ┌────────▼────────┐
       │ Schedule Tools  │
       │ P6 / XER / MPP  │
       └─────────────────┘
```

### Technology Stack

| Layer | Technologies |
|---|---|
| Backend API | Python, FastAPI, Pydantic |
| Frontend | React, Vite, TypeScript |
| Data layer | PostgreSQL, SQLAlchemy, Alembic, pgvector |
| Background jobs | Redis, Celery |
| ML / matching | Matching strategies, scikit-learn-based delay prediction |
| Schedule interoperability | Excel, Primavera P6/XER, Microsoft Project/MPP |
| Document & voice inputs | Tesseract OCR, speech-to-text pipeline |
| Deployment | Docker Compose |
| Testing | Pytest, frontend build and lint checks |

---

## 📁 Repository Structure

```text
Smarty_Vibz_SIH/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Versioned API routes
│   │   ├── core/            # Configuration, security, auth, Celery
│   │   ├── matching/        # Matching engine and strategies
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Request/response schemas
│   │   ├── services/        # Application and domain services
│   │   ├── workers/         # Background tasks
│   │   └── main.py          # FastAPI application
│   ├── alembic/             # Database migrations
│   ├── scripts/             # Seed and synthetic-data utilities
│   ├── tests/               # Backend tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   └── lib/
│   └── package.json
├── infrastructure/
│   └── docker-compose.yml
├── docs/
│   └── STABILIZATION_REPORT_P0-P12.md
├── SETUP.md
├── STATE.json
├── CHANGELOG.md
└── README.md
```

---

## 🚀 Getting Started

The project uses multiple services. **Docker Compose is the recommended setup** for running the full stack.

### Prerequisites

- Git
- Docker Desktop with Docker Compose v2 (or a compatible Docker/Podman setup)
- For local development: Python 3.11+, Node.js 20+, PostgreSQL with pgvector, and Redis

### 1. Clone the repository

```bash
git clone https://github.com/sujayv26/Smarty_Vibz_SIH.git
cd Smarty_Vibz_SIH
```

### 2. Configure the backend environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your local database, Redis, and application settings. **Never commit real credentials, API keys, or a populated environment file.**

### 3. Start the services

```bash
docker compose -f infrastructure/docker-compose.yml up -d --build
```

### 4. Apply database migrations

```bash
docker compose -f infrastructure/docker-compose.yml exec api python -m alembic upgrade head
```

### 5. Generate demo data

```bash
docker compose -f infrastructure/docker-compose.yml exec api python scripts/generate_synthetic_data.py --project DEMO-001 --org demo --weeks 4 --seed 42
```

### 6. Verify the API

```bash
curl http://localhost:8000/health
```

- API base URL: `http://localhost:8000`
- Interactive API docs: `http://localhost:8000/docs`

For the full local-development, frontend, worker, environment-variable, and OS-specific instructions, follow **[SETUP.md](SETUP.md)**.

---

## 🧪 Tests & Validation

The project includes a backend test suite and frontend validation commands.

### Backend

```bash
cd backend
python -m pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm run build
npm run lint
```

The repository's status documentation records the test and validation results. Re-run these commands in your own environment to verify the current checkout.

---

## 🗺️ Development Status

The repository tracks implementation by development phase. Use these documents as the source of truth:

- **[Implementation State](STATE.json)** — structured feature and phase tracking.
- **[Stabilization Report](docs/STABILIZATION_REPORT_P0-P12.md)** — verified implementation and validation notes.
- **[Changelog](CHANGELOG.md)** — development history.
- **[Setup Guide](SETUP.md)** — environment and operations.

Advanced items listed as future work in the state documentation should not be assumed to be implemented.

---

## 🔐 Security Notes

- Keep populated `.env` files and credentials out of version control.
- Replace development secrets before deploying.
- Use demo accounts only in a local demo environment; never expose default credentials in a public deployment.
- Configure CORS, authentication, and role permissions for your deployment.
- Review external service credentials and data-handling requirements before enabling integrations.

---

## 👥 Team

**Smarty Vibz**  
Smart India Hackathon · Problem Statement **26122**

This repository contains the team's implementation of CONSight, an AI-assisted construction progress and schedule intelligence platform.

## 📄 License & Usage

This repository is associated with the Smarty Vibz SIH project. No standard open-source license is specified here; contact the project maintainers before reusing or redistributing the code. Third-party libraries, pretrained models, and external datasets remain subject to their respective licenses and terms.

---

<div align="center">

### Turning site updates into schedule intelligence.

**Built for the planning-to-execution gap in construction projects.**

[Back to Repository](https://github.com/sujayv26/Smarty_Vibz_SIH)

</div>
