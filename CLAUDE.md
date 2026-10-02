# Law-di-gras — Project Settings

## 🚨 THIS IS A HACKATHON PROTOTYPE — READ FIRST, EVERY SESSION 🚨

Law-di-gras is **The Swan law-di-gras hackathon project**. The goal is a **basic,
working, demoable prototype, fast.** Everything in this file bends toward that.

- **Move fast.** Get to something that runs end to end as early as possible, then
  improve it. A working ugly path beats a beautiful half-built one.
- **No tests.** Do not write unit, integration, or E2E tests. Do not add test
  frameworks, CI pipelines, coverage gates, or pre-commit hooks.
- **Minimal QA.** Verify by running the app and clicking through the demo path
  yourself. That is the whole QA process. Say what you exercised.
- **Functional over polished** for internals: hardcode, stub, mock, and inline
  freely. Skip abstractions, config layers, migrations, auth, and error handling
  that the demo does not need.
- **UX and design still matter.** The demo is judged by what people see. The
  screens the demo touches must look intentional and feel good to use: clear
  hierarchy, consistent spacing and type, sensible empty/loading states, and no
  broken layouts. Spend polish on what is on screen, not on what is behind it.
- **The deliverable ends in a demo video.** Build toward one scripted demo path
  that runs reliably from a clean start with seeded or cached data (no live
  dependency that can stall on camera). Keep `docs/demo-script.md` current as
  features land. Playwright (already available) can drive and record the walkthrough.
- **No process overhead.** No issue tracker, no project board, no UAT, no Codex
  review loop, no PR gate. Commit straight to `main` unless the user asks
  otherwise.
- When a choice forks, pick the option that gets the demo working sooner and say
  which one you picked. Ask only when the answer changes what the user will see
  or cannot be undone.

## Who we are building for: trial attorneys

The users are **trial attorneys** (litigators preparing for and running trials),
not consumers. Every design, prompt, and copy decision targets them:

- **Speak their language.** Use litigation terms as-is (exhibits, depositions,
  pin cites, motions in limine, impeachment, witness outlines, separate
  statements). Do not simplify legal concepts or add consumer hand-holding.
- **Every claim traces to the record.** An attorney will not trust or use an
  output they cannot verify in seconds. Each factual or legal assertion links to
  its source: document, page, and line or highlighted span, opening the source
  right there (see the PDF patterns in the catalog).
- **Courtroom-grade accuracy.** A wrong cite or misquoted testimony in front of a
  judge damages the attorney's credibility. Quotes must be verbatim; anything the
  app cannot verify is visibly marked, never presented as fact.
- **Time pressure is the context.** Trial prep happens late at night and between
  sessions. Favor dense, scannable screens, fast search, keyboard-friendly flows,
  and outputs they can paste into a brief or outline (proper citation formats).
- **Draft, not decision.** Outputs are work product the attorney reviews and
  owns. The AI assists their judgment; it does not replace it.
- **Treat case materials as confidential and privileged.** Use sample or public
  documents for the demo; never send real client files anywhere the user did not
  approve.

## The challenge

**Not announced yet**, but the organizers' slides point at **personal-injury
law**: a years-long, document-heavy case where both the PI firm and the
lien-holding medical providers need to see where the case stands. Read
`docs/challenge.md` for the context gathered so far. The final challenge may
widen the users beyond trial attorneys to firm staff and provider billing
teams. Until then, do not write application code or pick a stack beyond what
the user asks for. When the challenge is known, record it in
`docs/challenge.md` and update this section with a one-sentence product goal for
trial attorneys.

Slides received so far are saved in `docs/slides/`. Save every new slide or deck
there too.

## Brainstorming workflow (next step)

The organizers will hand out a slide deck. Brainstorm it **with the user,
iteratively**, before building. Use the `superpowers:brainstorming` skill, with
these overrides:

1. **Ingest the deck.** Save it to `docs/slides/`. Extract the problems, users,
   constraints, judging criteria, provided data and deadlines into
   `docs/challenge.md`, replacing the inferences section with facts.
2. **Ask about priorities, a few questions at a time.** Each question has short
   options with your recommendation marked first. Ask about what to prioritize
   (which user, which problem, what the demo must show) before how to build it.
   Keep rounds short; the user answers between hackathon activities.
3. **Propose 2–3 solution concepts**, each with the demo moment that wins the
   room and which catalog patterns it reuses. Narrow to one with the user.
