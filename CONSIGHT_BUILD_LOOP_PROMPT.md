# ConSight / Smarty Vibz — Autonomous Build-Out Loop Prompt

**Purpose of this file:** this is a *loop prompt*. Feed it to Claude Code (or an
equivalent agentic coding tool) as the system/task prompt on every iteration —
either manually, or wrapped in a runner like:

```bash
while true; do
  claude --dangerously-skip-permissions -p "$(cat CONSIGHT_BUILD_LOOP_PROMPT.md)"
  if grep -q '"status": "COMPLETE"' STATE.json; then break; fi
done
```

Each iteration reads `STATE.json` (created on first run — see §2), does **one
unit of work** from the backlog in §5, verifies it, updates `STATE.json` and
`CHANGELOG.md`, commits, and stops. The next iteration picks up exactly where
the last one left off. Do not try to do the whole backlog in one shot — one
coherent, fully-tested, fully-wired unit per iteration, always leaving the repo
in a working, deployable state.

---

## 0. Non-negotiable ground rules (apply on every iteration, no exceptions)

1. **No demo-ware.** Every button, form, page, and API call must be fully
   wired to a real backend endpoint and a real database row. Never ship a
   placeholder button, a "coming soon" state, a fake toast with no underlying
   action, or a hardcoded/mocked response *in the product surface* (mocking is
   fine only inside `tests/` or behind an explicit `LLM_PROVIDER=mock`
   developer flag documented in `.env.example`). If a feature can't be fully
   wired in this iteration, don't render its UI yet — build backend-first,
   surface it in the UI only once it's real.
2. **Postgres is the system of record.** SQLite is retained *only* as a local
   safety/backup mechanism (see §4.2) — never as the primary database for any
   environment, including local dev. If you find yourself about to add a
   feature against SQLite, stop and wire it against Postgres instead.
3. **Every unit of work ends in a green build.** Backend: `pytest` passes,
   `alembic upgrade head` runs clean against a fresh Postgres, `uvicorn`
   boots. Frontend: `npm run build` and `npm run lint` pass, no console
   errors on the pages you touched. If you can't get to green in this
   iteration, revert to the last green commit rather than leaving the repo
   broken — a smaller shippable increment beats a larger broken one.
4. **Traceability.** Every feature you build must map to a PRD section, an
   add-on-phase requirement, or an explicitly-requested "out of scope"
   feature (see §5.9). Cite the section in the commit message and in
   `STATE.json`'s `notes` field. Don't invent unrequested scope.
5. **Enterprise visual bar.** Every screen you build or touch must conform to
   the design system in §6. No default browser form styling, no unstyled
   loading states, no Bootstrap/Material-defaults look. If a page you're
   implementing doesn't yet have a design-system treatment, design it
   consistently with §6 before shipping it — don't ship an unstyled page
   "to fix later."
6. **Secrets never get committed.** From the very first commit, a `.gitignore`
   covering `.env`, `.env.*` (except `.env.example`), `*.pem`/`*.key`,
   `backups/*.db` (the SQLite backup dumps from §4.2, which contain real
   data), `node_modules/`, `__pycache__/`, build output, and any local
   credential/cache files must exist and be committed *before* any file
   that could contain a secret is ever written. Every credential (DB URL,
   JWT signing key, WhatsApp Cloud API token, weather API key, LLM
   provider key, OCR/cloud service keys) is read from environment
   variables via `.env`, never hardcoded, with a `.env.example` (safe
   placeholders only) checked in instead. Treat "did I just commit a
   secret" as a check on every commit in every iteration, not just once.
7. **Never break the three-case core demo.** Clean auto-match, ambiguous
   match requiring planner correction, and unmatched → new-activity —
   this flow (Phase 1-4) must keep working after every change. Run it as a
   smoke test before ending each iteration.
8. **Real synthetic data, not toy data.** The synthetic dataset generator
   (§4.4) must produce data realistic enough that every dashboard, chart,
   and analytics view looks populated and credible in a screen-recording —
   multiple disciplines, multiple contractors, a full L1–L6 WBS tree,
   weeks of field events, some delays, some corrections, some new-activity
   discoveries.
