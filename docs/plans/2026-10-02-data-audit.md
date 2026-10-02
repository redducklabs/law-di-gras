# Plan: data audit stream (S6)

Goal: find data errors and anything that reads as a hallucination before the
judges do. The audit reports findings; the owning stream fixes them (S2 digest,
S4 ingest/sharing), routed through the manager session.

## Known so far

- Timeline showed a scheduled deposition (subpoena "commands" EBT on Dec 8, 2025)
  as an event that happened; the brief says it is outstanding. Sent to S2.
- Document header date is Clio's filing date (Jan 2, 2025), not the document's own
  date (Nov 2, 2025); confusing next to the cited passage.

## Checks (in priority order)

1. **Fact support (highest risk).** For every fact, bullet, timeline event,
   KPI, action and recent item in the cached Dashboard: does the cited quote
   actually support the stated value, date, amount and tense? Code checks first
   (dates and amounts in the value appear in the quote; quote span-matches the
   source), then a findings-only judge (Sonnet 5.5 via `llm.structured`) asking
   "supported / partially / contradicted / tense wrong (scheduled shown as
   occurred) / wrong party". Never rewrite, only report.
2. **Headline.** Each Opus bullet's claims trace to the facts it references.
3. **KPI reconciliation.** Specials = sum of medical-charge entries per provider;
   firm costs = the remaining entries; coverage values match their quotes; case
   value matches the configured rule.
4. **Ingestion.** Source counts vs Clio (GET-only counts); text equals Clio
   fields (entities unescaped); every PDF page has text; OCR quality on the 10
   scanned pages (compare to a Claude vision transcription of each page, report
   word error); duplicate documents; dates parsed correctly (doc date vs Clio
   created date).
5. **Timeline semantics.** Duplicate events, future vs past, scheduled vs occurred,
   wrong kind.
6. **Provider views.** For each of the 10 providers, the token view contains no
   notes, emails, strategy text or another provider's data.

## Session prompt

```
You own stream S6 (data audit) of the Sapini dashboard. You are in your own git worktree. Read CLAUDE.md, docs/plans/2026-10-02-data-audit.md (your plan), docs/challenge.md (Decisions) and docs/status.md first.
Goal: find every data error, unsupported claim, or hallucination-looking item in what the app shows for Sapini, starting with fact support, before the judges do. You REPORT; you do not fix pipeline code.
Owned paths: backend/app/audit/ (new; a re-runnable `uv run python -m app.audit` that writes a report) and docs/audit/ (findings). Do not edit digest/, retrieval/, share/, clio/, ingest/ or frontend/. Read the shared SQLite DB and the running API (GET only; use your own backend on port 8006, restart it fully after every pull). NEVER call POST /digest or POST /sync. Clio is read-only (GET only, via backend/app/clio/client.py). LLM calls go through app.llm.structured and log cost; keep the whole audit under ~$3.
Output docs/audit/2026-10-02-data-audit.md: a table per check with severity (critical = wrong number/date/party/tense on screen; major = unsupported or misleading; minor = cosmetic), the on-screen text, the cited quote, what's wrong, and the owning stream (S2 digest / S4 ingest+sharing / S3 UI). Push early and often (git pull --rebase origin main; git push origin HEAD:main; stage only your paths). After each check, message the manager session (title "Swans AI Hackathon brainstorm", id local_f51cb4b6-ab8e-4b29-b8de-9b0dc100e1c4) with the critical and major findings so they can be dispatched; don't message other streams directly.
Done when every check in the plan has run on the current cached dashboard and the report is pushed. Then re-run once after the streams' fixes land and confirm they're resolved.
```
