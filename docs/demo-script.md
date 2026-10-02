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
| 0:00–0:08 | Firm Case Brief loads | "A PI file is thousands of pages. Clio captures it; nobody digests it. This is Sapini, live from Clio." |
| 0:08–0:22 | Header, timeline strip, KPI row | "In ten seconds: litigation stage, the milestones that matter, what the case is worth and the coverage behind it. $118,400 in specials across nine providers, the value range with the firm's rule shown." |
| 0:22–0:38 | Click an injury chip → PDF opens, quote highlighted | "Every fact is a link. Click the injury and the scanned medical record opens at the exact line. Nothing on this screen is unsourced; anything we can't verify verbatim is marked." |
| 0:38–0:50 | Next steps → overdue item → Draft → Improve with AI | "What's overdue and who we're waiting on. One click drafts the follow-up; the AI version cites every fact and can't put a date or dollar in an email that the record doesn't contain." |
| 0:50–0:58 | Find in case: type a question, click a cited [n] | "Drill down on demand: search and cited answers over the whole file." |
| 0:58–1:15 | Share with provider → pick the chiropractor → toggle coverage → copy link | "Providers treating on a lien want two things: is the case alive, and is there coverage. The attorney picks exactly what this provider sees: no strategy, no notes." |
| 1:15–1:27 | Provider page: case active, coverage, what the firm needs, visits and bills, updates since | "The doctor sees status, coverage, what the firm needs from their office, and their own visits and bills, without the file and without an email." |
| 1:27–1:30 | Back to brief | "Ninety seconds to the whole case, every fact traceable. About $1.50 per case to digest." |

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