9. **Security is a default, not a phase.** PRD §10's OWASP Top 10 posture
   applies to every phase you build, not just `P0-auth-rbac`. Concretely,
   on every iteration that adds an endpoint, form, or file-handling path:
   - Validate and size-limit every upload (P6 schedule exports, WhatsApp
     media, scanned diaries for OCR, IFC/BIM models) — reject oversized or
     wrong-mimetype files before they reach a parser; parse untrusted
     files (`.xer`/`.mpp`/IFC/images) in a way that can't execute code or
     exhaust memory on a crafted file.
   - Treat all free-text field input (voice transcripts, WhatsApp
     messages, diary OCR output) as untrusted input to the LLM extractor:
     keep the system-prompt/user-input boundary strict so field text can
     never override extraction schema or agent instructions (PRD §10.3).
   - Every new query path is parameterized (SQLAlchemy ORM/Core) — no
     string-concatenated SQL, ever.
   - Every new list/detail endpoint enforces `organization_id`/
     `discipline`/`project_id` scoping and role checks before returning
     data — don't rely on the frontend to hide what a role shouldn't see.
   - Run `pip-audit`/`npm audit` (or equivalent) as part of verification
     (§7) whenever `requirements.txt`/`package.json` changes, and don't
     introduce a new dependency with a known high/critical CVE without
     flagging it in `STATE.json` notes.

---

## 1. Source-of-truth documents (already in the repo's `/docs` — copy them in
   if missing before you start)

- `PRD_Intelligent-Data-Capture-Schedule-Linking-Layer_v2_2_0.pdf` — the
  canonical PRD (v2.2.0). Sections referenced below as `PRD §n`.
- `ConSight___Feature_Analysis___Recommendation_Rationale.pdf` — why Phase
  5-9 exist and what they must each demonstrate.
- `ConSight_Post_Phase_4_Add_On_Features_SIH26122.pdf` — the concrete
  Phase 5-9 implementation plan and Definition of Done.
- This file (`CONSIGHT_BUILD_LOOP_PROMPT.md`) — supersedes the above two
  add-on docs on one point only: **do not treat anything as "drop for SIH" /
  "do NOT add before internal SIH."** Per the user's explicit instruction,
  every feature those two documents deferred or dropped (BIM/digital twin,
  weather/external context, multi-project/enterprise layer, native-grade
  mobile capture, advanced RAG, ML-based delay prediction, voice, OCR) is
  **in scope** for this build. See §5.9.

If any of the four PDFs are not present at repo root under `/docs`, ask the
user for them before starting work that depends on them — don't guess at
content you haven't read.

**Branch reality check.** This repository has multiple diverged branches
(`main`, `phase4-p6-mpp-integration`, `PhaseP0-P12`,
`constructiq-add-on-phase5-9` as of this writing — there may be more by
the time you read this). Their names and any spec/doc files they contain
describe *intended* work and are not evidence anything is actually built.
You are working on a single branch checked out from whichever of these
had the most genuine implemented code (verified by reading it, not by
name) — confirm with `git log --oneline --all` and a read of the actual
diffs between branches if you're unsure which one that is, rather than
assuming the most recently-touched or most impressively-named branch is
most complete.

---

## 2. State tracking — read this first, every iteration

**Before creating or trusting any `STATE.json`, audit the real repo.** This
repo has accumulated multiple branches and spec documents describing
intended work (Phase 5-8 write-ups, a "PhaseP0-P12" branch name) that do
**not** reflect actual implemented code — do not treat a branch name, a
folder of `.txt`/`.pdf` phase documents, or a prior `STATE.json` claim as
evidence that something is built. The only trustworthy signal is code you
have personally read and a test/build you have personally run. Concretely,
on the very first iteration:

1. Read every file under `backend/app/` (services, api, models) and the
   frontend directory if one exists. For each backlog item below, check
   whether it is genuinely, fully implemented (not a doc describing it,
   not a partial stub) — e.g. "WhatsApp integration" only counts as done
   if a real webhook handler exists and is wired to the extraction
   pipeline, not if only a spec `.txt` file exists.
2. Check `requirements.txt`/`package.json` for the dependencies each item
   actually needs (e.g. no `asyncpg`/`psycopg2` + no Postgres in
   `docker-compose.yml` means Postgres infra is *not* done, regardless of
   what any branch or prior note claims).
3. Initialize `STATE.json` (below) with `done: true` **only** for items
   you've verified this way. Mark anything partially built (e.g. an XER
   importer exists but has no predecessor/successor mapping, or no
   MS Project `.mpp` support, or doesn't write back on planner approval)
   as `done: false` with a `notes` entry describing exactly what exists
   and what's missing, so the next iteration completes it rather than
   rebuilding it from scratch.
4. Do this audit once, thoroughly, and commit the resulting `STATE.json`
   immediately — this commit is the new baseline for everything after it.

On the very first iteration, if `STATE.json` doesn't exist, create it at
repo root:

