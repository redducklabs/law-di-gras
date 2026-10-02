# Plan: Case Brief dashboard (Sapini)

Decisions: `docs/challenge.md` → Decisions. Deadline 4:00 PM PT; feature freeze
~3:00 PM for the video.

## Demo path (the 90-second video)

- [ ] Open the firm dashboard for Sapini; client name and photo/initials, timeline strip at top
- [ ] Headline status + stage, KPI tiles (specials, coverage/policy limits, firm spend)
- [ ] Needs action: overdue / upcoming / waiting on others; last client contact
- [ ] Click a date or injury chip → source pane opens the scan/note with the span highlighted
- [ ] "Find in case" search → cited passages (and cited Q&A if built)
- [ ] Share panel: pick a provider, toggle sections, preview, copy link
- [ ] Open the provider link: status, coverage, what the firm needs, their bills/visits
- [ ] (Nice) Firm sees "opened by provider at …"

## Worktrees, ports, syncing (every stream session)

- Streams S1–S4 each run in **their own git worktree** (start the session in a
  new worktree from the desktop app). Integration stays in the main checkout.
- Land work on `main` from your worktree branch:
  `git pull --rebase origin main` then `git push origin HEAD:main`. Do this
  after every small commit so other streams see it. Never `git add -A`; add your
  owned paths only.
- `.env` and the SQLite DB are **shared from the main checkout** automatically
  (`backend/app/config.py` resolves it via `git rev-parse --git-common-dir`).
  Do not copy `.env` into a worktree. All streams see S1's synced data at once.
- First run in a worktree: `cd backend; uv sync` and/or `cd frontend; npm install`
  (`frontend/.npmrc` pins `os=win32`; the global npm config says linux).
- Ports, so dev servers never collide:

  | Session | Backend (`uvicorn --port`) | Frontend (`$env:PORT`, `$env:API_PORT`) |
  |---|---|---|
  | Integration (main checkout) | 8000 | 5175 → 8000 |
  | S1 | 8001 | n/a |
  | S2 | 8002 | n/a |
  | S3 | n/a (fixture), later 8000 | 5173 → 8000 |
  | S4 | 8004 | 5174 → 8004 |

  Backend: `cd backend; uv run uvicorn app.main:app --reload --port 8001`.
  Frontend: `cd frontend; $env:PORT=5173; $env:API_PORT=8000; npm run dev`.

## Shared contracts (committed to `main` before streams start)

Integration session commits these files; streams build against them and change
them only by a small commit announced in the commit message (`contract:`).

**Layout**

```
backend/                      uv project, Python 3.13, FastAPI on 127.0.0.1:8000
  pyproject.toml              [contracts] deps for all streams
  app/main.py                 [integration] app + router mounts + CORS
  app/config.py               [contracts] .env loading (python-dotenv)
  app/db.py                   [contracts] SQLite schema + connect(); data/app.db
  app/schemas.py              [contracts] Pydantic API shapes below
  app/llm.py                  [contracts] Anthropic client, model ids, structured() helper, cost logging
  app/clio/                   [S1] client.py (GET-only), login.py (OAuth), sync.py
  app/ingest/                 [S1] pdf.py (PyMuPDF words / RapidOCR lines), chunk.py
  app/api/sources.py          [S1] /api/matters, /sync, /api/sources/*
  app/retrieval/              [S2] embed.py (OpenAI), hyde.py (Haiku), search.py (FTS5+vec RRF, Cohere rerank)
  app/digest/                 [S2] extract.py (Sonnet), brief.py (Opus), spans.py (verbatim + rects), dashboard.py
  app/api/digest.py           [S2] /digest, /dashboard, /search, /ask
  app/share/ + app/api/share.py  [S4] share settings, provider view builder, view log
frontend/                     Vite + React + TS + Tailwind on :5173, proxy /api → :8000
  src/api/types.ts            [contracts] TS mirror of schemas.py
  src/api/client.ts           [contracts] fetch wrappers
  src/App.tsx, routes         [integration] / → firm, /p/:token → provider
  src/styles/theme.css        [S3] design tokens via Tailwind v4 @theme (no tailwind.config)
  src/firm/                   [S3] dashboard page, cards, timeline strip, KPI tiles
  src/components/             [S3] SourceChip, Card, Badge, Tile, Drawer (S4 imports, never edits)
  src/dev/fixture.ts          [S3] fictional "Doe v. Example" data for design; deleted by 3 PM
  src/source/                 [integration] SourcePane: react-pdf + highlight overlay, note/email viewer
  src/provider/               [S4] provider page + share panel (functional); S3 does the visual pass after
```

