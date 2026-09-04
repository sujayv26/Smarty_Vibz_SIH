# Smarty Vibz - CONSight Schedule Interoperability

Phase 1, 2, 3 & 4 Implementation for SIH26122

## Overview

This project implements a schedule interoperability system that connects field progress reports with Primavera P6 schedules through a complete matching, confidence, and review workflow.

### Phases Implemented

- **Phase 1**: Schedule ingestion (Excel), progress extraction (free text + Excel), Time Agent chat interface
- **Phase 2**: Schedule matching engine (exact, fuzzy, semantic, context, temporal matchers)
- **Phase 3**: Confidence classification, planner review workflow, audit trail
- **Phase 4**: Primavera P6 XER import/export, schedule relationships, approved actuals export

## Architecture

```
backend/
├── app/
│   ├── api/                 # FastAPI route handlers
│   │   ├── schedule.py      # Excel schedule upload
│   │   ├── progress.py      # Progress extraction endpoints
│   │   ├── agent.py         # Time Agent chat
│   │   ├── matching.py      # Phase 2 matching
│   │   ├── confidence.py    # Phase 3 confidence evaluation
│   │   ├── reviews.py       # Planner review workflow
│   │   ├── audit.py         # Audit trail
│   │   ├── xer_import.py    # Phase 4: XER import & relationships
│   │   └── xer_export.py    # Phase 4: XER export with approved actuals
│   ├── core/
│   │   └── config.py        # Settings
│   ├── matching/
│   │   ├── engine.py        # Matching orchestration
│   │   ├── matchers/        # Individual matchers
│   │   ├── schemas.py       # Matching data models
│   │   └── service.py       # Matching service
│   ├── models/
│   │   ├── schedule.py      # ScheduleActivity model
│   │   ├── progress.py      # ProgressEvent model
│   │   ├── confidence.py    # Phase 3 models
│   │   └── xer.py           # Phase 4: ExternalSchedule, ScheduleRelationship
│   ├── schemas/             # Pydantic request/response models
│   ├── services/
│   │   ├── schedule_service.py     # Excel schedule validation/insertion
│   │   ├── progress_service.py     # Progress extraction
│   │   ├── excel_progress_service.py
│   │   ├── confidence_engine.py    # Confidence scoring
│   │   ├── confidence_service.py   # Confidence workflow
│   │   ├── extraction_service.py   # LLM provider abstraction
│   │   ├── llm_provider.py         # Real LLM provider
│   │   ├── mock_provider.py        # Offline mock provider
│   │   ├── xer/
│   │   │   ├── parser.py           # XER file parser
│   │   │   ├── service.py          # XER import service
│   │   │   └── export.py           # XER export service
│   ├── database.py          # SQLAlchemy setup
│   └── main.py              # FastAPI app entry point
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_phase1.py       # Phase 1 tests
│   ├── test_phase2.py       # Phase 2 tests
│   ├── test_phase3.py       # Phase 3 tests
│   └── test_phase4.py       # Phase 4 tests
└── fixtures/
    └── sample_schedule.xer  # Synthetic XER test fixture
```

## Requirements

- Python 3.12+
- Dependencies in `requirements.txt`

## Installation

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Application

```bash
cd backend
uvicorn app.main:app --reload
```

API Documentation: http://localhost:8000/docs

## API Endpoints

### Phase 1 - Schedule & Progress

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/schedule/upload` | Upload Excel schedule (.xlsx) |
| GET | `/schedule/activities` | List all schedule activities |
| POST | `/progress/extract` | Extract progress from free text |
| POST | `/progress/upload-excel` | Upload progress from Excel |
| GET | `/progress/events` | List progress events |
| POST | `/agent/chat` | Time Agent chat interface |
| GET | `/agent/sessions/{session_id}/events` | Get session events |

### Phase 2 - Matching

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/matching/run/{progress_event_id}` | Run matching for progress event |
| POST | `/matching/benchmark` | Run benchmark suite |