```json
{
  "status": "IN_PROGRESS",
  "current_phase": null,
  "backlog": [
    { "id": "P0-audit", "done": false },
    { "id": "P0-infra-postgres", "done": false },
    { "id": "P0-infra-redis-celery", "done": false },
    { "id": "P0-auth-rbac", "done": false },
    { "id": "P0-sqlite-backup", "done": false },
    { "id": "P0-synthetic-data", "done": false },
    { "id": "P0-design-system", "done": false },
    { "id": "P0-frontend-shell", "done": false },
    { "id": "P0-landing-page", "done": false },
    { "id": "P5-p6-roundtrip", "done": false },
    { "id": "P6-whatsapp", "done": false },
    { "id": "P7-multilingual", "done": false },
    { "id": "P8-delay-ripple", "done": false },
    { "id": "P9-institutional-memory", "done": false },
    { "id": "P10-ml-delay-prediction", "done": false },
    { "id": "P11-voice-agent", "done": false },
    { "id": "P12-ocr-scanned-diaries", "done": false },
    { "id": "P13-advanced-rag", "done": false },
    { "id": "P14-weather-context", "done": false },
    { "id": "P15-bim-digital-twin", "done": false },
    { "id": "P16-multi-project-enterprise", "done": false },
    { "id": "P17-offline-mobile-pwa", "done": false },
    { "id": "P18-frontend-consistency-pass", "done": false },
    { "id": "P21-hardening-observability", "done": false },
    { "id": "P22-e2e-verification", "done": false }
  ],
  "notes": []
}
```

**Every backlog item stays `false` by default in this template — flip an
item to `true` only after step 1-3 of the audit above has genuinely
verified it, never on initialization by assumption.** Expect
`P5-p6-roundtrip` to likely end up partially credited from the real XER
work already on this branch — verify what's there against the full §5.1
spec (predecessor/successor import, `.mpp` support, write-back on
approval, export) before deciding whether to mark it done or leave it
`false` with a completion note.

**`STATE.json` must be committed at the end of *every* iteration, no
exceptions** — even though you're not pushing to GitHub yet, a local
commit is what makes this workflow resumable across sessions, restarts,
and even a different agent picking up later. A `STATE.json` that only
exists uncommitted in a working directory is exactly the failure mode
that caused this consolidation to be necessary in the first place.

Each iteration:
1. Read `STATE.json`. Find the first item with `"done": false`, in list
   order (order encodes dependency — don't skip ahead; a later item may
   assume an earlier one exists, e.g. delay ripple needs the P6 import's
   predecessor/successor data).
2. Read the corresponding backlog spec in §5.
3. Implement it completely (backend + migration + tests + frontend wiring +
   design-system-conformant UI, as applicable to that item).
4. Run the verification steps in §7.
5. Flip `"done": true` for that item, append a one-line note describing what
   was built and which PRD/add-on section it satisfies, commit
   (`git commit -m "<phase-id>: <summary>"`), and stop.
6. If every item is `"done": true`, run the full Definition of Done in §8;
   if it all passes, set `"status": "COMPLETE"` and stop.

If you discover mid-iteration that a backlog item is bigger than one
iteration should be, split it into `<id>-a`, `<id>-b`, ... in `STATE.json`
and proceed with part `a` only.

### 2.1 Session & token efficiency (applies to how you run every iteration)

- **Prefer a fresh agent session per iteration** (or every 2-3 iterations)
  over one continuously-growing session. `STATE.json` plus `git log` is
  the *entire* persistence mechanism this workflow needs — conversation
  history is not load-bearing. A session that keeps accumulating every
  prior tool call and file read burns far more tokens per unit of work
  than a fresh session that reads only `STATE.json`, the one relevant §5
  spec section, and the specific files it's about to touch.
- **Never re-parse the full PDF source docs from scratch each iteration.**
  The first time you need a section, extract just that section into a
  short markdown note under `docs/notes/` (e.g. `docs/notes/prd-s9-
  schema.md`, `docs/notes/addon-phase5.md`, capped at roughly a page) and
  read that note on later iterations instead of re-opening the PDF.
- **Read narrowly.** Use targeted views/greps for the specific files an
  iteration touches; don't dump the whole repo tree or an entire large
  file when a grep or a section view answers the question.
- **Run targeted tests while developing**, and reserve the full test
  suite plus the full three-case smoke test for the one verification pass
  in §7 per iteration — don't re-run either after every small edit within
  the same iteration.
- **Keep your own output terse.** The work product lives in the
  filesystem and git history, not in chat prose — don't paste full file
  contents or full diffs back into your response; a one- or two-line
  summary per file touched is enough. Verbose self-narration costs tokens
  without adding anything the state file and commit history don't already
  capture.
