# ConSight — P0-P12 Stabilization Pass (run once, then stop)

**What this is:** a *single bounded pass*, not another open-ended loop. Run
this once, after `STATE.json` shows every item from `P0-audit` through
`P12-ocr-scanned-diaries` as `done: true`. Its only job is to independently
re-verify that everything claimed done in that range is *actually*
functional, secure, and professionally finished — and to fix anything that
isn't — then stop, leaving the repo in a state the user can confidently
review and push themselves.

**Scope is strictly P0 through P12. Nothing else.** Bugs, security issues,
or workflow problems in anything P13 or later are explicitly **out of
scope for this pass** — including frontend gaps for P13+ features (missing
screens, unstyled placeholders, incomplete wiring for BIM/RAG/weather/ML-
prediction/voice-beyond-P11/multi-project work, etc.). Do not fix, polish,
or even flag those unless they actively break something that's supposed to
work within P0-P12 (for example: if a P13+ route crashes the whole app on
load, or a shared component you'd need to touch for a P0-P12 fix also
happens to serve a P13+ screen — fix only the shared piece, and only to the
extent P0-P12 needs it). The bar for anything outside P0-P12 is simply "can
the P0-P12 demo still run without it getting in the way" — nothing more.

This companion prompt assumes `CONSIGHT_BUILD_LOOP_PROMPT.md` is present at
repo root and references its §4/§5 phase specs directly — read that file for
what each phase was supposed to deliver. This prompt does not redefine any
feature; it only defines the verification-and-fix pass.

---

## 0. Hard rules for this pass — no exceptions

1. **Never run `git push`, under any circumstance, for any reason, no
   matter how clean the result looks.** Not automatically, not if asked to
   within this session, not "just to be safe," not even to a new branch.
   The decision to push is reserved for the human, full stop. Your job
   ends at a clean local commit history and a clear report — the human
   takes it from there.
