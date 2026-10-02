# Submission notes

Draft for the form; final numbers re-checked at the 3:00 PM freeze.

## What it is

A Case Brief dashboard that digests the live Clio matter "Sapini" for (1) the
PI firm team and (2) treating medical providers. One screen answers where the
case stands in 90 seconds; every fact links to the note, email or scanned page
it came from, with the quote highlighted.

## Tech stack

- **Built with:** Python 3.13 + FastAPI, React + Vite + TypeScript + Tailwind v4,
  react-pdf; PyMuPDF and Windows OCR (RapidOCR fallback) for PDFs and scans.
- **Running on:** localhost (Windows). `README.md` has the run commands.
- **Data outside Clio:** local SQLite (`backend/data/app.db`): synced sources,
  pages with line boxes, chunks, embeddings, cached digests, share settings and
  view log, LLM usage. Clio is read-only: one GET-only client; the only POST is
  the OAuth token refresh.

## AI models and cost per case

| Step | Model |
|---|---|
| Retrieval questions per chunk (HyDE), recent-activity headlines, milestone flags | Claude Haiku 4.5 |
| Fact extraction (8 categories, verbatim quotes), grounded drafts | Claude Sonnet 5.5 |
| Headline brief, cited Q&A | Claude Opus 5.5 |
| Embeddings | OpenAI text-embedding-3-large |
| Rerank | Cohere rerank-v3.5 |

- **First full digest of Sapini:** about $1.50 (most of it one-time indexing).
- **Refresh after Clio changes:** about $0.07–0.25 (only changed sources re-processed).
- **Per AI draft:** about $0.01–0.02. Per cited Q&A answer: about $0.02.
- **Total spend today including all development runs:** about $5.

## Notes for judges

- **Where to look first:** `backend/app/digest/` (extraction, verbatim span
  verification, rule-based KPIs, draft verifier), `backend/app/share/`
  (server-side provider filtering), `frontend/src/source/` (PDF highlight).
- **Differentiator:** every number and date on screen is traceable. Facts are
  accepted only if their quote is found verbatim in the source; unverified
  items are visibly marked. AI drafts are checked token by token (dates,
  amounts, names, claim numbers) against cited sources, regenerated once, and
  anything still unverified becomes a visible `[verify: …]`.
- **Deterministic where it matters:** specials, firm costs, actions and
  "waiting on" come straight from Clio's structured data; the case value is a
  configurable firm rule (default 1.5x–3x billed specials), not a model guess.
- **Provider privacy:** filtering happens on the server; strategy, notes and
  unshared documents never reach the provider endpoint.
- **Not built / limits:** real-time sync (on-demand today; Clio webhooks in
  production, not built because creating a subscription writes to Clio);
  outbound notifications to providers; Windows-only OCR; search results
  highlight the whole passage, not the exact sentence.
- **Nothing about the case is hardcoded.** The only Sapini reference in code is
  the default matter name to look up (`MATTER_QUERY`, env-overridable).