**SQLite tables** (`backend/app/db.py`, one file, `CREATE TABLE IF NOT EXISTS`)

- `matters(id, display_number, description, client_name, client_photo_url, status, opened_date, raw_json, synced_at)`
- `sources(id, matter_id, kind, title, date, author, text, content_hash, file_path, page_count, raw_json, synced_at)` with
  `id = "<kind>:<clio_id>"`, `kind ∈ note|communication|task|calendar_entry|expense|document|custom_field|contact|matter`
- `pages(source_id, page_no, width, height, text, ocr, lines_json)`, where `lines_json = [{text, char_start, char_end, x0,y0,x1,y1}]`, normalized 0–1, top-left origin, `char_*` offsets into `pages.text`
- `chunks(id, source_id, page_no, char_start, char_end, text, content_hash)` + `chunks_fts` (FTS5)
- `vectors(id, chunk_id, kind[body|hyde], text, embedding BLOB float32)`
- `facts(id, matter_id, category, label, value, amount, date, source_id, page_no, quote, char_start, char_end, rects_json, verified, model, input_hash, created_at)`
- `digests(matter_id, kind, input_hash, payload_json, model, created_at)`; `kind='dashboard'` caches the whole Dashboard
- `share_settings(matter_id, contact_id, sections_json, source_ids_json, token, updated_at)`, `share_views(token, viewed_at, user_agent)`
- `llm_usage(id, matter_id, model, purpose, input_tokens, output_tokens, cost_usd, created_at)`

