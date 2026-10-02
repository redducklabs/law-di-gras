# Built-in audit + background progress (Aron, 13:25)

Goal: every new digest or Blind spots run is audited automatically, flagged items
are marked on screen (never silently shown as fact), and long runs show a progress
bar instead of a frozen skeleton. Hard cutoff 2:40 PT; anything not solid is reverted.

## Contract (committed first)

- `RunProgress {status, stage, pct, started_at, finished_at, error}`
- `CaseReview.run?: RunProgress` (set while a new review runs; findings = last completed)
- `AuditFlag {target, item_id, section, severity, check, note, citations}`
- `AuditReport {matter_id, target, target_hash, run, items_checked, flags, cost_usd}`

## Routes

- S7: `POST /api/matters/{id}/review` starts a background run, returns `CaseReview` with
  `run` (202-style, immediate). `GET /review` returns the last completed review + `run`.
  Never two runs at once. The agent reports stage/pct as it goes.
- S6: `GET /api/matters/{id}/audit?target=dashboard|review` returns `AuditReport`. If no
  report exists for the current payload hash, it starts the audit in the background
  and returns `run.status = queued|running`. One audit per hash, cached in `digests`.
  Dashboard target = the existing checks (fact support, whole record, KPI reconcile,
  timeline semantics, provider leaks). Review target = Check 8 in code (span match,
  overreach/absolutes, same-source conflict, whole-record contradiction, legal cites).

## Streams

| Stream | Owns | Work |
|---|---|---|
| S6 | `backend/app/audit/`, new `backend/app/api/audit.py` | audit route + background runner + review check in code |
| S7 | `backend/app/review/`, `api/review.py`, `frontend/src/review/` | background run + progress; BlindSpots shows progress bar, "Unaudited" until audit done, flags inline |
| S3 (redesign) | `frontend/src/{components,firm}/` | `<ProgressBar>` component; brief header audit badge ("Audited · N flags" / progress); flag markers on facts/sections |
| Manager | `main.py`, `App.tsx`, docs | mount audit router; verify; demo script |

## Demo rules

- The audited local caches (r26 dashboard, 10-finding review) stay; do not start a new review locally before recording.
- The video can show the audit badge and one flagged item if they are solid by 2:40.
