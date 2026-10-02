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

## Audience: trial attorneys

Users are trial attorneys, not consumers. Use litigation vocabulary, make every
claim trace to its source (document, page, line or highlighted span), keep
quotes verbatim and visibly mark anything unverified, favor dense scannable
screens and paste-ready citation formats, present AI output as a draft for
attorney review, and use only sample or public case materials in the demo.

## Challenge

Not known yet beyond the audience. Do not write application code or pick a
stack until the user says so. Once known, it lives in `docs/challenge.md`.

## Reuse before you build

Read `docs/reuse-catalog.md` before building AI-generation or document-viewing
features. It points into `c:\repos\aurolegal.ai` (anti-hallucination/grounding)
and `c:\repos\redducklaw` (PDF viewing/highlighting). Copy from them freely;
never modify them.

## Limits that still apply

- No hallucinated law: legal citations come only from retrieved or
  user-supplied material, never model memory.
- No consumer "information, not advice" framing; write direct professional
  analysis marked as a draft for attorney review.
- Structured LLM output uses forced tool calling, not text parsing.
- No secrets in git; use `.env` plus `.env.example`.

## Environment and reporting

- Windows: use Windows paths and native git; no WSL path rewriting.
- US English, concise. Final responses state **What was done**, **What
  remains**, and **What you need to do** (use **None** when empty).
- Do not modify `CLAUDE.md` or Claude-specific setup unless asked.

## Context health and handoffs

Read `handoffs/README.md` when continuing earlier work.
<!-- agent-handoff-toolkit:start -->
Agent handoff toolkit. Sessions run untracked by default and nothing is gated
until a root is registered.

- Register a root only for work that continues in another session or that the
  user will resume later. Attempt
  `python .agent-handoff-toolkit/runner.py lifecycle register-root --scope-id <id> --scope-kind <kind> --scope-title "<title>" --scope-outcome "<outcome>"`;
  the denial returns the bound command after `Command:`; run that verbatim.
- A user prompt whose first line is `Track: <goal>` registers that goal as the
  root; one whose first line is `Continue from handoff: <path>` resumes that
  record's chain. Either way the rest of the prompt is the work, and
  `AHK-TRACK-FAILED` or `AHK-RESUME-FAILED` means it did not take effect.
- A tracked session ends with a continuation or a completion audit, authored
  through the `agent-handoff` skill. The renderer is the only source of the
  final response: send the `render-tail` output as your entire final message.
  A turn that is merely unfinished may instead end on the exact
  `progress_response` from `lifecycle inspect`; nothing else record-less is
  accepted.
- `AHK-DECLARE` and `AHK-NO-HANDOFF` are notices, not errors, and each fires
  once. `lifecycle one-off` records that a session needs no handoff.
- If a hook looks broken, run
  `python .agent-handoff-toolkit/runner.py lifecycle doctor` from the
  repository root. An `AHK-HOOK-RUNTIME` notice blocks nothing in an untracked
  session.
- Handoff records that predate the installed release are historical. Do not
  read, validate or migrate them.
- Run `install` and `sync` only from the toolkit release checkout.
<!-- agent-handoff-toolkit:end -->