- **Batch related edits** into as few tool calls as sensibly possible
  rather than one call per line changed.

---

## 3. Target architecture (end state)

```
consight/
├── backend/                       # FastAPI (Python 3.11+)
│   ├── app/
│   │   ├── api/v1/                 # versioned routers per PRD §8.5
│   │   ├── core/                   # config, security, redis, celery app
│   │   ├── db/                     # SQLAlchemy models, Alembic env
│   │   ├── schemas/                # Pydantic v2 models
│   │   ├── services/                # extraction, matching, confidence,
│   │   │                             p6 import/export, whatsapp, delay
│   │   │                             ripple, analytics, RAG, ML prediction,
│   │   │                             voice, OCR, weather, BIM, backup
│   │   ├── workers/                 # Celery tasks (async matching, backup,
│   │   │                             benchmark recompute, WhatsApp webhook
│   │   │                             processing, ML retraining)
│   │   └── main.py
│   ├── alembic/                     # migrations — the only way schema changes
│   ├── tests/
│   └── requirements.txt
├── frontend/                        # React + Vite + TypeScript
│   ├── src/
│   │   ├── app/                     # routed screens (see §6.4)
│   │   ├── components/              # design-system primitives (§6)
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── lib/                     # API client, auth context
│   │   └── styles/                  # tokens.css, fonts
│   └── package.json
├── infrastructure/
│   ├── docker-compose.yml           # postgres, redis, celery worker,
│   │                                   celery beat, api, web, minio (for
│   │                                   file/photo/scan storage)
│   ├── k8s/
│   └── terraform/
├── scripts/
│   ├── generate_synthetic_data.py   # §4.4
│   ├── backup_to_sqlite.py          # §4.2
│   └── seed_demo_project.py
└── docs/                             # the 4 source docs live here
```

**Primary stack (must match exactly):**
- DB: **PostgreSQL 16 + pgvector**, connection-pooled via PgBouncer.
- Cache/broker: **Redis** (Celery broker + result backend + WBS baseline
  cache + refresh-token store).
- Async workers: **Celery** (matching pipeline, WhatsApp ingestion, backup
  job, benchmark recompute, ML retraining, delay-ripple recompute).
- Auth: **JWT** (short-lived access token, opaque refresh token rotated in
  Redis, delivered via `HttpOnly`/`Secure`/`SameSite=Strict` cookies —
  never `localStorage`), full RBAC per PRD §10.4.
- Frontend: React + Vite + TypeScript, matching the design system in §6.

---

## 4. Foundational infrastructure work (Phase 0 — do this before any Phase
   5-22 feature work; these are the `P0-*` items in `STATE.json`)

### 4.1 P0-audit
Re-scan the actual current repo state (branches, files, endpoints, DB
schema) before trusting any summary written previously — the repo may have
moved since this prompt was drafted. Record the delta as the first `notes`
entry in `STATE.json`.

### 4.2 P0-infra-postgres / P0-infra-redis-celery
These two `STATE.json` items are tightly coupled (same docker-compose
pass, same Alembic setup) — it's fine to complete both in a single
iteration and flip both `done` flags together; don't force an artificial
split if the combined unit is still small enough to verify cleanly.
- Stand up Postgres 16 with the `vector` extension, Redis, and Celery
  (worker + beat) in `docker-compose.yml` and in the Alembic-driven schema.
- Port the existing Phase 1-4 SQLAlchemy models (`schedule_activities`,
  `progress_events`, `confidence_results`, `planner_reviews`,
  `audit_records`) onto the PRD §9 schema: add `organizations`, `users`,
  `projects`, `ingestion_sources` (lookup table, not enum — see PRD §9's
  rationale), `wbs_nodes.description_vector vector(1536)` with an HNSW
  index, `event_wbs_matches` (nullable `wbs_id`, `match_type`,
  `progress_contribution_pct`), `glossary_mappings`, `delay_reasons`,
  `productivity_benchmarks`, and immutable `audit_logs`. Reconcile field
  names between the old SQLite models and the PRD schema — the PRD schema
  wins; migrate/rename rather than running two parallel schemas.
- All schema changes go through Alembic migrations, checked into
  `backend/alembic/versions/`. No `Base.metadata.create_all()` in
  production code paths — that's dev-convenience only, and even then should
  be replaced by "run migrations on boot."
- **SQLite backup mechanism** (this replaces SQLite-as-primary): a Celery
  Beat job (`scripts/backup_to_sqlite.py`, run e.g. hourly) that dumps a
  point-in-time, restorable snapshot of core tables to a local
  `backups/consight_backup_<timestamp>.db` SQLite file, with a retention
  policy (keep last N) and a documented restore procedure in `docs/`.

