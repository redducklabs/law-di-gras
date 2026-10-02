```json agent-handoff-metadata
{
  "active_scopes": [
    {
      "highest_authorized": true,
      "parent_scope_id": null,
      "remaining_code": true,
      "remaining_code_detail": "S2 chat/KPI-label audit fixes in backend/app/digest/, S7 Blind spots in backend/app/review/ and frontend/src/review/ plus its brief mount; then freeze, audit gate, recording and submission.",
      "remaining_work": true,
      "scope_definition": {
        "outcome": "Firm and provider dashboard digesting the live Clio Sapini matter demoable in a 90 second video",
        "title": "Sapini case brief dashboard"
      },
      "scope_definition_digest": "343f23ca39aecdfe507f9e93a623b809224d5e824f1aeed28cddf189621b6a15",
      "scope_id": "sapini-dashboard",
      "scope_kind": "epic",
      "status": "in-progress"
    }
  ],
  "authorization_evidence": {
    "evidence_hmac": "c4476ddae646b2f83cb4993ebe6bdd26d23bc136f2c648eb84bc39a75c257f82",
    "kind": "initial-user-turn",
    "proposal_turn_ref": null,
    "user_turn_ref": "turn-e6946a41f8af3c61e8ed018176b18759"
  },
  "authorization_id": "auth-a6ae1f0a9ce17625b94675f1a4694582",
  "authorized_root_scope_id": "sapini-dashboard",
  "exact_action": {
    "action": "Recreate the manager check-in loop and freeze one-shots with CronCreate exactly as in docs/manager-runbook.md, then run the first check-in",
    "completion_condition": "CronList shows the 15-minute check-in plus 2:43 and 3:03 one-shots, and Aron has received a 3-6 line status reply",
    "constraints": "Follow docs/manager-runbook.md operating rules; Clio read-only; no hardcoded case content; restart :8000/:5175 after pulls; route fixes to owning streams",
    "target": "Manager session local_f51cb4b6-ab8e-4b29-b8de-9b0dc100e1c4 in C:\\Repos\\law-di-gras (main checkout)"
  },
  "next_session_gates": [],
  "next_session_prompt": "- Read docs/manager-runbook.md and docs/status.md first; streams message this same session id.\n- Pending Aron decision: upload the DB snapshot to demo.redducklaw.com (recommend yes).\n- When S2 re-digests, ping S6 (local_8b6cd5c2-f9ab-4afd-9f80-b1bf8226840e) for the audit re-run.\n- When S7 reports, mount BlindSpots in the brief and get S6 to audit it; cut from the video if not solid by 2:30.",
  "predecessor": null,
  "record_id": "sapini-manager-handoff-1",
  "record_type": "continuation",
  "schema_version": 2,
  "timestamp": "2026-10-02T12:28:00-07:00",
  "transition": null,
  "verification": [
    {
      "check": "curl http://127.0.0.1:8000/api/health returns ok with the latest pipeline_rev",
      "evidence": "12:20 PT: ok, pipeline_rev 16 after restart on main",
      "result": "pass"
    },
    {
      "check": "cd frontend; npx tsc -b",
      "evidence": "Clean after the routes/chat wiring on main (b53f8c0, e53a059)",
      "result": "pass"
    },
    {
      "check": "Audit gate: cd backend; uv run python -m app.audit --checks 1,2,3,5,6 (S6 runs it)",
      "evidence": "r16 run 903ac6f: no contradicted on-screen claims; KPIs reconcile; providers clean; majors N1-N3 open with S2",
      "result": "pass"
    },
    {
      "check": "Demo path clicked live at :5175 (cases, brief, source chip PDF highlight, chat deeplink, share)",
      "evidence": "Verified 12:00-12:15 PT on Sapini; PDF blank-page fix 7dabb24 verified by S5",
      "result": "pass"
    }
  ]
}
```

# Session continuation

## Objective

Ship the Sapini case brief dashboard (firm brief, Cases landing, provider sharing, Ask-the-case chat, Blind spots review) and the 90-second video plus submission by 4:00 PM PT 2026-10-02, with every on-screen claim traceable to a verbatim Clio quote. This session manages streams S2-S7 and the deploy stream and owns integration.

## Authoritative references

CLAUDE.md; docs/manager-runbook.md (streams, session ids, ports, rules, freeze checklist); docs/status.md; docs/challenge.md Decisions; docs/plans/2026-10-02-case-brief-dashboard.md, -data-audit.md, -blind-spots.md, -deploy-demo.md; docs/demo-script.md; docs/submission.md; docs/audit/2026-10-02-data-audit.md.

## User decisions

Stack FastAPI + SQLite + React/Vite; models Haiku 4.5 ingest, Sonnet 5.5 extract/judges, Opus 5.5 brief/chat/review; embeddings OpenAI, rerank Cohere. Cases landing page with labeled sample rows; branded app sign-in (creds in main .env); docked chat with deeplinks; templated drafts plus Improve-with-AI; timeline zoom on; case value is a configurable firm rule; hosted demo on demo.redducklaw.com via Droplet; record the video locally; anti-hallucination is the headline differentiator; S6 audit spend approved.

## Repository state

12:28 PT: main checkout C:\Repos\law-di-gras on main at f2c96a9, clean, in sync with origin/main. Stream worktrees under .claude/worktrees/*. Local servers: backend :8000 and Vite :5175 run as background tasks of this session (2 h limit).

## Completed work

Contracts and skeleton; Clio sync (219 sources, OCR); digest pipeline r16 with claim verifier and whole-record conflict check; KPI fixes; Cases page, sign-in, re-layout, chat panel and routes wired in App.tsx; source pane with PDF font fix; provider sharing; grounded drafts; S6 audits through r16; demo script, submission notes with anti-hallucination section, README accuracy pointer; manager runbook.

## Incomplete work and risks

S2 chat critical (false 'no IME findings') still open: keep the injury question out of the video until S6 confirms. Background servers and cron jobs die with the process; recheck :8000/:5175 health. Stale servers can serve old code; restart after pulls. Freeze is 3:00; first-digest cost is about $2.50, not $1.50.

## External effects

Pushed to origin main (github.com/redducklabs/law-di-gras). demo.redducklaw.com is live via GitHub Actions deploy and a DigitalOcean Droplet with a DNS A record (by the deploy stream). Clio was only read.