### Phase 3 - Confidence & Review

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/confidence/evaluate/{progress_event_id}` | Evaluate confidence |
| GET | `/reviews/pending` | List pending reviews |
| GET | `/reviews/{review_id}` | Get review details |
| POST | `/reviews/{review_id}/approve` | Approve match |
| POST | `/reviews/{review_id}/correct` | Correct to different activity |
| POST | `/reviews/{review_id}/reject` | Reject match |
| POST | `/reviews/{review_id}/create-new` | Create new unplanned activity |
| GET | `/audit/{progress_event_id}` | Get audit trail |

### Phase 4 - P6/XER Interoperability

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/schedule/import/p6` | Import Primavera P6 .xer file |
| GET | `/schedule/relationships` | Get schedule relationships |
| GET | `/schedule/external-schedules` | List imported external schedules |
| GET | `/schedule/external-schedules/{id}/activities` | Get activities for external schedule |
| POST | `/schedule/export/p6/{external_schedule_id}` | Export XER with approved actuals |
| GET | `/schedule/export/p6/{external_schedule_id}/preview` | Preview export content |

## XER Import/Export

### Import Flow

1. Upload `.xer` file via `POST /schedule/import/p6`
2. Parser extracts activities, WBS, planned dates, relationships
3. Activities mapped to internal `ScheduleActivity` model
4. Relationships persisted in `ScheduleRelationship` table
5. External IDs preserved for traceability

### Export Flow

1. Run Phase 2 matching + Phase 3 review for progress events
2. Planner approves actual start/finish dates
3. Export via `POST /schedule/export/p6/{external_schedule_id}`
4. Exported XER contains:
   - All original activities with planned dates
   - Approved actual start/finish dates
   - Predecessor-successor relationships with lag
   - Original external identifiers preserved

### Supported Relationship Types

- **FS** - Finish to Start
- **SS** - Start to Start
- **FF** - Finish to Finish
- **SF** - Start to Finish

Lag values preserved in days.

## Testing

```bash
cd backend
python -m pytest tests/ -v
```

### Test Coverage

- **135 tests total** (105 Phase 1-3 + 30 Phase 4)
- All tests run offline (no internet, no LLM API, no P6 installation)
- Synthetic XER fixture with 11 activities, 11 relationships (FS, SS, FF, SF, lag)
- End-to-end test: XER import → progress → matching → confidence → review → export

### Phase 4 Test Categories

- **Parser tests**: Valid XER, activity extraction, WBS mapping, all 4 relationship types, lag, empty/malformed XER, duplicate IDs, missing names
- **Import service tests**: Activity creation, relationship persistence, external ID preservation, Excel coexistence, self-ref rejection, invalid ref rejection
- **Export tests**: Valid XER output, approved actuals, unapproved actuals excluded, relationships preserved, original file unchanged
- **API tests**: Import endpoint, relationships endpoint, external schedules endpoint
- **End-to-end test**: Complete workflow from XER import to approved export

## Data Models

### ScheduleActivity (Extended for Phase 4)

```python
activity_code: str          # Unique identifier
activity_name: str
discipline: str
wbs: str
planned_start: date
planned_finish: date
is_unplanned: bool
source_format: str          # "EXCEL" or "XER"
external_schedule_id: int   # FK to ExternalSchedule
external_activity_id: str   # Original P6 task_id
```

### ExternalSchedule (New)

```python
external_schedule_id: str   # P6 proj_id
schedule_name: str
source_filename: str
source_format: str          # "XER"
imported_at: datetime
```

### ScheduleRelationship (New)

```python
predecessor_activity_id: int
successor_activity_id: int
relationship_type: str      # FS, SS, FF, SF
lag: int                    # Days
lag_unit: str               # "days"
external_schedule_id: int   # FK to ExternalSchedule
```

## Validation & Error Handling

### Import Validation

- Empty XER file → Clear error
- Malformed XER → Clear error with line context
- Missing activity ID → Rejected with record
- Missing activity name → Rejected with record
- Invalid dates → Rejected with record
- Duplicate activity IDs → First kept, rest rejected
- Self-referencing relationships → Rejected
- Invalid relationship references → Rejected

### Export Safety

- Never overwrites original imported file
- Only approved actual dates exported (APPROVED, CORRECTED, NEW_ACTIVITY_CREATED)
- Unapproved (PENDING, REJECTED, AUTO_MATCH without review) excluded
- Unsupported fields documented in warnings

## MPP Support Status

Microsoft Project .MPP native import/export is **not implemented**. The XER adapter interface is designed for future extension. For MPP interoperability, export to XER from MS Project first.

## Limitations

- No delay ripple calculation
- No critical path prediction
- No productivity analytics
- No institutional memory analytics
- No multilingual extraction (Hinglish, Tamil-English)
- No WhatsApp integration
- No frontend/dashboard
- MPP support requires separate investigation

## License

SIH26122 Project - Smarty Vibz Team