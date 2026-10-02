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
- **No process overhead.** No issue tracker, no project board, no UAT, no Codex
  review loop, no PR gate. Commit straight to `main` unless the user asks
  otherwise.
- When a choice forks, pick the option that gets the demo working sooner and say
  which one you picked. Ask only when the answer changes what the user will see
  or cannot be undone.

## The challenge

**Not known yet.** It will be announced at the hackathon. Until then, do not
write application code or pick a stack beyond what the user asks for. When the
challenge is known, record it in `docs/challenge.md` and update this section with
a one-sentence product goal.

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

- **No hallucinated law.** If the prototype emits legal citations (statutes,
  rules, cases), they must come from material the app actually retrieved or the
  user supplied, never from model memory. Prefer the simplest grounding pattern
  in the catalog that works; a clearly labeled "unverified" state is acceptable
  for a demo, a confidently invented citation is not.
- **Information, not advice.** User-facing legal output is framed as general
  information, with a short disclaimer, unless the challenge says the users are
  lawyers.
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
