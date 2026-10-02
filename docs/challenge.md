# Challenge brief

Source: organizers' deck, `docs/slides/LDG-8_30-LDG-Hackathon.pdf` (20 slides), plus
live notes. Event: Swans · Applied AI Hackathon, Law-Di-Gras, San Diego,
2026-10-02. Swans builds AI for US personal-injury (PI) firms; this is a real
problem their clients would pay for.

## 🚨 Hard facts

- **Deadline: 4:00 PM PT today, hard close.** Form submitted and all work
  committed. Submit early: submission order = presentation order.
- **Input: one Clio Manage matter, "Sapini"**, built from a real litigated PI
  case. Every team uses it. Our build must **read it live from our own Clio
  Manage trial account** (team creates the trial, then runs the organizers'
  setup app to load Sapini; ~10–15 min, start it first).
- **Clio is read-only.** API reads are fine; anything that writes or updates
  case data is not. Need a database? Bring our own, outside Clio.
- **They read the repo.** Features are verified from code. **Hardcoded features
  are quickly identified and count against us.** The digestion must be
  genuinely generated from Sapini's data.
- Judges: **trial attorneys and AI builders** (the real buyers). Swans screens
  every build 4–5 PM (does it run, does it work on Sapini, generated vs
  hardcoded, engineering) → **Top 7** pitch (4 min, around the video) → Top 3 on
  main stage ~7 PM. "Top 7 is won in the code. Winning is won on the stage."
- Prizes: $2,500 / $1,500 / $1,000. We own what we build.

## Links (decoded from the deck's QR codes)

- Setup app (Clio seeder): https://clio-seeder-405499094876.us-central1.run.app/
- Submission form: https://swans.fillout.com/t/1PkfYHm6P9us
- Slides and materials: https://drive.google.com/drive/folders/1yzQE1r1N857mqK28xNeGxlcpHE_G0p2-?usp=sharing

## Seeder setup (what loads Sapini)

1. Create Clio Manage trial. 2. Connect Clio in the seeder. 3. **By hand in
Clio:** add eight matter stages to the Personal Injury practice area, in order,
spelled exactly: Intake, Treatment, Demand, Negotiation, Litigation, Trial,
Disbursement, Closed. Then press *Check stages*. 4. *Create fields*: sixteen
"Case Briefing" custom fields. 5. Populate the matter.

Sapini matter as the seeder describes it: **Justin Sapini, stage Litigation.**
"Still treating three years on, in suit and stuck in discovery. The second
shoulder surgery is recommended and has no date, which is what the case is
worth turning on." 31 documents (14 MB), 42 notes, 69 communications, 14 tasks,
17 events, 14 case expenses. The seeder's writes are setup, not our app; our
app never writes to Clio.

## The challenge (slide 08)

Build a solution that acts as a **dashboard** to:

1. **Get internal firm team members up to speed on a case.**
2. **Improve communication and visibility on the case for the medical providers**
   treating the client.

**Both halves.** Approach is ours. It must go **beyond an AI chat**: a *visual
digestion* of everything already in the case, so attorney and providers get up
to speed **without having to know what to ask**.

## The problem (slides 05–07)

- PI basics: client hurt (classic: car crash) → attorney on contingency →
  doctors treat now, paid from settlement later via a **lien** → case takes years,
  file grows to thousands of pages → liens usually negotiated down at the end.
- **Capturing is solved** (Clio already holds notes, emails, dates, contacts,
  documents). **Digesting is not:** turn a live case file into something a human
  absorbs in **ninety seconds**.
- The firm reconstructs every case by hand. Providers can't see where the case
  is or whether there's coverage. Both fall back to email "with no intelligence
  in it".
- Existing tools (slides 11–13: Clio Manage, CasePeer, Lawmatics): good
  dashboards, but counts and lists, detail one jump away, story assembled by
  hand. Organizer live comment: you can't see what's required or the state of
  things **at a glance**.

## Sapini data available in Clio (slide 15)

One matter with: contacts, native + custom fields, notes, case expenses,
communications, tasks, calendar, and documents **including scanned PDFs**
(OCR needed).

## What users asked for (slide 09: "a menu, not a spec")

