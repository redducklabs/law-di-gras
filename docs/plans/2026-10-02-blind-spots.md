# Plan: Blind spots (agentic whole-case review), stream S7

Goal: an agent reviews the entire Sapini file the way a senior partner does a
file review and surfaces what item-by-item dashboards miss: conflicts, gaps,
stale threads, risks, inconsistencies, opportunities. Each finding is cited and
verified. This is the "above other dashboards" feature.

Contract (on main, 95bf41c): `ReviewFinding`, `CaseReview` in `schemas.py` /
`types.ts`.

## Design

- **Agent loop** (Claude API manual tool loop, `claude-opus-5-5`, effort high,
  thinking adaptive; capped at about 25 tool calls and about $1.50 per run). Tools,
  all read-only over our SQLite:
  - `get_brief()`: the cached Dashboard (facts, actions, timeline, KPIs,
    providers, conflicts) as compact JSON with fact/source ids.
  - `search_record(query, k)`: existing hybrid search (`retrieval.search`).
  - `read_source(source_id, page?)`: text of a note, email, task or document page.
  - `list_sources(kind?, since?)`: titles and dates, to spot gaps and staleness.
  - `submit_finding(...)`: records a finding with quotes. It may be called many times.
- **Prompt:** review checklist for a PI file: liability evidence and witnesses
  (who was never contacted), coverage and limits (conflicts, exhaustion,
  excess), liens, treatment gaps or stalls, specials reconciliation, records
  still outstanding, client contact cadence, deadlines and scheduled events
  with no record, inconsistent accounts, defense experts vs treating
  findings, damages the file supports but the demand doesn't use. Case text is
  fenced as data (catalog A8). **No legal citations from memory**: statutes,
  rules or cases only if quoted from the record.
- **Verification:** each finding's quotes must span-match (`spans.locate`). Then
  the claim verifier (`digest.verify`: token check plus Sonnet judge) runs on
  title, why_it_matters and suggested_next_step against the finding's own
  quotes. Failures are regenerated once, then dropped. Optional: the whole-record
  conflict check (`digest.conflicts`) on each finding.
- **Absence claims** ("nobody contacted Pullano", "no police report in the
  file") are allowed only when the agent searched for it and cites what it
  searched plus the closest evidence; phrase it "No record found of …".
- **Cache** by the dashboard input hash; `GET /api/matters/{id}/review` (cached),
  `POST /api/matters/{id}/review?force=` (runs the agent, about 1–3 min). Log
  cost to llm_usage (purpose `review`).
- **UI:** a "Blind spots" card on the brief (section id `review`) under Next
  steps: severity-sorted findings with a category badge, why it matters, the
  suggested next step and source chips. Deeplinks via the existing
  onOpenSource. A Cases-page attention reason "N blind spots (high)".

## Session prompt

```
You own stream S7 (Blind spots: an agentic whole-case review) of the Sapini dashboard. You are in your own git worktree. Read CLAUDE.md, docs/plans/2026-10-02-blind-spots.md (your plan), docs/submission.md ("How we keep it honest"), docs/challenge.md (Decisions) and docs/status.md first. Load the claude-api skill before writing Claude API code (note: Opus 5.5 rejects forced tool_choice, so use tool_choice auto, strict tools, and steer from the prompt).
Owned paths: backend/app/review/ (new), backend/app/api/review.py (new; expose `router`, which I will mount in main.py, or add one line to the module tuple in main.py yourself), frontend/src/review/ (new: a `BlindSpots({review, onOpenSource})` card). Import, never edit: app.retrieval.search, app.digest.spans, app.digest.verify, app.digest.conflicts, app.llm, app.db, schemas. Do not touch digest/, share/, clio/, other frontend folders. Clio stays read-only; this feature never calls Clio. NEVER call POST /digest. Firm sign-in is ON: test over HTTP by signing in (POST /api/auth/login with creds read from the main .env, never printed) or call your code in-process. Use your own backend on port 8007 (full restart after every pull).
Goal: find what an attorney misses looking item by item (conflicts, gaps such as an uncontacted key witness, stale threads, coverage/lien/deadline risk, inconsistent accounts, unused leverage), each with a verified citation, a plain-language why-it-matters and a concrete next step. No legal citations from model memory. Absence claims only as "No record found of …" after an actual search.
Freeze is 3:00 PM PT. Land the backend first (GET/POST review + a cached Sapini run), then the card. Push small commits (git pull --rebase origin main; git push origin HEAD:main; stage only your paths). Report to the manager session (title "Swans AI Hackathon brainstorm", id local_f51cb4b6-ab8e-4b29-b8de-9b0dc100e1c4) with the findings list, cost and run time; the manager wires the card into the brief and gets S6 to audit it.
Done when: a cached Sapini review returns 5–10 verified findings that a PI attorney would find genuinely useful, and the card renders them with working source chips.
```
