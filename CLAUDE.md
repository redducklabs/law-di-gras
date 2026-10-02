# Law-di-gras — Project Settings

## 🚨 THIS IS A HACKATHON PROTOTYPE — READ FIRST, EVERY SESSION 🚨

Law-di-gras is **The Swan law-di-gras hackathon project**. The goal is a **basic,
working, demoable prototype, fast.** Everything in this file bends toward that.

- **Move fast.** Get to something that runs end to end as early as possible, then
  improve it. A working ugly path beats a beautiful half-built one.
- **No tests.** Do not write unit, integration, or E2E tests. Do not add test
  frameworks, CI pipelines, coverage gates, or other pre-commit hooks (the
  secret guard in `.githooks/` is the one exception and stays on).
- **Minimal QA.** Verify by running the app and clicking through the demo path
  yourself. That is the whole QA process. Say what you exercised.
- **Functional over polished** for internals: inline freely, and skip
  abstractions, config layers, migrations, auth, and error handling the demo
  does not need.
- **🚨 But NEVER hardcode features or case content.** Judges read the repo and
  penalize hardcoded features. Everything shown about the case (dates, injuries,
  KPIs, summaries, status) must be generated from Sapini data read live from
  Clio. Stubbing plumbing is fine; faking the digestion is not.
- **UX and design still matter.** The demo is judged by what people see. The
  screens the demo touches must look intentional and feel good to use: clear
  hierarchy, consistent spacing and type, sensible empty/loading states, and no
  broken layouts. Spend polish on what is on screen, not on what is behind it.
- **Hard deadline: 4:00 PM PT, 2026-10-02.** Everything committed and the
  submission form in. Submit early (submission order = presentation order).
  Stop adding features well before 4:00 to record the 90-second video.
- **The deliverable includes a 90-second demo video** on Sapini. Build toward one
  scripted demo path. The app reads Clio live, but cache AI digestion in our own
  database so the demo is fast and does not re-digest on every open (an explicit
  attorney ask). Keep `docs/demo-script.md` current as features land. Playwright
  (already available) can drive and record the walkthrough.
- **No process overhead.** No issue tracker, no project board, no UAT, no Codex
  review loop, no PR gate. Commit straight to `main` unless the user asks
  otherwise.
- When a choice forks, pick the option that gets the demo working sooner and say
  which one you picked. Ask only when the answer changes what the user will see
  or cannot be undone.

## Who we are building for: PI attorneys and medical providers

The judges are **trial attorneys and AI builders**. The users are (1) the
**personal-injury firm's team** (attorneys, paralegals, case managers) and
(2) the **medical providers** treating the client on a lien. Both are
professionals, not consumers. Every design, prompt, and copy decision targets
them:

- **Speak their language.** Use PI and litigation terms as-is (matter, liens,
  policy limits, demand, treatment, specials, settlement, statute of
  limitations). No consumer hand-holding. Provider-facing views use plain
  billing/treatment language, not legal strategy.
- **Every claim traces to the record.** An attorney will not trust or use an
  output they cannot verify in seconds. Each factual or legal assertion links to
  its source: document, page, and line or highlighted span, opening the source
  right there (see the PDF patterns in the catalog).
- **Courtroom-grade accuracy.** A wrong cite or misquoted testimony in front of a
  judge damages the attorney's credibility. Quotes must be verbatim; anything the
  app cannot verify is visibly marked, never presented as fact.
- **Ninety seconds is the bar.** A user should absorb where the case stands in
  about 90 seconds, then drill down on demand. One headline status, the few
  items that need action, then detail. Fewer widgets, not more.
- **Draft, not decision.** Outputs are work product the attorney reviews and
  owns. The AI assists their judgment; it does not replace it.
- **Provider views share only what the attorney allows.** Status changes, bills
  and records yes; case strategy and unrelated confidential material no. The
  attorney controls and can adjust what a provider sees.
- **Treat case materials as confidential.** Sapini is the only case we use;
  never send case data anywhere the user did not approve.

## The challenge

**Build a dashboard that digests one live Clio Manage PI matter ("Sapini") so
(1) firm team members get up to speed fast and (2) the treating medical
providers get visibility into the case.** Both halves are required, and it must
be a visual digestion, not just an AI chat. Full brief, user asks, sharing
rules, and submission requirements: `docs/challenge.md`. Read it first.

Slides received so far are saved in `docs/slides/`. Save every new slide or deck
there too.

## Brainstorming workflow (next step)

The organizers' deck is saved in `docs/slides/` and digested into
`docs/challenge.md`. Brainstorm it **with the user, iteratively**, before
building, and keep it fast: the deadline is 4:00 PM. Use the `superpowers:brainstorming` skill, with
these overrides:

1. **Start from `docs/challenge.md`.** Skim the deck PDF for visuals if useful.
   Add any new slides or live notes the user shares.
2. **Ask about priorities, a few questions at a time.** Each question has short
   options with your recommendation marked first. Ask about what to prioritize
   (which of the slide-09 asks to build, the firm/provider split, what the
   90-second video must show, and what the Clio setup status is) before how to build it.
   Keep rounds short; the user answers between hackathon activities.