**Attorneys**
- Get me up to speed and show what happened recently, without asking anyone.
- What changed since I last opened this matter?
- Out of 300 entries, show me the 10 that matter.
- Sometimes 2-minute catch-up, sometimes dig into everything (progressive depth).
- **If a date is on screen, show where it came from.**
- **Click anything to open the note, document or email it came from.**
- Show the client's picture as soon as I open the matter.
- Somewhere in a 200-page scan are my client's primary injuries.
- When did anyone last actually talk to the client?
- **Don't re-digest the whole case with AI every time someone opens it** (cache /
  incremental processing in our own DB).
- What's overdue, what's coming, what's waiting on someone else?
- **Top two KPIs: what is the case worth, and what coverage sits behind it.**
- How much has the firm already spent on this case?
- What did we share with this provider, and has anyone in their office opened it?
- Let treating doctors see where the case is without handing over my whole file.
- Let me adjust what the provider sees before I send it.
- A secure way to share part of my case with providers.

**Medical providers**
- I'm treating on a lien: is there coverage behind the case?
- Is this case even still alive?
- Tell me when the case moves; I shouldn't have to email.
- I only see the records I sent; I'm treating with one eye closed.
- What does the firm need from my office right now?
- Is my patient still showing up to treatment?

## Sharing rules (slide 10)

- **Share with providers:** status changes, bills and records.
- **Don't share:** case strategy; anything confidential not relevant to the
  provider.
- Attorneys differ on what they share, so the attorney should control it. Ask
  attorneys in the room when unsure.

## Submission (slide 17)

1. GitHub repository (the repo *is* the submission).
2. **90-second clip** on Sapini showing the solution and its visuals; Google
   Drive link, public access.
3. Tech stack: built with, running on, where data lives outside Clio.
4. **AI models used for digestion and approximate cost per case** (attorneys
   think per case).
5. Notes for judges: differentiator, where to look first, anything half-done or
   hardcoded.
6. Optional live link or install path (localhost can win).

## Working notes (from Aron, before the deck)

- Direction: **turn a case into a dashboard**, every fact linked to its source.
- First screen answers "where does this case stand and what needs doing now?" in
  seconds; detail on demand.

## Decisions

Brainstorm, 2026-10-02. Plan: `docs/plans/2026-10-02-case-brief-dashboard.md`.

- **Concept: Case Brief + source pane.** One screen: subtle timeline strip at the
  top, headline status, KPI tiles, needs-action list, injuries/treatment. Every
  fact is a source chip that opens a right-side pane at the highlighted span.
  Reason: answers "where does it stand" in 90 seconds and proves every fact.
- **Firm priorities:** (1) status + source links, (2) KPIs: value drivers,
  coverage, firm spend, (3) actions: overdue / upcoming / waiting on others,
  last client contact, (4) injuries from scans (lower priority; page-level
  highlight acceptable).
- **Provider priorities:** status + coverage ("is it alive, is there money"),
  attorney-controlled share (toggle sections, preview, share link), what the
  firm needs from this provider. Opened-tracking is nice to have.
- **Provider view = same cards, filtered server-side** by the attorney's share
  settings. Strategy, notes and unshared sources never reach the provider API.
- **Video:** open Sapini → grasp status + KPIs → click a date/injury → source
  opens highlighted → toggle provider sharing → provider view.
- **Stack:** FastAPI (Python 3.13, uv) + SQLite; React + Vite + TypeScript +
  Tailwind; react-pdf with a highlight overlay. Reason: copy Python grounding
  code from aurolegal, PyMuPDF for text positions.
- **Models:** Haiku 4.5 for bulk ingestion (HyDE questions, OCR cleanup); Sonnet 5.5 for fact extraction; Opus 5.5 for the headline brief and
  cited Q&A. Every call logs tokens and cost for the "cost per case" answer.
- **Retrieval must be strong:** chunks + Haiku HyDE questions, embedded with
  OpenAI `text-embedding-3-large`, fused with SQLite FTS5 BM25 by RRF, then Cohere
  `rerank-v3.5` (falls back to RRF order if no `COHERE_API_KEY`). Each dashboard field is extracted from retrieved evidence.
- **On screen, retrieval also powers** "Find in case" (cited passages) and,
  if time allows, cited Q&A (secondary; the brief says beyond chat).
- **Scanned PDFs:** RapidOCR (pip, no system install) gives line boxes for
  highlights; PyMuPDF words for text PDFs.
- **Grounding:** forced tool calls; a fact is "verified" only if its quote is a
  verbatim (normalized) span of the source; otherwise shown as unverified.
- **Cache:** all digestion keyed by content hash in SQLite; re-digest only
  changed sources.