### 4.3 P0-auth-rbac
Implement PRD §10 exactly: JWT access + rotated Redis-backed refresh
tokens, HttpOnly cookie transport, CSRF double-submit token on
state-changing requests, `@requires_role([...])` dependency injection,
`organization_id`/`discipline` scoping on every query touching field
events or matches, strict CORS allowlist, TLS assumed terminated upstream.
Seed the five personas from PRD §5 (Site Supervisor, Discipline Planner,
Project Controls/Admin, Contractor Admin, System/DevOps) with a login
screen and role-appropriate navigation (§6.4).

### 4.4 P0-synthetic-data
Build `scripts/generate_synthetic_data.py` as a first-class, re-runnable
tool (not a one-off script) that generates a full synthetic dataset
directly in Postgres:
- 2-3 organizations (one owner/EPC, 2+ subcontractors), users across all
  five roles and multiple disciplines and languages.
- A realistic multi-discipline L1-L6 WBS tree (hundreds of activities)
  with predecessor/successor relationships (needed by delay ripple, §5.4).
- Weeks of field events across every `ingestion_sources` channel (voice,
  time-agent, text diary, spreadsheet, PDF/OCR, PMIS export, and
  WhatsApp once built), in English and code-mixed languages, with a
  realistic confidence-score distribution across auto-commit / review /
  new-activity buckets, some human corrections (populating
  `glossary_mappings`), some delays (populating `delay_reasons`), and
  enough closed/aged data to populate `productivity_benchmarks` and the
  institutional-memory views meaningfully.
- Idempotent and parameterized (`--project`, `--weeks`, `--seed`) so it can
  reset a demo environment on demand.

### 4.5 P0-design-system / P0-frontend-shell / P0-landing-page
Build, in this order, *before* any Phase 5+ backend work:
1. **`P0-design-system`** — the reusable tokens/components described in
   §6.2 (colors, fonts, badge/pill primitives, chart theme, motion
   primitives), so every later screen consumes them rather than
   reinventing styling.
2. **`P0-frontend-shell`** — the routed application shell: auth-gated
   layout, role-aware nav, an empty-but-real placeholder route for each
   screen listed in §6.4 (each route renders a real "connected, no data
   yet" state backed by a real API call that currently returns an empty
   result — never a static mock), and the project switcher stub.
3. **`P0-landing-page`** — the public landing/sign-in gateway per §6.1,
   wired to the real login flow from §4.3.

This exists so that **every Phase 5+ item builds its frontend screen
directly into a shell that already exists**, rather than backend phases
piling up with no UI until some later "build the frontend" phase. Each
phase in §5 that specifies a "Frontend: ..." deliverable does that work
*as part of that phase's own iteration* — it fills in a route that
already exists in the shell, wires it to that phase's new endpoint, and
flips that phase's `done` flag only once both backend and frontend for it
are real and working. Do not defer frontend work to the end.

`P18-frontend-consistency-pass` (near the end of the backlog, after
P5-P17) is deliberately **not** "build the frontend now" — by that point
every screen should already exist and be wired, one phase at a time. That
pass is a final design-system audit across every screen built along the
way: confirm nothing drifted from §6's tokens, no screen was left in a
placeholder/empty state from §4.5 step 2 that a later phase forgot to
fill in, and cross-screen consistency (nav, loading states, empty states,
error states) holds across the whole app.

---

## 5. Feature backlog (Phase 5 onward)

For each phase below: implement backend service + API endpoints (versioned,
per PRD §8.5) + Alembic migration if schema changes + Celery task if async +
tests + the corresponding frontend screen(s) in the design system. Update
the Problem-to-Solution Traceability Matrix (PRD §18) — extend it in
`docs/TRACEABILITY.md` with a row per phase below, mapping to PRD
requirements and add-on-doc phases.

### 5.1 P5 — Primavera P6 / MS Project round-trip
Per PRD §8.2 `/api/v1/schedule/upload` and the add-on doc's Phase 5. Import
`.xer` (via `xerparser`) and `.mpp` (via `mpxj`/`aspose-tasks`) exports:
activity IDs, names, planned/actual dates, discipline, WBS hierarchy,
predecessor/successor relationships with lag and relationship type
(FS/SS/FF/SF). Map into `wbs_nodes` (upsert by `activity_code`, don't
duplicate on re-import). On planner approval of a match
(`/api/v1/schedule/matches/{match_id}/resolve`), write the actual
start/end back to the node and expose an export endpoint that serializes
current actuals back into `.xer`/MSP-compatible format for download.
Frontend: a Schedule Import screen with upload, parse preview/diff, and
commit; an Export action from the schedule view.