3. **Propose 2–3 solution concepts**, each with the demo moment that wins the
   room and which catalog patterns it reuses. Narrow to one with the user.
4. **Write the decision and a short build plan.** Record decisions in
   `docs/challenge.md` under "Decisions". Put the plan, a checklist of the demo
   path, in `docs/plans/YYYY-MM-DD-<topic>.md`. No Codex review and no separate
   spec unless the user asks; skip the skill's default
   `docs/superpowers/` paths.
5. **Split the plan into parallel workstreams and hand the user one prompt per
   stream.** Once the concept is approved, the user runs several Claude Code
   sessions at once to go faster. In the plan:
   - Define the **shared contracts first** (data shapes, API routes, DB schema,
     folder layout) and commit them to `main` before any stream starts, so streams
     build against the same interfaces.
   - Cut the work into **2–4 independent streams** with disjoint file ownership
     (for example: Clio read client and ingestion; AI digestion and cache; firm
     dashboard UI; provider view and sharing). Name the directories each stream
     owns and the ones it must not touch.
   - Write a **self-contained, copy-paste prompt per stream** in the plan file and
     in your reply: goal, owned paths, contracts to build against, what "done"
     looks like on Sapini, and the rules that always apply (read CLAUDE.md, Clio
     read-only, no hardcoded case content, no tests, commit small and often to
     `main` with `git pull --rebase` before each push, touch only owned paths).
   - Say which stream is the critical path for the demo and which to drop first
     if time runs short.
6. **Start building as soon as the user approves the plan.** This session
   usually takes the integration stream: wiring streams together and keeping the
   demo path working.

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
- **🚨 Secrets live ONLY in the main checkout's `.env` (`c:\repos\law-di-gras\.env`),
  and are NEVER committed. 🚨** `.env.example` lists every variable (Clio OAuth
  app ID/secret, redirect URI, tokens, AI keys). Never print, log, echo, or paste
  their values into code, docs, commit messages, or chat.
  - **Worktrees do not have the `.env`.** We work in git worktrees, and `.env` is
    gitignored, so a worktree starts without it. Anything that calls Clio or an AI
    API must load the main checkout's `.env`. Find the main root with
    `git rev-parse --path-format=absolute --git-common-dir` and take its parent
    directory; use `<main root>/.env` (fall back to a local `.env` only if the
    main one is missing). App config code must do this resolution itself, so the
    app runs correctly from any worktree. For a quick one-off you may copy the
    file into the worktree (it stays gitignored), but never commit it.
  - **Token writes go to the main `.env` only.** The Clio OAuth login and
    refresh code updates `CLIO_ACCESS_TOKEN`/`CLIO_REFRESH_TOKEN` in the main
    checkout's `.env`, never in a worktree copy, so every worktree shares one
    valid token. Clio API access is already authorized and verified (see
    `docs/challenge.md`); do not re-run the login unless a call returns 401
    after refresh.
  - **A pre-commit secret guard is on** (`.githooks/`, enabled with
    `git config core.hooksPath .githooks`, which all worktrees share). It blocks
    any `.env*` file except `.env.example`, known key formats, and any value
    from the main `.env`. Never bypass it (`--no-verify` is forbidden). If it
    blocks you, remove the secret; do not weaken the guard. Stage files by path
    and check `git status` before committing; avoid blind `git add -A`.
  - Clio uses OAuth 2.0 (`https://app.clio.com/oauth/authorize` and
    `/oauth/token`, US). Notes need `type=Matter`. The user's Clio password is
    never needed and must never be stored.
- **No hallucinated law.** If the prototype emits legal citations (statutes,
  rules, cases), they must come from material the app actually retrieved or the
  user supplied, never from model memory. Prefer the simplest grounding pattern
  in the catalog that works; a clearly labeled "unverified" state is acceptable
  for a demo, a confidently invented citation is not.
- **No consumer UPL framing.** The users are professionals, so skip
  "information, not advice" disclaimers and hedged consumer copy. Write direct, professional
  analysis, and mark AI output as a draft for attorney review.
- **Structured LLM output is schema-enforced**, never regex or `json.loads` on
  free text. Opus 5.5 and Sonnet 5.5 reject forced `tool_choice` (400), so use
  `app.llm.structured()` (`messages.parse` with a Pydantic `output_format`).
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

## Parallel sessions and worktrees

Build streams run as parallel Claude Code sessions, each in its own git
worktree; the integration session stays in the main checkout. The plan
(`docs/plans/2026-10-02-case-brief-dashboard.md`, "Worktrees, ports, syncing")
holds the details. Essentials:

- Land work with `git pull --rebase origin main` then `git push origin HEAD:main`
  from the worktree branch. Stage only your owned paths, never `git add -A`.
- `.env` and the SQLite DB (`backend/data/`) are shared from the main checkout
  via `backend/app/config.py`. Never copy `.env` into a worktree.
- Each session uses its assigned backend/frontend ports from the plan.
- `frontend/.npmrc` pins `os=win32` because the global npm config says linux.

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
