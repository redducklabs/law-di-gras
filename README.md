# Law-di-gras

The Swan law-di-gras hackathon project by Red Duck Labs. A fast, working
prototype: a dashboard that digests a live Clio Manage personal-injury
matter (Sapini) for the firm's team and the treating medical providers.
Deadline 4:00 PM PT, 2026-10-02.

- Agent rules: [`CLAUDE.md`](CLAUDE.md) (Claude Code) and [`AGENTS.md`](AGENTS.md) (Codex)
- Reusable patterns from sibling projects: [`docs/reuse-catalog.md`](docs/reuse-catalog.md)
- Challenge brief and decisions: [`docs/challenge.md`](docs/challenge.md)
- Organizer deck: `docs/slides/`

## Running it

Windows / PowerShell. `.env` at the repo root (see `.env.example`).

```powershell
cd backend; uv sync; uv run uvicorn app.main:app --reload --port 8000
cd frontend; npm install; $env:PORT=5175; $env:API_PORT=8000; npm run dev
```

**Sign in (local demo):** the firm pages (`/cases`, `/matters/:id`) need a sign-in.
The demo username and password are `APP_LOGIN_USER` and `APP_LOGIN_PASSWORD` in the
main checkout's `.env` (leave `APP_LOGIN_USER` empty to turn sign-in off locally).
Provider share links (`/p/:token`) never need a sign-in.

Parallel build sessions run in git worktrees with their own ports; see
`docs/plans/2026-10-02-case-brief-dashboard.md` ("Worktrees, ports, syncing").

## Accuracy first

Every number, date and claim on screen traces to a verbatim quote in the Clio
record, and the app flags conflicts in the record instead of guessing. How:
[`docs/submission.md`](docs/submission.md#how-we-keep-it-honest-anti-hallucination).
Independent audit, re-runnable with `cd backend; uv run python -m app.audit`:
[`docs/audit/2026-10-02-data-audit.md`](docs/audit/2026-10-02-data-audit.md).
