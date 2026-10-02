# Demo video script (90 seconds)

Sapini, read live from Clio (read-only) and digested once into our own cache.
Firm view at `http://localhost:5175/`; provider view from the share panel's link.

**Before recording:** restart backend `:8000` and frontend `:5175` from the main
checkout on latest `main`; `GET /api/health` shows the current `pipeline_rev`;
run `POST /api/matters/1811191943/digest` once so every click is served from
cache; browser at 1440x900, zoom 100%, no other tabs; open one chip and one
draft once beforehand so PDFs and drafts are warm.

**Restart both servers after the last pull:** uvicorn `:8000` (fully, not --reload) and Vite with `npm run dev -- --force`; a stale Vite serves old modules (e.g. "api.chat is not a function").

**Chat questions safe to demo (S6 audited):** Pullano deposition, overdue / waiting on, last client contact, coverage (after conflict B is fixed). Avoid the injuries/defense-IME question until S6 confirms the fix.

**Blind spots (S6 Check 8b, cache frozen; never POST /review before recording):** safe to show as worded: #1 incident report "annexed" vs "not produced" (the demo beat), #7 IME dates, #9 deferring surgery vs "available", #10 prior injuries "Not applicable". In narration never say "only eyewitness", "without any analysis", "neither matches the pleadings", "the lien will have grown" (#2/#4/#6/#8 overstate), "planned motion to compel" or "the only contemporaneous account" (#1), or "were never reported" (#7). S7's verifier (016061d) now catches all of these on any future run.

**Warm the chat:** ask the exact demo questions once before recording (cold answers take 20–28 s; cached repeats take about 1 s). Example: "When is the Pullano deposition?" and "What's overdue and who are we waiting on?".

**Accuracy gate (blocker):** after the final re-digest, run
`cd backend; uv run python -m app.audit --checks 1,2,3,5,6` (about $0.75, 3–4 min).
Any critical finding blocks recording until fixed or the item is cut from the video.

| Time | On screen | Say |
|---|---|---|
| 0:00–0:07 | Sign-in page (Red Duck Lawyer) → Cases | "A PI file is thousands of pages. Clio captures it; nobody digests it." |
| 0:07–0:17 | Cases page: Sapini on top with "2 overdue · 6 waiting · deadline in 19 days", specials, coverage, draft value | "Every matter, sorted by what needs you first, with what it's worth and the coverage behind it. Sapini is live from Clio; the greyed rows are labeled samples." |
| 0:17–0:30 | Open Sapini → lane timeline; hover a milestone, zoom once | "The timeline lawyers asked for: medical, legal and deadlines at a glance. Scheduled things say scheduled, not done." |
| 0:30–0:44 | Click an injury or timeline chip → scanned PDF with the quote highlighted; then point at the coverage "Conflict" line | "Every fact is a link to the exact line. Nothing is stated unless its quote is in the record, and where the file contradicts itself, like Metro-North's limits, we show both sides instead of guessing." |
| 0:44–0:54 | Expand the Blind spots bar → finding #1 (incident report) → click its chip to the annexed report page | "Then the part nobody has time for: an agent reads the whole file for what a page-by-page read misses. Here, the defense says it annexed Metro-North's incident report, while our own email says it was never produced. Every point is checked against quoted record." |
| 0:54–1:00 | Next steps: overdue item → Draft (skip Improve if short on time) | "What's overdue, and a cited follow-up drafted in one click." |
| 1:00–1:10 | Ask the case: "When is the Pullano deposition?" → answer with chips → click "Show on timeline" | "Ask anything. Answers come only from the record, with sources, and they take you to the right place on the page." |
| 1:10–1:22 | Share with provider → chiropractor → toggle coverage → open the provider link | "Providers on a lien see status, coverage, what we need from them, and their own bills. No strategy, no notes; the attorney decides." |
| 1:22–1:30 | Back to Cases | "Ninety seconds to the whole case, every fact traceable, about $2.50 per case to digest." |

## Pitch notes (say these; not built)

- **Sync today:** on demand (`POST /api/matters/{id}/sync`). Incremental: about 24
  read-only Clio GETs, unchanged items skipped by content hash; only changed
  sources are re-chunked, re-embedded and re-digested (about $0.15–0.20 per
  refresh vs about $1.50 first digest).
- **Production: real time via Clio webhooks.** Subscribe to record-change
  events (notes, communications, tasks, calendar, documents, activities), then
  re-ingest just that item and re-digest just the affected facts in seconds.
  The same events drive "the case moved" updates to providers. Not built here,
  because creating a webhook subscription is a write to Clio and our build is
  strictly read-only.
