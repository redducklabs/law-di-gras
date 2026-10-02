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
- **Running on:** localhost (Windows) and hosted at demo.redducklaw.com (Linux, RapidOCR). `README.md` has the run commands.
- **Data outside Clio:** local SQLite (`backend/data/app.db`): synced sources,
  pages with line boxes, chunks, embeddings, cached digests, share settings and
  view log, LLM usage. Clio is read-only: one GET-only client; the only POST is
  the OAuth token refresh.

## AI models and cost per case

| Step | Model |
|---|---|
| Retrieval questions per chunk (HyDE), recent-activity headlines, milestone flags | Claude Haiku 4.5 |
| Fact extraction (8 categories, verbatim quotes), grounded drafts, claim and whole-record conflict judges | Claude Sonnet 5.5 |
| Headline brief, Ask-the-case chat | Claude Opus 5.5 |
| Embeddings | OpenAI text-embedding-3-large |
| Rerank | Cohere rerank-v3.5 |

- **First full digest of Sapini:** about $2.50 (≈$1.20 one-time indexing: Haiku retrieval questions + embeddings; ≈$0.80 extraction and reranking; ≈$0.50 brief plus verification and whole-record conflict checks).
- **Refresh after Clio changes:** about $0.55–0.75 with all verification passes (only changed sources re-indexed).
- **Per AI draft:** about $0.01–0.02. Per cited chat answer: about $0.12–0.14 (Opus + verification); repeats are cached.
- **Total spend today including all development and audit runs:** about $12.

## How we keep it honest (anti-hallucination)

Built in one day, so these layers are prototype-grade, but every one runs on
Sapini today and is in the repo.

1. **Faithful ingestion.** Clio is read through a GET-only client. Note and email
   text is stored exactly (HTML entities unescaped). PDFs keep per-line
   positions, scans are OCR'd with line boxes, and source counts and texts were
   reconciled against Clio.
2. **Deterministic where the data is structured.** Specials, firm costs, next
   steps, "waiting on" and the case-value range are computed in code from
   Clio's own entries, not by a model. The case-value rule is a visible,
   configurable firm setting (default 1.5x–3x billed specials).
3. **Every fact carries a verbatim quote.** Extraction is schema-enforced. A
   fact is "verified" only if its quote is found in the source text, which
   gives the exact page and line to highlight. Anything else is shown and
   visibly marked unverified, never silently dropped or promoted.
4. **Claim verifier on all generated text.** The brief, status line, recent
   activity, drafts and chat answers go through two checks: code checks that
   every date, amount, name and claim number appears in the cited quotes, and
   a Claude judge checks each claim against only its cited evidence. The text
   is regenerated once with the failures listed; whatever still fails is
   stripped, or in drafts becomes a visible `[verify: …]`.
5. **Whole-record conflict check.** Each headline, coverage, lien, injury and
   specials claim is also checked against the rest of the file. Where the
   record disagrees with itself, the app shows "Conflict: X vs Y" with both
   sources instead of picking a side. Example: Metro-North "self-insured" vs
   the claims administrator's $100k/$300k email.
6. **Tense and status.** Dated items are labeled occurred, scheduled, adjourned
   or deadline from their own wording. A subpoenaed deposition with no record
   of happening reads "Scheduled … (no record it occurred)".
7. **Constrained chat.** Answers cite only retrieved or brief evidence, every
   citation is span-verified, and deeplinks are validated server-side against
   real sections, sources, timeline dates and providers.
8. **Independent audit stream.** `cd backend; uv run python -m app.audit` re-runs
   six checks:
   - fact support
   - claim vs whole record
   - KPI reconciliation
   - ingestion fidelity
   - timeline semantics
   - provider-view leaks

   It found real issues that we then fixed, among them a rounded case value,
   claims beyond their quotes, defense IME opinions listed as the client's
   injuries, and a scheduled deposition shown as held. Findings and each fix
   round are in `docs/audit/2026-10-02-data-audit.md`. It ran as a release
   gate before we recorded.
9. **Blind spots (agentic whole-case review) is verified the same way.** An
   Opus agent reads the whole file for conflicts, gaps, stale threads and
   leverage. Every finding's quotes are span-matched and judged, and it must
   pass four extra checks:
   - Words like "only" or "never" must appear in the quotes, and an upcoming
     event needs a cited calendar entry, task or quote.
   - A claimed conflict is re-read against the full text of the documents it
     cites, and rejected if those documents reconcile it.
   - Each fact is checked against the whole record: supporting passages are
     attached as extra citations, and a contradiction rejects the finding.
   - Statute or rule cites must appear on a cited page.

   The audit stream checked every finding (Check 8b); open wording items are
   listed there.
10. **Provider privacy by construction.** Provider views are filtered on the
   server. The audit confirms that none of the 10 provider links exposes notes,
   strategy or another provider's data.

**Honest limits:** model judges are probabilistic; OCR on low-quality scans is
imperfect (photo-ID page); open audit items at submission time are listed in the
audit report.

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
  outbound notifications to providers; OCR is Windows OCR locally, RapidOCR (slower) on Linux; search results
  highlight the whole passage, not the exact sentence.
- **Nothing about the case is hardcoded.** The only Sapini reference in code is
  the default matter name to look up (`MATTER_QUERY`, env-overridable).

## Hosted demo

- **URL:** https://demo.redducklaw.com (TLS). Firm screens need sign-in;
  credentials go to judges directly from Aron (submission form), never in git.
- **Provider links** (`/p/...`) open without signing in, as a provider would
  use them.
- **Live from Clio:** the server holds its own read-only Clio grant (in-app
  Connect Clio at `/api/clio`) and pulled and digested Sapini itself: 31
  documents, 361 pages, about 10 minutes and $1.86 on a 1-vCPU Droplet. Scanned
  pages OCR with RapidOCR on Linux.
- **Stack:** one DigitalOcean Droplet, Docker Compose (FastAPI + Caddy),
  deployed by GitHub Actions on every push to `main`. Runbook: `deploy/README.md`.