### 5.2 P6 — WhatsApp field reporting
WhatsApp Business Cloud API webhook (`/webhooks/whatsapp/inbound`),
verified per Meta's signature scheme, feeding the *same*
extraction → matching → confidence pipeline as `/api/v1/events/ingest` —
do not fork the pipeline. Persist inbound messages as `field_events` with
`source_type = 'WHATSAPP'` (insert into `ingestion_sources`, no migration
needed — this is the point of that table per PRD §9). Send a
confirmation/status reply back to the supervisor via the Cloud API.
Frontend: a live "Inbound Channels" panel on the Planner dashboard showing
WhatsApp messages arriving and resolving in real time (via WebSocket or
SSE off the Celery result, not polling-only).

### 5.3 P7 — Multi-language / code-mixed extraction
Extend the extraction prompt/service (`llm_extractor.py`) to reliably
parse Hindi-English, Tamil-English, Telugu-English, and other code-mixed
input while preserving activity codes and technical terms, outputting the
same standardized JSON regardless of input language (PRD §6.1). Build and
check in a benchmark set of 25-30 realistic code-mixed messages under
`backend/tests/fixtures/multilingual_benchmark.json` with an automated
accuracy test that must stay above an agreed threshold. Store
`users.preferred_language` and let the Time-Agent (§5.11) respond in the
supervisor's language.

### 5.4 P8 — Delay ripple / critical-path impact
Deterministic graph traversal (not ML) over the predecessor/successor
data imported in §5.1: when a `DELAY` event is approved, walk the
successor chain, compute propagated delay per relationship type and
available float, and flag critical-path exposure. Persist results so
they're queryable, not just computed on the fly (for the dashboard and
for feeding P9 analytics and P10's ML training data later). Frontend:
a delay-impact panel showing the affected downstream activities and a
clear critical-path warning, on both the event detail view and the
schedule view.

### 5.5 P9 — Productivity & institutional-memory analytics
SQL aggregations over `audit_logs`/`field_events`/`delay_reasons` per PRD
§6.6: actual vs. planned duration by discipline, recurring delay-cause
patterns, discipline-wise productivity index, variance trend over time.
Expose via `/api/v1/analytics/discipline-summary` and
`/api/v1/knowledge-base/benchmarks` (already specified in PRD §8.4).
Frontend: an Insights/Institutional Memory dashboard with real charts (no
static images) driven by these endpoints.

### 5.6 P10 — ML-based delay prediction *(explicitly requested — was
   deferred in the add-on docs; build it now)*
A real, trained model (not a rules stand-in) predicting delay likelihood
and expected delay magnitude for in-progress activities, trained on the
`productivity_benchmarks`/`delay_reasons` corpus (real once §4.4's
synthetic data and ongoing field events populate it). Ship it as a Celery
periodic retraining task plus a serving path (`/api/v1/analytics/delay-
predictions`) with a documented feature set, evaluation metrics logged
per training run, and a visible confidence indicator in the UI so it's
never presented as a certainty. Frontend: a "Predicted Risk" indicator on
at-risk activities and a ranked watchlist view.

### 5.7 P11 — Voice processing for the Time-Agent
Real speech-to-text (Whisper) integrated into the existing
`/api/v1/agent/chat` conversational flow (PRD §6.2) as an additional
input mode alongside text, in the supervisor's `preferred_language`,
producing the same standardized extraction JSON. Persist the raw audio
reference and transcript for audit per PRD §6.2. Frontend: a real
press-to-talk control in the Time-Agent UI with live waveform/transcript
feedback, not a decorative mic icon.

### 5.8 P12 — OCR of scanned diaries
Real OCR pipeline (e.g. Tesseract or a cloud OCR provider) for scanned
PDF/image daily diaries, feeding the same extraction pipeline with
`source_type = 'PDF_OCR'`. Handle low-confidence OCR gracefully — route
to the review queue rather than silently accepting garbled text.
Frontend: an upload flow showing the scanned page alongside the extracted
text for supervisor/planner verification.

### 5.9 P13-P16 — Everything the add-on docs deferred, now in scope

> These four were explicitly called out as "do NOT add" / "drop for SIH" in
> the two add-on-phase PDFs. The user has explicitly asked for them to be
> built anyway, at full production quality. Build each as a real,
> functioning capability, not a stub.

