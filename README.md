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

Parallel build sessions run in git worktrees with their own ports; see
`docs/plans/2026-10-02-case-brief-dashboard.md` ("Worktrees, ports, syncing").
