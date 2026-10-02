# Law-di-gras — Codex Instructions

`CLAUDE.md` is the source of truth for this repository. Read it before any work.
The short version:

## 🚨 This is a hackathon prototype 🚨

- **Goal: a basic, working, demoable prototype, fast.** Get an end-to-end path
  running early, then improve it.
- **No tests.** No test frameworks, CI, coverage, or pre-commit hooks.
- **Minimal QA:** run the app and click through the demo path; say what you
  exercised.
- **Functional over polished** behind the scenes: hardcode, stub, and mock
  freely.
- **UX and design still matter** on every screen the demo touches: clear
  hierarchy, consistent spacing and type, sensible empty/loading states, no
  broken layouts.
- **No process overhead:** no issue tracker, board, UAT, review loop, or PR gate.
  Commit to `main` only when the user asks.
- When a choice forks, pick what gets the demo working sooner and say so.

## Challenge

Not known yet. Do not write application code or pick a stack until the user
says so. Once known, it lives in `docs/challenge.md`.

## Reuse before you build

Read `docs/reuse-catalog.md` before building AI-generation or document-viewing
features. It points into `c:\repos\aurolegal.ai` (anti-hallucination/grounding)
and `c:\repos\redducklaw` (PDF viewing/highlighting). Copy from them freely;
never modify them.

## Limits that still apply

- No hallucinated law: legal citations come only from retrieved or
  user-supplied material, never model memory.
- Legal output is information, not advice, unless users are lawyers.
- Structured LLM output uses forced tool calling, not text parsing.
- No secrets in git; use `.env` plus `.env.example`.

## Environment and reporting

- Windows: use Windows paths and native git; no WSL path rewriting.
- US English, concise. Final responses state **What was done**, **What
  remains**, and **What you need to do** (use **None** when empty).
- Do not modify `CLAUDE.md` or Claude-specific setup unless asked.

## Context health and handoffs

Read `handoffs/README.md` when continuing earlier work.