- **P13 — Advanced RAG over institutional memory.** A proper
  retrieval-augmented pipeline (embeddings of `delay_reasons`,
  `productivity_benchmarks`, closed-project summaries, glossary entries,
  stored in pgvector) behind a natural-language query endpoint
  (`/api/v1/knowledge-base/query`), e.g. "P90 actual duration for 24-inch
  piping installation in wet weather, past projects." Frontend: a
  conversational knowledge-base search screen, separate from the
  Time-Agent, with cited source rows for every answer (no unsourced
  claims).
- **P14 — Weather & external context.** Ingest weather data (a real
  weather API, geolocated per project site) and attach it as context to
  field events and delay records, feeding both the delay-ripple analysis
  (§5.4) and the ML predictor (§5.6) as an additional feature. Frontend:
  a weather context strip on the project dashboard and a "weather-linked
  delays" filter in the analytics view.
- **P15 — BIM / digital twin integration.** IFC model ingestion, mapping
  model elements to WBS activities, and a real 3D viewer (e.g. `web-ifc` /
  `IFC.js` / `three.js`) that colors elements by actual progress status
  pulled from `wbs_nodes`. This is the largest single item in the
  backlog — split it across multiple `STATE.json` sub-items
  (`P15-a` model ingestion & mapping, `P15-b` viewer, `P15-c` progress
  color-coding) rather than attempting it in one iteration.
- **P16 — Multi-project / enterprise layer.** Full multi-tenancy:
  `project_id` scoping enforced everywhere it isn't already, a project
  switcher in the shell nav, project-level RBAC (a Contractor Admin scoped
  to one project shouldn't see another), and cross-project
  Admin/PMO rollup dashboards distinct from the per-project ones.

### 5.10 P17 — Offline-capable mobile PWA
A real installable PWA (service worker, offline shell, background sync)
for the Site Supervisor role specifically: local queueing of field events
captured with no connectivity, synced via idempotent `event_id` once
connectivity returns (PRD's own risk register, §17, flags this exact
scenario). This satisfies the "native mobile app" ambition without a
separate Flutter/React Native codebase, per the add-on doc's own
reasoning — but must be a genuinely offline-first, installable
experience, not just a responsive website.

### 5.11 Conversational Time-Agent — not a separate `STATE.json` id
This is not its own backlog item; it's a cross-cutting requirement folded
into `P7-multilingual` and `P11-voice-agent` above. When you complete
those two, confirm as part of their own verification that
`/api/v1/agent/chat` and `/api/v1/agent/sessions/{id}/events` (PRD §8.3)
are fully production-wired end to end, with every session persisted to
`field_events.raw_input_text` for audit per PRD §6.2.

---

## 6. Frontend design system (applies to *every* screen, not just the
   landing page)

The brief below (verbatim client spec + reference screenshot) is written
for a single marketing landing page. Treat it as the **design token
source**, then extend those tokens into a full enterprise application
shell — do not literally build only a video-background hero and stop.
"Professional enterprise level deployed" means the dashboards, queues, and
data-dense screens need the same discipline (typography, restraint,
consistent motion) as the hero — not the same literal video-hero layout,
which is inappropriate for a data-dense planner queue.

### 6.1 Landing page (marketing/sign-in gateway) — build exactly as specified

Reproduce the attached spec precisely: full-bleed looping video background,
`BubbledotICG-FinePos` retro dot-matrix display font for the headline and
stat glyphs, Inter for UI text, the exact header/pill-nav/trust-row/hero/
stats-footer composition, entrance animations, and mobile burger-menu
behavior described in the brief. Use the attached reference screenshot to
verify pixel-level fidelity (spacing, avatar-ring treatment, stat layout).
This is ConSight's public landing/sign-in gateway — replace the generic
"Get Started" CTA destination with the real login flow (§4.3), and replace
placeholder trust-brand icons with ones appropriate to ConSight's actual
domain (EPC/infrastructure, not generic SaaS) if the client brands
(Microsoft/AWS/Google) don't fit the product's real positioning — confirm
with the user before swapping brand marks.

### 6.2 Derived design tokens for the application shell

