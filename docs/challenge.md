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

_None yet. Record each brainstorming decision here with a one-line reason._