2. **Do not start any `P13`-or-later work.** If you notice something that
   would clearly belong to a later phase (e.g. "this would be better with
   RAG" or "BIM support would help here"), do not build it — note it in
   the report (§4) as an observation and move on. Scope creep here defeats
   the entire purpose of doing a bounded stabilization pass before
   continuing the main loop.
3. **Don't trust any existing `done: true` flag, commit message, or prior
   `STATE.json` note at face value.** This repo has already had branches
   and commit messages that overstated what was actually implemented —
   treat every claim from `P0-audit` through `P12-ocr-scanned-diaries` as
   an unverified hypothesis until you've personally read the code and run
   a real check that proves it.
4. **Fix root causes, not symptoms.** If a test is failing because the
   underlying feature is broken, fix the feature — don't loosen the test,
   remove an assertion, or comment out a failing check to get to green.
   If you find yourself about to weaken a test to pass it, that's the
   signal to look harder at the code instead.
5. **Every fix is its own focused commit**, exactly like the main loop —
   never batch unrelated fixes into one commit, and never squash the
   stabilization pass into a single giant commit at the end. The commit
   history should read as clearly as the original build history did.
6. **Stop when the pass is done, not when you run out of things to
   improve.** There is always something that could be polished further —
   that's not the bar. The bar is: everything claimed for P0-P12 is real,
   working, tested, and secure per the original spec. Once that's true,
   write the report (§4) and stop.

---

## 1. Verification sweep — do this for every phase P0 through P12

For each of the following, read the actual implementation (not the
commit message) against its spec in `CONSIGHT_BUILD_LOOP_PROMPT.md`, then
run a real check that proves or disproves it:

- **P0-audit / P0-infra-postgres / P0-infra-redis-celery** — bring the
  full stack up from a clean state (`docker compose down -v && docker
  compose up -d`), confirm Postgres has the `vector` extension enabled,
  Redis and Celery workers are actually running and processing jobs (not
  just present in `docker-compose.yml`), and `alembic upgrade head` runs
  clean on a *fresh* database, not just an already-migrated one.
- **P0-auth-rbac** — actually exercise it: log in as each of the five
  roles from PRD §5, confirm JWT is delivered via `HttpOnly`/`Secure`/
  `SameSite=Strict` cookies (check response headers directly, don't just
  read the code and assume), confirm a state-changing request without a
  valid CSRF token is rejected, and confirm a Contractor Admin token
  genuinely cannot read another organization's data by hitting the
  endpoint directly with `curl`, not just checking that the UI hides it.
- **P0-sqlite-backup** — trigger the backup job manually, confirm a
  restorable `.db` file is actually produced, and test the documented
  restore procedure once, end to end, rather than trusting that it reads
  correctly.
- **P0-synthetic-data** — re-run the generator from a clean database and
  confirm it's idempotent and actually produces the volume/realism
  described in §4.4 (multiple orgs, full WBS tree, weeks of events,
  delays, corrections) — not just that it runs without erroring.
- **P0-design-system / P0-frontend-shell / P0-landing-page** — build the
  frontend (`npm run build && npm run lint`), then actually load the
  landing page and compare it against the reference screenshot and spec
  in §6.1 of the loop prompt (fonts, video background, header/hero/stats
  composition, mobile menu behavior) — visually, not just "the code looks
  like it matches the spec."
- **P5-p6-roundtrip** — import a real `.xer` file and, separately, an
  `.mpp` file if that support exists; confirm predecessor/successor
  relationships actually land in the database (query them directly), and
  confirm that approving a match in the Planner queue actually writes the
  updated actual date back and that the export path produces a file the
  round-trip claim depends on. If `.mpp` support doesn't exist despite
  being claimed, that's a bug to fix, not a note to defer.
- **P6-whatsapp** — send a real (or realistically simulated) WhatsApp
  webhook payload and confirm it flows through the *same* extraction/
  matching pipeline as `/api/v1/events/ingest`, not a parallel code path.
- **P7-multilingual** — run the full 25-30 message code-mixed benchmark
  suite and confirm it passes the accuracy threshold the phase spec set,
  not just that the benchmark file exists.
- **P8-delay-ripple** — log a delay event against real predecessor/
  successor data from the P6 import and confirm the downstream impact and
  critical-path flag are computed correctly, not hardcoded or
  approximated.
- **P9-institutional-memory** — confirm the analytics endpoints return
  real aggregates computed from the synthetic dataset, not placeholder
  numbers, and that the Insights screen renders real charts from them.
- **P10-ml-delay-prediction** — confirm a model was actually trained (not
  a stubbed constant-output function), that evaluation metrics were
  logged, and that the UI's "Predicted Risk" indicator reflects the
  model's actual output with a visible confidence value.
- **P11-voice-agent** — submit a real short audio clip and confirm actual
  speech-to-text transcription occurs and reaches the same extraction
  pipeline, in more than one supported language if that was claimed.
- **P12-ocr-scanned-diaries** — submit a real scanned/photographed diary
  image or PDF and confirm OCR text actually reaches the extraction
  pipeline with `source_type = 'PDF_OCR'`, and that low-confidence OCR
  correctly routes to review rather than being silently accepted.

For anything in this list you cannot personally verify with a real
check (e.g. no test WhatsApp number available), say so explicitly in the
report (§4) rather than marking it verified on the strength of reading
the code alone.

---

## 2. Cross-cutting checks (apply once, across everything in P0-P12)

- [ ] Full backend test suite passes: `pytest`.
- [ ] Frontend build and lint pass: `npm run build && npm run lint`.
- [ ] The three-case core demo (clean auto-match, ambiguous match with
      planner correction, unmatched → new-activity) works end to end,
      exactly as it did after Phase 1-4.
- [ ] No screen reachable from the nav renders a dead button, a "coming
      soon" state, or a hardcoded/mocked response outside an explicit,
      documented `LLM_PROVIDER=mock` developer flag.
- [ ] `.gitignore` genuinely covers everything sensitive (`.env`,
      `*.pem`/`*.key`, `backups/*.db`, build artifacts) — confirm by
      checking `git status` after a fresh local run touches those paths,
      not just by reading the `.gitignore` file.
- [ ] Full-history secret scan comes back clean: `gitleaks detect
      --source . --log-opts="--all"` (or equivalent). If it finds
      anything in history — even in an old commit — flag it prominently
      in the report; a secret already committed needs rotation, and
      `.gitignore` alone won't remove it from history.
- [ ] `pip-audit` and `npm audit` come back clean, or every remaining
      finding is explicitly listed in the report with its severity and
      why it's acceptable to leave for now.
- [ ] Every new endpoint added across P0-P12 enforces the
      `organization_id`/`discipline`/`project_id` scoping and role checks
      it's supposed to — spot-check at least one endpoint per phase with
      a `curl` request using a token that should be denied.
- [ ] `STATE.json` itself is internally consistent — every item claimed
      `done: true` for P0-P12 is one you've now personally re-verified in
      §1, not one you're leaving on trust.
- [ ] Every screen that belongs to a P0-P12 feature (landing page, auth,
      Planner Exception Dashboard, Schedule/P6 import-export, Inbound
      Channels/WhatsApp, Time-Agent voice+multilingual, delay-ripple
      panel, Insights/analytics, OCR upload flow) looks and behaves like
      finished, professional software per §6 of the loop prompt's design
      system — consistent spacing, typography, loading/empty/error
      states, no unstyled default form elements, no visual regressions
      introduced by later phases' shared-component changes. This check is
      scoped only to P0-P12 screens; a P13+ screen looking unfinished is
      not a finding for this pass (see scope note above).

---

## 3. Fixing what you find

For every gap, bug, or security issue uncovered in §1 or §2:
1. Fix it completely against the original phase's spec in
   `CONSIGHT_BUILD_LOOP_PROMPT.md` §4/§5 — not a minimal patch that makes
   the specific check pass while leaving the underlying issue.
2. Add or correct a test that would catch a regression of this specific
   issue in the future.
3. Commit it on its own, with a message naming the phase it belongs to
   and what was actually wrong — e.g. `"Fix P5: MS Project .mpp import
   was stubbed, now parses via mpxj and maps predecessor/successor data"`.
4. Re-run the specific check from §1/§2 that caught it, to confirm the
   fix actually works, before moving to the next issue.

Work through issues in the same order as §1 (P0 → P12) so the commit
history stays readable as "verify P0, fix what's broken in P0, verify P5,
fix what's broken in P5, ..." rather than jumping around.

---

## 4. Final report — write this, then stop

When §1-§3 are complete, write `docs/STABILIZATION_REPORT_P0-P12.md`
covering:
- A per-phase table (P0 through P12): what was checked, what was found
  (working as specified / found broken and fixed / could not verify and
  why), and any residual risk worth the user's attention before pushing.
- Confirmation that P13+ was left untouched — you didn't fix, polish, or
  expand anything outside P0-P12, and any P13+ issue you happened to
  notice is only mentioned if it currently gets in the way of the P0-P12
  demo, with a one-line note on how (nothing more).
- Every security finding from §2, whether fixed or (if genuinely
  unfixable in this pass) explicitly flagged as needing the user's
  decision.
- A final, one-paragraph honest verdict: is this in a state you'd
  recommend pushing and continuing the main loop from, or is there
  something you'd want the user to look at first.
- The line: **"Not pushed to GitHub — awaiting manual review and push by
  the user."**

Then update `STATE.json`: add a top-level field
`"p0_p12_stabilization_pass": { "completed_at": "<timestamp>",
"report": "docs/STABILIZATION_REPORT_P0-P12.md" }`. Leave the backlog
items' `done` flags as `true` (now genuinely re-verified rather than
merely claimed) and leave `P13` onward untouched — the user will resume
those one at a time from here, as before.

Commit the report and the `STATE.json` update, and stop. Do not continue
into `P13`. Do not push.