**API** (all ours; only S1's Clio client talks to Clio, GET only)

| Route | Owner | Returns |
|---|---|---|
| `GET /api/matters` | S1 | `MatterSummary[]` |
| `POST /api/matters/{id}/sync` | S1 | `{sources, pages, chunks}` counts (reads Clio, writes our DB) |
| `GET /api/sources/{source_id}` | S1 | `SourceDetail` |
| `GET /api/sources/{source_id}/file` | S1 | PDF bytes |
| `POST /api/matters/{id}/digest?force=false` | S2 | `Dashboard` (cached unless changed) |
| `GET /api/matters/{id}/dashboard` | S2 | `Dashboard` from cache (404 if none) |
| `GET /api/matters/{id}/search?q=` | S2 | `Passage[]` |
| `POST /api/matters/{id}/ask` `{question}` | S2 | `Answer` |
| `GET /api/matters/{id}/providers` | S4 | `Provider[]` (contacts tagged medical) |
| `GET/PUT /api/matters/{id}/share/{contact_id}` | S4 | `ShareSettings` (PUT also mints `token`) |
| `GET /api/share/{token}` | S4 | `ProviderView` (logs a view) |

**Shapes** (`schemas.py` ↔ `types.ts`)

```
Rect        {page, x0, y0, x1, y1}                        # 0–1, top-left origin
Citation    {source_id, source_kind, source_title, date?, page?, quote,
             char_start?, char_end?, rects: Rect[], verified: bool}
Fact        {id, label, value, amount?, date?, citations: Citation[], verified: bool}
TimelineEvent {date, label, kind: incident|treatment|legal|communication|deadline,
             is_future: bool, citations: Citation[]}
ActionItem  {title, due_date?, owner?, status: overdue|upcoming|waiting, waiting_on?,
             citations: Citation[]}
TreatmentLine {provider, contact_id?, first_visit?, last_visit?, visit_count?,
             billed?: Fact, citations: Citation[]}
Dashboard   {matter: MatterSummary, generated_at, cost_usd, models: string[],
             headline: {status_line, stage, bullets: Fact[]},
             timeline: TimelineEvent[],
             kpis: {specials?: Fact, coverage: Fact[], case_value?: Fact, firm_spent?: Fact},
             actions: ActionItem[], last_client_contact?: Fact,
             injuries: Fact[], treatment: TreatmentLine[], recent: Fact[]}
MatterSummary {id, display_number, title, client_name, client_photo_url?, status, opened_date?}
SourceDetail {id, kind, title, date?, author?, text, page_count?, has_file: bool,
             pages: {page_no, width, height, ocr}[]}
Passage     {citation: Citation, score, snippet}
Answer      {answer_markdown, citations: Citation[]}      # [n] markers index citations
Provider    {contact_id, name, role?}
ShareSettings {contact_id, sections: {status, coverage, treatment, requests,
             timeline, documents}: bool, source_ids: string[], token?, last_viewed_at?}
ProviderView {matter_title, client_name, provider_name, stage, status_line,
             case_active: bool, last_activity_date?, coverage?: Fact[],
             requests?: ActionItem[], treatment?: TreatmentLine[],
             timeline?: TimelineEvent[], documents?: {source_id, title}[]}
```

`llm.py` exposes `MODEL_HAIKU="claude-haiku-4-5"`, `MODEL_SONNET="claude-sonnet-5-5"`,
`MODEL_OPUS="claude-opus-5-5"`, `structured(model, PydanticSchema, system, content, purpose=, matter_id=, effort=)`
(`messages.parse` with a Pydantic `output_format`; Opus/Sonnet 5.5 reject forced
`tool_choice`, so this is the schema-enforced path; retries, logs `llm_usage`),
`log_usage(...)` for OpenAI/Cohere calls, and `matter_cost(matter_id)`.
Every router module exposes `router = APIRouter()`; `main.py` mounts
`app.api.sources`, `app.api.digest`, `app.api.share` when present.

## Streams

Critical path: **S1 → S2 → S3** (S3 starts at once on a fictional fixture). S4 runs alongside. Drop first if late:
cited Q&A → opened-tracking → scan injuries (fall back to page-level chips) →
provider document list.

### S1: Clio read client + ingestion
- [ ] `clio/login.py`: one-time OAuth (local callback on 8765), writes tokens to `.env`
- [ ] `clio/client.py`: GET-only, refuses other verbs, auto-refresh, pagination, `fields=`
- [ ] `sync.py`: matter, contacts, custom fields, notes, communications, tasks, calendar, expenses, documents (download) → `sources`
- [ ] `ingest/pdf.py`: PyMuPDF text + line rects; pages with little text → RapidOCR lines
- [ ] `chunk.py`: ~800-token chunks with page + char offsets, FTS5 index
- [ ] Source routes; `SourceDetail` for every kind

### S2: Retrieval + AI digestion + cache
- [ ] OpenAI `text-embedding-3-large` for chunks; Haiku HyDE questions per chunk (embedded as `hyde`)
- [ ] Hybrid search: FTS5 BM25 + cosine (numpy) → RRF → Cohere `rerank-v3.5` if key
- [ ] Per-field extraction (Sonnet, forced tool) over retrieved evidence: incident, injuries, treatment/bills, coverage/policy limits, liens, expenses, key dates, client contact, status signals
- [ ] Tasks/calendar/expenses mapped deterministically where structured (no LLM needed)
- [ ] `spans.py`: verbatim (normalized) quote match → char offsets → `rects` from `pages.lines_json`; unmatched → `verified=false`
- [ ] Opus headline brief from verified facts only; cache `Dashboard` by input hash
- [ ] `/search`, then `/ask` (Opus, [n] citations only from retrieved passages)

### S3: UI design (interactive with Aron)
A design session that iterates visually with Aron in the browser pane: show,
get feedback, revise. It owns the look of every screen; mechanics live elsewhere.
- [ ] 2–3 visual directions for the Case Brief on the fictional fixture → Aron picks one
- [ ] Design tokens + shared components (SourceChip incl. unverified state, Tile, Card, Badge, Drawer)
- [ ] Firm Case Brief: subtle timeline strip at top; headline; KPI tiles; Needs action; injuries; treatment
- [ ] Loading/empty states; "Draft for attorney review · generated <time> · $<cost>"
- [ ] Swap fixture for live `GET /dashboard` once S2 is up; delete `src/dev/` by 3 PM
- [ ] Visual pass on S4's SharePanel + ProviderPage, and on the SourcePane frame

### S4: Provider view + sharing
- [ ] Providers list from Clio contacts (via S1 tables)
- [ ] Share settings CRUD + token; `ProviderView` built server-side from the cached Dashboard, filtered by settings
- [ ] Attorney share panel (drawer from the firm dashboard header): provider picker, toggles, live preview, copy link
- [ ] Provider page `/p/:token`: plain billing/treatment language, case-active badge, coverage, requests, their visits/bills
- [ ] (Nice) view log + "opened" badge in share panel

### Integration (this session)
- [ ] Commit contracts + scaffold (backend runs, frontend renders a blank shell)
- [ ] `src/source/SourcePane`: react-pdf page + rect overlay + scroll to highlight; text sources with highlighted span; Find-in-case + Ask boxes (S3 styles it)
- [ ] Wire routes in `main.py`, keep demo path green, README run commands
- [ ] `docs/demo-script.md`, record the video with Playwright, submission notes (models + cost per case)

## Stream prompts

Each prompt is self-contained; paste it into a fresh Claude Code session in `C:\Repos\law-di-gras`.

### Common rules (included in each prompt)

> Read CLAUDE.md, docs/challenge.md (Decisions) and docs/plans/2026-10-02-case-brief-dashboard.md first. Hackathon: move fast, no tests, verify by running it. Clio is READ-ONLY: only HTTP GET, through `backend/app/clio/client.py`. Never hardcode case content: everything shown must come from Sapini data read from Clio (no Sapini names, dates, amounts or injuries in code or prompts). Never print or commit `.env` values. Build against the shared contracts (`backend/app/schemas.py`, `db.py`, `llm.py`, `frontend/src/api/types.ts`); change a contract only with a small `contract:` commit. Touch only your owned paths. Work in your own git worktree per "Worktrees, ports, syncing"; land with `git pull --rebase origin main` then `git push origin HEAD:main`. Report what you ran/clicked.

### S1 prompt

```
You own stream S1 (Clio read client + ingestion) of the Sapini dashboard.
Read CLAUDE.md, docs/challenge.md (Decisions) and docs/plans/2026-10-02-case-brief-dashboard.md first. Hackathon: move fast, no tests, verify by running it. Clio is READ-ONLY: only HTTP GET, through backend/app/clio/client.py. Never hardcode case content: everything shown must come from Sapini data read from Clio (no Sapini names, dates, amounts or injuries in code or prompts). Never print or commit .env values. Build against the shared contracts (backend/app/schemas.py, db.py, llm.py, frontend/src/api/types.ts); change a contract only with a small `contract:` commit. Touch only your owned paths. You run in your own git worktree: follow the plan's "Worktrees, ports, syncing" section (use your assigned ports; .env and the SQLite DB are shared from the main checkout, never copy .env). Commit small and often with conventional commits, git add only your owned paths, then git pull --rebase origin main and git push origin HEAD:main. Report what you ran/clicked.
Owned: backend/app/clio/, backend/app/ingest/, backend/app/api/sources.py. Do not touch digest/, retrieval/, share/, frontend/.
Goal: pull everything in the Sapini matter from Clio into our SQLite (backend/data/app.db) in the shapes in db.py, so S2 can digest it and S3 can show sources.
1. clio/login.py: one-time OAuth 2.0 (US: https://app.clio.com/oauth/authorize, /oauth/token), local callback on CLIO_REDIRECT_URI, writes CLIO_ACCESS_TOKEN/REFRESH_TOKEN into .env without echoing them.
2. clio/client.py: only get()/paginate(); raises on any other verb; refreshes on 401; respects rate limits; requests explicit fields=.
3. clio/sync.py: find the Sapini matter; store matter, contacts (with roles/types so S4 can find medical providers), custom field values, notes, communications, tasks, calendar entries, activities/expenses, and documents (download latest version to backend/data/files/). One `sources` row per item, content_hash for change detection, raw_json kept.
4. ingest/pdf.py: PyMuPDF per-page text and line boxes (normalized 0–1, top-left); if a page has under ~50 chars, rasterize and run RapidOCR (rapidocr-onnxruntime) to get lines + boxes; set pages.ocr=1. Build pages.text by joining lines so char offsets map to lines_json.
5. ingest/chunk.py: chunk per page (~800 tokens, overlap), with char offsets; fill chunks + chunks_fts. Non-PDF sources (notes, emails) chunk their text with page_no NULL.
6. api/sources.py: GET /api/matters, POST /api/matters/{id}/sync, GET /api/sources/{id}, GET /api/sources/{id}/file.
Done when: `POST /sync` on Sapini fills every table above, scanned PDFs have OCR text with line boxes, and GET /api/sources/<a document> returns text + pages. Report counts per kind and any Clio endpoints that failed.
```

### S2 prompt

```
You own stream S2 (retrieval + AI digestion + cache) of the Sapini dashboard.
Read CLAUDE.md, docs/challenge.md (Decisions) and docs/plans/2026-10-02-case-brief-dashboard.md first. Hackathon: move fast, no tests, verify by running it. Clio is READ-ONLY: only HTTP GET, through backend/app/clio/client.py. Never hardcode case content: everything shown must come from Sapini data read from Clio (no Sapini names, dates, amounts or injuries in code or prompts). Never print or commit .env values. Build against the shared contracts (backend/app/schemas.py, db.py, llm.py, frontend/src/api/types.ts); change a contract only with a small `contract:` commit. Touch only your owned paths. You run in your own git worktree: follow the plan's "Worktrees, ports, syncing" section (use your assigned ports; .env and the SQLite DB are shared from the main checkout, never copy .env). Commit small and often with conventional commits, git add only your owned paths, then git pull --rebase origin main and git push origin HEAD:main. Report what you ran/clicked.
Owned: backend/app/retrieval/, backend/app/digest/, backend/app/api/digest.py. Do not touch clio/, ingest/, share/, frontend/.
Read docs/reuse-catalog.md and copy/adapt from C:\Repos\aurolegal.ai (read-only): A6 schema-enforced output + validation retry (already wrapped as llm.structured, which uses messages.parse because Opus/Sonnet 5.5 reject forced tool_choice), A7 verbatim span find, A8 fencing of case text as data, HyDE prompt shape from backend/src/services/hyde_service.py.
Goal: turn the S1 tables into a cached `Dashboard` (schemas.py) where every fact carries citations with verbatim quotes and highlight rects.
1. retrieval/embed.py: OpenAI text-embedding-3-large (OPENAI_API_KEY), batch, store in vectors; skip unchanged content_hash.
2. retrieval/hyde.py: Haiku 4.5 generates ~5 questions an attorney/paralegal/provider might ask that each chunk answers; embed as kind=hyde.
3. retrieval/search.py: FTS5 BM25 + cosine over body+hyde vectors → RRF → Cohere rerank-v3.5 if COHERE_API_KEY else RRF order. Returns Passage with Citation.
4. digest/extract.py: per category (incident, injuries, treatment+bills per provider, coverage/policy limits, liens, firm expenses, key dates, client contact, case stage signals) run several retrieval queries, then a Sonnet 5.5 llm.structured call returning items with source chunk ids + verbatim quotes. Structured Clio data (tasks, calendar, expenses, custom fields) map deterministically into actions/timeline/firm_spent with citations to their source rows.
5. digest/spans.py: normalize whitespace/quotes, find quote in pages.text (exact then rapidfuzz partial_ratio_alignment ≥ 90), map char range → rects from lines_json. Not found → verified=false (shown, marked).
6. digest/brief.py: Opus 5.5 writes headline {status_line, stage, bullets} using ONLY verified facts, bullets reference fact ids. Case value: draft range only if grounded in specials/limits; else omit.
7. dashboard.py + api/digest.py: assemble Dashboard; cache in digests by hash of all source content_hashes; POST /digest (force flag), GET /dashboard, GET /search, then POST /ask (Opus, answer cites only retrieved passages as [n]).
Done when: POST /digest on Sapini returns a full Dashboard, a second call returns from cache in <1s, ≥80% of facts verified with rects, and llm_usage gives cost per case. Report the cost and model split.
```

### S3 prompt (interactive design session)

```
You own stream S3 (UI design) of the Sapini dashboard. This is an interactive session: Aron iterates on the visuals with you.
Read CLAUDE.md, docs/challenge.md (Decisions) and docs/plans/2026-10-02-case-brief-dashboard.md first. Hackathon: move fast, no tests, verify by running it. Clio is READ-ONLY: only HTTP GET, through backend/app/clio/client.py. Never hardcode case content: everything shown must come from Sapini data read from Clio (no Sapini names, dates, amounts or injuries in code or prompts). Never print or commit .env values. Build against the shared contracts (backend/app/schemas.py, db.py, llm.py, frontend/src/api/types.ts); change a contract only with a small `contract:` commit. Touch only your owned paths. You run in your own git worktree: follow the plan's "Worktrees, ports, syncing" section (use your assigned ports; .env and the SQLite DB are shared from the main checkout, never copy .env). Commit small and often with conventional commits, git add only your owned paths, then git pull --rebase origin main and git push origin HEAD:main. Report what you ran/clicked.
Owned: frontend/src/styles/ (Tailwind v4 tokens in theme.css), frontend/src/components/, frontend/src/firm/, frontend/src/dev/. After S4 lands its functional provider screens, you also restyle frontend/src/provider/ and the frame of frontend/src/source/SourcePane (coordinate via small commits; do not change their data logic). Do not touch backend/.
Audience: PI attorneys, paralegals, case managers (firm view) and treating medical providers (provider view). Professional, calm, dense-but-scannable; "where does this case stand" in 90 seconds. Use the frontend-design skill.
How to work:
1. Run the frontend (npm run dev in frontend/) and show it in the built-in browser pane. Work against a clearly fictional fixture in frontend/src/dev/fixture.ts ("Doe v. Example", invented content, typed as Dashboard from src/api/types.ts). No Sapini content anywhere in code.
2. First, show Aron 2–3 distinct visual directions for the Case Brief (screenshots at 1440×900): type scale, color, density, how the timeline strip and KPI tiles read. Ask him to pick or mix. Keep each round short; he answers between hackathon activities.
3. Then build the chosen direction as tokens + components: SourceChip ("Title · p.N"; dashed amber + "unverified" when verified=false), Tile, Card, Badge, Drawer, and the firm Case Brief page: header (client name + photo or initials, matter number, stage badge, Share button that calls an onShare prop) → subtle timeline strip at top (past events, today marker, upcoming deadlines) → headline status line + bullets → KPI tiles (specials, coverage/policy limits, firm spent, case value draft if present) → Needs action (overdue / upcoming / waiting on others) + last client contact → injuries → treatment by provider. Chip clicks call an onOpenSource(citation) prop; the integration session mounts SourcePane on it.
4. Loading/empty/error states, "Draft for attorney review · generated <time> · $<cost>" footer, sensible narrow-width layout (16px gutters, no horizontal scroll).
5. After every meaningful change, screenshot and ask Aron for feedback before moving on.
6. Once GET /api/matters/{id}/dashboard returns real data, switch to it (fixture only as a dev fallback) and delete frontend/src/dev/ before 3 PM.
Done when: Aron signs off on the Case Brief on real Sapini data at 1440×900 and narrow width, and the provider screens and SourcePane share the same visual language.
```

### S4 prompt

```
You own stream S4 (provider view + attorney-controlled sharing) of the Sapini dashboard.
Read CLAUDE.md, docs/challenge.md (Decisions) and docs/plans/2026-10-02-case-brief-dashboard.md first. Hackathon: move fast, no tests, verify by running it. Clio is READ-ONLY: only HTTP GET, through backend/app/clio/client.py. Never hardcode case content: everything shown must come from Sapini data read from Clio (no Sapini names, dates, amounts or injuries in code or prompts). Never print or commit .env values. Build against the shared contracts (backend/app/schemas.py, db.py, llm.py, frontend/src/api/types.ts); change a contract only with a small `contract:` commit. Touch only your owned paths. You run in your own git worktree: follow the plan's "Worktrees, ports, syncing" section (use your assigned ports; .env and the SQLite DB are shared from the main checkout, never copy .env). Commit small and often with conventional commits, git add only your owned paths, then git pull --rebase origin main and git push origin HEAD:main. Report what you ran/clicked.
Owned: backend/app/share/, backend/app/api/share.py, frontend/src/provider/. Import (never edit) frontend/src/components/ and the design tokens from S3 so your screens match; keep layout simple, since the S3 design session restyles provider/ after you land it. Put data logic in provider/api.ts and hooks so restyling does not touch it.
Goal: the attorney chooses what a treating provider sees and shares a link; the provider sees where the case stands without the file.
Sharing rules (slide 10): share status changes, bills and records; never strategy, attorney notes or unrelated confidential material. Filtering happens server-side: the provider endpoint must never return anything the settings exclude.
1. GET /api/matters/{id}/providers: medical-provider contacts from S1's contacts sources (by Clio contact type/custom field/relationship; fall back to companies named in treatment facts).
2. GET/PUT /api/matters/{id}/share/{contact_id}: ShareSettings with sensible defaults (status, coverage, treatment for this provider, requests to this provider on; timeline off; documents only those the attorney ticks). PUT mints a random token.
3. GET /api/share/{token}: build ProviderView from the cached Dashboard: provider-safe status line (derive from stage + last activity; no strategy), case_active, coverage, ActionItems that wait on this provider, this provider's TreatmentLine/bills, shared documents. Log share_views.
4. frontend/src/provider/SharePanel: drawer opened from the firm header Share button: provider picker, toggles, live preview of the provider page, Copy link, "Opened <time>" if viewed.
5. frontend/src/provider/ProviderPage at /p/:token: calm, plain billing/treatment language, big "Case active" and coverage answer, "What the firm needs from your office", "Your patient's visits and bills", shared documents opening in the source viewer.
Done when: on Sapini, toggling coverage off in the panel removes it from the provider page after reload, and the link works in a private window. Screenshot both.
```
