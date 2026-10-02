# Demo video script (90 seconds)

Sapini, read live from Clio (read-only) and digested once into our own cache.
Firm view at `http://localhost:5175/`; provider view from the share panel's link.

**Before recording:** restart backend `:8000` and frontend `:5175` from the main
checkout on latest `main`; `GET /api/health` shows the current `pipeline_rev`;
run `POST /api/matters/1811191943/digest` once so every click is served from
cache; browser at 1440x900, zoom 100%, no other tabs; open one chip and one
draft once beforehand so PDFs and drafts are warm.

**Warm the chat:** ask the exact demo questions once before recording (cold answers take 20–28 s; cached repeats take about 1 s). Example: "When is the Pullano deposition?" and "What's overdue and who are we waiting on?".

**Accuracy gate (blocker):** after the final re-digest, run
`cd backend; uv run python -m app.audit --checks 1,2,3,5,6` (about $0.75, 3–4 min).
Any critical finding blocks recording until fixed or the item is cut from the video.

| Time | On screen | Say |
|---|---|---|
| 0:00–0:07 | Sign-in page (Red Duck Lawyer) → Cases | "A PI file is thousands of pages. Clio captures it; nobody digests it." |
| 0:07–0:17 | Cases page: Sapini on top with "2 overdue · 6 waiting · deadline in 19 days", specials, coverage, draft value | "Every matter, sorted by what needs you first, with what it's worth and the coverage behind it. Sapini is live from Clio; the greyed rows are labeled samples." |
| 0:17–0:30 | Open Sapini → lane timeline; hover a milestone, zoom once | "The timeline lawyers asked for: medical, legal and deadlines at a glance. Scheduled things say scheduled, not done." |
| 0:30–0:42 | Click an injury or timeline chip → scanned PDF with the quote highlighted | "Every fact is a link. Click it and the record opens at the exact line. Anything we can't verify verbatim is marked." |
| 0:42–0:54 | Next steps: overdue McCulloch item → Draft → Improve with AI | "What's overdue and who we're waiting on. The AI follow-up cites every fact and can't invent a date or a dollar." |
| 0:54–1:07 | Ask the case: "When is the Pullano deposition?" → answer with chips → click "Show on timeline" | "Ask anything. Answers come only from the record, with sources, and they take you to the right place on the page." |
| 1:07–1:20 | Share with provider → chiropractor → toggle coverage → open the provider link | "Providers on a lien see status, coverage, what we need from them, and their own bills. No strategy, no notes; the attorney decides." |
| 1:20–1:30 | Back to Cases | "Ninety seconds to the whole case, every fact traceable, about $1.50 per case to digest." |

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
