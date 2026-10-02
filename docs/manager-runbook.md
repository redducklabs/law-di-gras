# Manager runbook (integration/manager session)

The manager session ("Swans AI Hackathon brainstorm", id
`local_f51cb4b6-ab8e-4b29-b8de-9b0dc100e1c4`, main checkout `C:\Repos\law-di-gras`)
coordinates every stream, owns integration (`frontend/src/App.tsx`,
`backend/app/main.py`, docs), and keeps Aron informed. Streams message this id;
after `/clear` it is unchanged. Live state: `docs/status.md`. Plans: `docs/plans/`.

## Deadline and schedule (PT, 2026-10-02)

- **2:43** freeze warning to all streams; **3:00** feature freeze; **3:00–3:30** record
  locally; **~3:45** submit (submission order = presentation order); **4:00** hard close.
- The previous manager's cron check-ins were session-scoped and **are gone**. Recreate
  them (see "Check-in loop").

## Streams (all in `.claude/worktrees/*`, each on its own branch, landing on main)

| Stream | Session id | Owns | Port | State at handoff (12:30) |
|---|---|---|---|---|
| S1 Clio + ingestion | archived | (now S4) | n/a | done |
| S2 retrieval + digest + chat | `local_4ffd991b-ee95-4e9d-859a-6858575ea7b2` | `backend/app/{retrieval,digest}/`, `api/digest.py` | 8002 | working the queue below |
| S3 UI design | `local_86d8e431-053d-40e3-b28b-9e76d8dfab5a` | `frontend/src/{styles,components,firm,cases}/`, provider restyle | 5173 | holding for freeze |
| S4 provider/sharing + auth + cases API + Clio/ingest | `local_ae7ee234-f027-4239-8a52-8ca04fc78b46` | `backend/app/{share,auth,cases,clio,ingest}/`, `api/{share,auth,cases,sources}.py`, `frontend/src/{provider,auth}/` | 8004 / 5174 | standby |
| S5 source pane + chat panel | `local_bf74fa6b-165c-4c81-8bd1-ee65e21f0b70` | `frontend/src/{source,chat}/` | 8005 / 5176 | standby (PDF blank-page fix landed 7dabb24) |
| S6 data audit | `local_8b6cd5c2-f9ab-4afd-9f80-b1bf8226840e` | `backend/app/audit/`, `docs/audit/` | 8006 | waits for pings to re-run (~$0.70/run; Aron OK'd spend) |
| S7 Blind spots review | `local_9355b4e5-925a-40c0-a2b0-a142f2c87eba` | `backend/app/review/`, `api/review.py`, `frontend/src/review/` | 8007 | just started (plan `docs/plans/2026-10-02-blind-spots.md`) |
| Deploy | `local_0cc4a245-b3a7-44e3-b25f-b46126893ef8` | `deploy/`, `.github/workflows/demo-*`, `backend/app/clio/web.py` | n/a | demo.redducklaw.com live on app sign-in; **DB empty, awaiting Aron's yes to upload snapshot** |

## Open work at handoff

- **S2 queue (in order):** (1) chat CRITICAL: injury/defense question answered "evidence
  does not contain any IME findings" (retrieval miss): feed Dashboard facts by topic,
  forbid unsupported absence claims, fix "2023-07-26 arthroscopy on the calendar",
  align chat coverage wording with the r16 conflict tile; (2) N1 drop the CSB
  "defendant" coverage line (reads as a second $100k/$300k policy); (3) N2 keep KPI
  labels short, move attributed note text out of labels; (4) N3 "Defense radiology
  review (Dr. Katzman)", not IME; (5) leftovers: bullet 0 cite notes 2996972633 /
  2996970518, status_citations add note 2996972258, knee card left-knee scope,
  bullet 4 fragment, "Surgery: New Horizon (one day)", SOL cite complaint, IME date
  conflict, Hudson Valley date, dedupe chat citations. Then a re-digest → ping S6.
- **S7:** when it reports, mount `<BlindSpots>` in the brief (App.tsx passes the review
  via `api` / or S3 places it under Next steps), have S6 audit the findings, and decide
  by ~2:30 whether it's in the video.
- **Aron decisions pending:** upload DB snapshot to demo.redducklaw.com (recommend yes).
- **Freeze tasks:** see "Freeze checklist".

## Operating rules learned today (enforce these)

- **Restart servers fully after every pull.** `uvicorn --reload` misses pulls on Windows;
  Vite serves stale modules (`npm run dev -- --force`). A stale backend once re-cached
  wrong KPIs; S2 added a pipeline-revision guard (`GET /api/health` → `pipeline_rev`).
- **Only S2 (or the manager) calls `POST /digest`.** Other streams read the cache.
- **Firm sign-in is ON** (`APP_LOGIN_USER/PASSWORD/SESSION_SECRET` in the main `.env`, set
  by Aron). `/api/*` needs the session cookie, except `/api/auth/*`, `/api/health`,
  `/api/share/*`. For curl tests, sign in with creds read from `.env` (never print),
  or call code in-process.
- **Clio is read-only.** The only POSTs are OAuth token exchange/refresh. The deploy
  server has its own Clio grant; never copy the laptop's tokens there.
- **Every visible claim must trace to a verbatim quote**; conflicts are shown, not
  resolved. Route audit findings to the owning stream; don't let streams fix each
  other's code.
- **Contracts** (`schemas.py` ↔ `types.ts`) change only by small `contract:` commits.
- Background servers in this session: backend `:8000`
  (`cd backend; uv run uvicorn app.main:app --port 8000`), frontend `:5175`
  (`cd frontend; $env:PORT=5175; $env:API_PORT=8000; npm run dev -- --force`). Check with
  `curl http://127.0.0.1:8000/api/health` and `http://localhost:5175/login`; restart if
  down. Background tasks have a 2 h limit.

## Check-in loop (recreate with CronCreate)

Every 15 minutes (`7,22,37,52 12-15 2 10 *`): git fetch; list new commits on main and each
worktree's unpushed or uncommitted work; skim each stream's recent transcript
(`list_events`, about 30) for off-plan work, hardcoded case content, non-GET Clio calls,
ownership violations, `git add -A`, stalls, or waiting on Aron; send corrective messages;
restart `:8000`/`:5175` if main moved; update `docs/status.md`; reply to Aron with 3–6 lines.
One-shots: **2:43** freeze warning to all streams; **3:03** freeze (verify main end to end,
grep for hardcoded Sapini content, audit gate, finalize demo script and submission,
tell Aron to record).

## Freeze checklist (3:00)

1. All streams stop; nothing uncommitted in any worktree; main builds (`npx tsc -b`,
   backend imports).
2. Restart `:8000` and `:5175` from the main checkout; `GET /api/health` shows the latest
   `pipeline_rev`.
3. S2 or the manager re-digests once (signed in); S6 runs the audit gate
   (`uv run python -m app.audit --checks 1,2,3,5,6`). Any critical blocks recording or is
   cut from the video.
4. Warm the demo chat questions and one source chip; browser at 1440x900.
5. Grep for hardcoded case content (`grep -rni sapini backend/app frontend/src`; only
   the `MATTER_QUERY` default and comments are allowed; sample rows are labeled).
6. Finalize `docs/demo-script.md` and `docs/submission.md` (cost per case is about $2.50
   first digest; open audit items listed). Aron records and submits.