4. **Write the decision and a short build plan.** Record decisions in
   `docs/challenge.md` under "Decisions". Put the plan, a checklist of the demo
   path, in `docs/plans/YYYY-MM-DD-<topic>.md`. No Codex review and no separate
   spec unless the user asks; skip the skill's default
   `docs/superpowers/` paths.
5. **Start building as soon as the user approves the plan.**

Working direction so far: **turn a PI case into a dashboard** of where the case
stands, for the firm and the medical providers, with every fact linked to its
source page.

## Reuse before you build

`docs/reuse-catalog.md` lists proven patterns from two sibling Red Duck Labs
projects, with file locations:

- `c:\repos\aurolegal.ai` — anti-hallucination and grounding for legal AI
  output (citations only from retrieval, regen-then-scrub, judges, forced tool
  calling).
- `c:\repos\redducklaw` — PDF viewing, text extraction with positions, and
  highlighting cited source spans.

Read the catalog before building any AI-generation or document-viewing feature.
Copy and adapt code from those repos when it saves time, but **never modify the
source repos** — they are read-only references.

## Limits that still apply (even in a hackathon)

Speed does not license these. They are cheap to keep and embarrassing to break
in a legal demo.

- **🚨 The case-management API (likely Clio) is READ-ONLY. NEVER write to it. 🚨**
  The organizers will provide API access to a live practice-management system.
  Only ever issue read requests (HTTP `GET`). Never call `POST`, `PUT`, `PATCH`
  or `DELETE`, never call any endpoint that creates, updates, deletes, uploads,
  sends or triggers anything, and never run a script that might. Wrap the API in
  one client module that exposes only read methods and refuses any non-`GET`
  request. Anything the app needs to persist (notes, flags, AI output) goes in
  our own local storage, never back into that system. If a feature seems to need
  a write, stop and ask the user.
- **No hallucinated law.** If the prototype emits legal citations (statutes,
  rules, cases), they must come from material the app actually retrieved or the
  user supplied, never from model memory. Prefer the simplest grounding pattern
  in the catalog that works; a clearly labeled "unverified" state is acceptable
  for a demo, a confidently invented citation is not.
- **No consumer UPL framing.** The users are attorneys, so skip "information,
  not advice" disclaimers and hedged consumer copy. Write direct, professional
  analysis, and mark AI output as a draft for attorney review.
- **Structured LLM output uses forced tool calling** (`tool_choice` +
  `input_schema`), not regex or `json.loads` on free text. It is also the
  fastest path to reliable output.
- **No secrets in git.** Keys go in `.env` (ignored); commit a `.env.example`.
- **Use the latest Claude models** for any AI feature unless the user says
  otherwise.

## Execution Environment

Claude Code runs on Windows here. Use Windows paths and PowerShell syntax when
giving local commands. In Git Bash, `export MSYS_NO_PATHCONV=1` before passing
POSIX-looking arguments (log-group names, container paths) to CLIs.

## Communication

- Use US English. Plain language, as concise as possible.
- Lead with what now works (or what is blocking the demo), not implementation
  detail. No raw command output unless it explains a blocker.
- Every final response covers **What was done** (and what you actually ran or
  clicked), **What remains** for the demo, and **What you need to do**. Use
  **None** when empty; do not invent follow-ups.

## Documentation Locations

- Challenge brief and decisions → `docs/challenge.md`
- Design notes (if any) → `docs/specs/YYYY-MM-DD-<topic>-design.md`
- Plans (if any) → `docs/plans/YYYY-MM-DD-<topic>.md`
- Never write to `docs/superpowers/...`; override skill defaults.
- Keep docs short. A plan is a checklist, not an essay. Skip specs and plans
  entirely for anything small enough to just build.

## Keep project knowledge in the project

Put setup steps, gotchas, and run commands in `README.md` or this file and
commit them, not in agent-local memory. Fix stale instructions the moment you
notice them.

## Source Control

- Default: commit directly to `main` with conventional commits (`feat:`, `fix:`,
  `docs:`, `chore:`, `style:`). Small, frequent commits are fine.
- Push when the user asks or at natural checkpoints they have approved.
- Do not attribute Claude in commit messages.

## Context health and handoffs

Read `handoffs/README.md` at the start of a session that continues earlier work.
Hackathon sessions are usually one-offs; register a tracked root only when work
will genuinely continue in another session.
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