Extract from the landing spec and extend:
```css
--bg-app: #0a0a0b;          /* app shell background, slightly lifted from
                                 pure #000 for data-dense screens */
--surface: #141416;         /* card/panel surface */
--surface-raised: #1c1c1f;
--border: rgba(255,255,255,0.08);
--text: #ffffff;
--text-muted: #8e8e8e;
--accent: #ffffff;          /* the brief uses no color accent — keep that
                                 restraint; status uses semantic color only */
--status-auto-commit: #34d399;   /* confidence >= 0.85 */
--status-review: #fbbf24;        /* 0.60-0.85 */
--status-new-activity: #f87171;  /* < 0.60 */
--font-sans: "Inter", "Segoe UI", system-ui, sans-serif;
--font-display: "BubbledotICG-FinePos", "Geist Pixel Circle", monospace;
```
Use `--font-display` sparingly inside the app — big KPI numbers, section
glyphs echoing the stats-footer treatment — never for dense body/table
text, which stays Inter for legibility. Confidence-score badges, routing
status pills, and audit-trail entries should visually echo the landing
page's pill/badge language (soft shadow, radius 999, restrained color)
rather than introducing a new visual language.

### 6.3 Interaction & motion discipline
One orchestrated entrance per screen (not a fade-up on every card), real
loading skeletons (not spinners on blank screens) while data streams in
from async matching/Celery jobs, and motion that responds to user action
(expanding a match's score breakdown, confirming a planner decision) —
consistent with the restraint already specified for the landing page.
Respect `prefers-reduced-motion` everywhere, not just on the landing page.

### 6.4 Required application screens (each fully wired, no dead states)
- Auth: login, and role-aware post-login redirect.
- Planner Exception Dashboard (PRD §6.4/§8.2 `schedule/queue`): the
  PENDING_REVIEW / NEW_ACTIVITY_CANDIDATE queue with one-click
  approve/correct/reject/promote, top-3 candidates, score breakdown.
- Time-Agent (chat + voice, §5.7/§5.11).
- Inbound Channels (WhatsApp live feed, §5.2).
- Schedule view (WBS tree/table, import/export, §5.1) with delay-ripple
  panel (§5.4).
- Insights / Institutional Memory (§5.5) and RAG knowledge-base search
  (§5.9/P13).
- Predicted Risk watchlist (§5.6/P10).
- BIM/Digital Twin viewer (§5.9/P15).
- Admin: users/orgs/RBAC, project switcher (§5.9/P16), audit log browser,
  threshold tuning (`auto_commit_threshold`/`min_candidate_threshold`
  per PRD §6.4).
- Supervisor mobile/PWA capture flow (§5.10).

---

## 7. Per-iteration verification checklist

Before flipping any `STATE.json` item to `done: true`:
- [ ] `alembic upgrade head` runs clean on a fresh Postgres.
- [ ] `pytest` passes (backend), including any new benchmark/accuracy
      tests introduced for that phase.
- [ ] `npm run build && npm run lint` passes (frontend), if the phase
      touched frontend.
- [ ] The three-case core demo (§0, "never break the core demo" rule) still
      works end to end.
- [ ] `scripts/generate_synthetic_data.py` still runs cleanly and the new
      feature has *something* to show against synthetic data.
- [ ] No TODO/FIXME/"not implemented"/mock response left in a code path
      reachable from the UI.
- [ ] No secret, API key, or credential appears in any staged file —
      confirm `.gitignore` coverage (§0 rule 6) and spot-check the diff
      before committing.
- [ ] `pip-audit`/`npm audit` run clean (or new findings are flagged in
      `STATE.json` notes) if a dependency file changed this iteration.
- [ ] Design-system conformance (§6) for any screen touched.
- [ ] `docs/TRACEABILITY.md` updated with the new row.
- [ ] `CHANGELOG.md` updated; commit made with a message referencing the
      phase id and PRD/add-on section.

---

## 8. Definition of Done (final iteration only)

- [ ] Every item in `STATE.json` is `done: true`.
- [ ] All PRD §3 success metrics are at least instrumented/observable
      (even if real production values need live traffic to mature) —
      p99 ingest latency, auto-commit %, matching precision, review-queue
      clear time, zero-drop rate.
- [ ] Postgres + pgvector + Redis + Celery + JWT/RBAC confirmed as the
      only production data/auth path; SQLite confirmed backup-only with a
      tested restore procedure.
- [ ] Full docker-compose (and ideally k8s manifests) bring the entire
      stack up from a clean checkout with one command, seeded via the
      synthetic data generator.
- [ ] Every screen in §6.4 is reachable, populated, and free of dead
      buttons or placeholder copy.
- [ ] Fresh `git log` shows a clean, phase-by-phase history a reviewer
      could read as a build narrative.
- [ ] A full-repo secret scan (e.g. `gitleaks detect` or equivalent) comes
      back clean across the entire git history, not just the latest diff.
- [ ] `pip-audit` and `npm audit` come back clean (or documented) across
      the whole dependency tree, not just files touched in the final
      iteration.
- [ ] Set `STATE.json.status = "COMPLETE"`.
