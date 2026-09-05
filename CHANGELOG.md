# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **P0-landing-page**: Public landing page per §6.1 specification
  - Full-bleed looping video background with gradient overlay
  - BubbledotICG-FinePos display font for headlines and stat glyphs
  - Inter font for UI text
  - Header with logo, pill navigation, mobile burger menu
  - Hero section with badge, headline, subheadline, dual CTAs
  - Trust row with EPC/infrastructure brands (Bechtel, Fluor, AECOM, Jacobs, Kiewit, Vinci)
  - Stats footer with 4 KPIs (auto-commit accuracy, queue clearance, disciplines, uptime)
  - Platform highlights section (Field capture, Schedule intelligence, Institutional memory)
  - Integrations strip with native connectors
  - Footer with product/company/legal links and social icons
  - Entrance animations (fade-in, slide-up) with reduced-motion support
  - CTA buttons wired to real `/login` route
  - Design-system conformant per §6.2 tokens and components

### Changed
- **Routing**: Root path `/` now serves landing page; app shell moved to `/app/*` prefix
- **Auth flow**: Landing page "Get Started" and "Sign in" CTAs navigate to `/login`

### Fixed
- TypeScript build passes with strict mode
- ESLint configuration added (.eslintrc.cjs)

## [0.3.0] - 2026-09-05

### Added
- **P6-whatsapp**: WhatsApp Business Cloud API integration per PRD §5.2 and add-on Phase 6
  - Webhook endpoint `/webhooks/whatsapp/inbound` with Meta signature verification (X-Hub-Signature-256 HMAC-SHA256)
  - GET verification endpoint for Meta webhook subscription
  - POST handler for inbound text messages
  - Feeds same extraction → matching → confidence pipeline as `/progress/extract` (no forked pipeline)
  - Persists messages as `field_events` with `source_type='WHATSAPP'` and `ingestion_source_id` linked to WHATSAPP source
  - Sends confirmation/status reply back to supervisor via WhatsApp Cloud API
  - Configuration via environment variables: WHATSAPP_APP_ID, WHATSAPP_APP_SECRET, WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN, WHATSAPP_WEBHOOK_SECRET
  - Frontend: Inbound Channels panel (`/inbound`) with live feed from `/progress/inbound/recent`
  - Source status grid showing all 7 ingestion sources (WhatsApp, Time Agent, Voice, Spreadsheet, PDF/OCR, PMIS Export, Text Diary)
  - Auto-refresh every 10 seconds with real-time message feed
  - Message status badges (Auto-matched/Needs review/Processing/New activity/Rejected) with activity code links
  - Time-ago formatting and live connection indicator

## [0.2.0] - 2026-09-05

### Added
- **P5-p6-roundtrip**: Primavera P6 / MS Project round-trip per PRD §8.2 and add-on Phase 5
  - XER import with xerparser: activities, WBS hierarchy, predecessor/successor (FS/SS/FF/SF + lag)
  - MPP import with mpxj: activities, relationships, lag support
  - Upsert by activity_code (no duplicates on re-import)
  - Write-back of actual_start/actual_finish on planner approval via /schedule/matches/{match_id}/resolve
  - Review approve/correct endpoints also write actuals to schedule_activities
  - Export XER with current actuals from schedule_activities (not just reviews)
  - Alembic migration adding actual_start/actual_finish to schedule_activities
  - Frontend: Schedule Import screen with file upload, parse preview with diff (New/Updated/Unchanged badges), commit
  - Frontend: Export XER action with schedule selector dropdown
  - Frontend: Schedule view with actual start/finish columns, status badges

## [0.1.0] - 2026-09-05

### Added
- **P0-frontend-shell**: React+Vite+TS application shell
  - Routing with react-router-dom v6
  - Auth context with JWT HttpOnly cookie flow
  - 8 application screens (Dashboard, Schedule, Planner Queue, Time Agent, Inbound, Insights, Risk, BIM, Admin, Settings)
  - Responsive sidebar with role-based navigation
  - Top bar with project switcher, notifications, user menu
  - Protected routes with role checks

- **P0-design-system**: Complete design system per §6.2
  - CSS custom properties (colors, spacing, radii, shadows, transitions, animations)
  - Tailwind config with all design tokens
  - Font families: Inter (UI), BubbledotICG-FinePos (display)
  - Reusable components: Button, Badge, Card, Input/Textarea, Select, DataTable, Skeleton, EmptyState
  - Status color system (auto-commit, review, new-activity)
  - Reduced motion support

- **P0-synthetic-data**: Realistic synthetic dataset generator
  - 2-3 organizations with 5 roles each
  - L1-L6 WBS tree (274 nodes) with predecessor/successor relationships
  - 181 field events across 7 ingestion sources (VOICE, TIME_AGENT, TEXT_DIARY, SPREADSHEET, PDF_OCR, PMIS_EXPORT, WHATSAPP)
  - Realistic confidence distribution (auto-commit/review/new-activity buckets)
  - 15 delay reasons across 8 categories
  - 10 productivity benchmarks, 10 glossary mappings
  - Idempotent, parameterized (--project, --weeks, --seed)

- **P0-auth-rbac**: JWT authentication with RBAC
  - Access + rotated refresh tokens in HttpOnly cookies
  - CSRF double-submit token on state-changing requests
  - 5 roles: SYSTEM_ADMIN, CONTRACTOR_ADMIN, PROJECT_CONTROLS, DISCIPLINE_PLANNER, SITE_SUPERVISOR
  - Organization/project scoping on all data queries
  - CORS allowlist, audit logging on auth events
  - Seed script for demo users

- **P0-sqlite-backup**: Celery Beat hourly SQLite backup
  - Dumps core tables to timestamped SQLite files
  - Retention policy (keep last 24)
  - Restore procedure documented

- **P0-infra-redis-celery**: Redis + Celery infrastructure
  - Redis as broker and result backend
  - Celery worker, beat, backup task
  - Configured in docker-compose.yml

- **P0-infra-postgres**: PostgreSQL 16 + pgvector
  - docker-compose.yml with Postgres 16 + pgvector extension
  - Alembic initial migration with all PRD §9 tables
  - Database.py supports both SQLite (dev) and PostgreSQL (prod)

- **P0-audit**: Baseline repository audit and STATE.json initialization