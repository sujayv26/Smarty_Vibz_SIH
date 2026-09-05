# Problem-to-Solution Traceability Matrix

Per PRD §18 and CONSIGHT_BUILD_LOOP_PROMPT §5, this matrix maps each implemented phase to PRD requirements and add-on document phases.

| Phase ID | PRD Section | Add-on Phase | Description | Status |
|----------|-------------|--------------|-------------|--------|
| P0-audit | — | — | Repo audit, baseline STATE.json | ✅ Done |
| P0-infra-postgres | §9 (schema), §10 (security) | — | PostgreSQL 16 + pgvector, Alembic migrations, all PRD §9 tables | ✅ Done |
| P0-infra-redis-celery | §8.5 (async workers) | — | Redis + Celery (worker, beat) in docker-compose | ✅ Done |
| P0-auth-rbac | §10.4 (auth/RBAC), §5 (personas) | — | JWT + rotated refresh tokens, HttpOnly cookies, CSRF, 5 roles, org/project scoping | ✅ Done |
| P0-sqlite-backup | §4.2 (backup) | — | Celery Beat hourly SQLite dump with retention | ✅ Done |
| P0-synthetic-data | §4.4 (synthetic data) | — | generate_synthetic_data.py: multi-org, L1-L6 WBS, 7 ingestion sources, confidence distribution, delays, benchmarks | ✅ Done |
| P0-design-system | §6.2 (tokens), §6.3 (motion) | — | CSS tokens, Tailwind config, reusable components, animations, reduced motion | ✅ Done |
| P0-frontend-shell | §6.4 (screens), §6.1 (landing) | — | React+Vite+TS, routing, auth context, 8 screens, sidebar, role-based access | ✅ Done |
| P0-landing-page | §6.1 (landing page) | — | Video background, BubbledotICG-FinePos/Inter, header/pill-nav/trust-row/hero/stats-footer, animations, mobile menu, CTA → /login, EPC trust brands | ✅ Done |
| P5-p6-roundtrip | §8.2 (schedule upload), §9 (wbs_nodes) | Phase 5 | XER/MSP import/export, predecessor/successor, write-back on approval | ✅ Done |
| P6-whatsapp | §8.3 (WhatsApp), §9 (ingestion_sources) | Phase 6 | WhatsApp Cloud API webhook, same extraction pipeline, live inbound panel | ⏳ Pending |
| P7-multilingual | §6.1 (extraction), §5.7 (code-mixed) | Phase 7 | Hindi-English, Tamil-English, Telugu-English extraction, benchmark set | ⏳ Pending |
| P8-delay-ripple | §6.5 (delay ripple), §9 (schedule_relationships) | Phase 8 | Deterministic graph traversal, critical-path flagging, persisted results | ⏳ Pending |
| P9-institutional-memory | §6.6 (analytics), §8.4 (endpoints) | Phase 9 | Discipline productivity, delay patterns, benchmarks, Insights dashboard | ⏳ Pending |
| P10-ml-delay-prediction | §6.7 (ML), §8.4 (predictions) | Phase 10 | Trained delay prediction model, Celery retraining, watchlist UI | ⏳ Pending |
| P11-voice-agent | §6.2 (Time-Agent), §8.3 (chat) | Phase 11 | Whisper STT, press-to-talk, same extraction JSON, audit persistence | ⏳ Pending |
| P12-ocr-scanned-diaries | §6.1 (extraction), §9 (PDF_OCR source) | Phase 12 | Tesseract/cloud OCR, review queue for low confidence, verification UI | ⏳ Pending |
| P13-advanced-rag | §6.6 (knowledge base), §8.4 (query) | Phase 13 | pgvector RAG over delay_reasons/benchmarks/glossary, cited sources | ⏳ Pending |
| P14-weather-context | §6.5 (delay context), §10 (external) | Phase 14 | Weather API ingestion, geolocated per project, feeds ripple + ML | ⏳ Pending |
| P15-bim-digital-twin | §6.8 (BIM), §9 (IFC) | Phase 15 | IFC ingestion, WBS mapping, three.js viewer, progress color-coding | ⏳ Pending |
| P16-multi-project-enterprise | §5 (personas), §10.4 (RBAC) | Phase 16 | Multi-tenancy, project switcher, project-level RBAC, PMO rollup | ⏳ Pending |
| P17-offline-mobile-pwa | §17 (risk register), §6.4 (supervisor) | Phase 17 | Installable PWA, offline queue, background sync, idempotent event_id | ⏳ Pending |
| P18-frontend-consistency-pass | §6 (all) | — | Cross-screen design-system audit, no placeholder states | ⏳ Pending |
| P21-hardening-observability | §10 (security), §18 (metrics) | — | p99 latency, auto-commit %, precision, review time, zero-drop | ⏳ Pending |
| P22-e2e-verification | §3 (success metrics), §8 (DoD) | — | Full stack docker-compose, synthetic seed, secret scan, audit clean | ⏳ Pending |

---

**Legend:** ✅ Done | ⏳ Pending | 🔄 In Progress

**Last updated:** 2026-09-05