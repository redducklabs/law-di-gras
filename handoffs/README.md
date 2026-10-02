# Law-di-gras handoff overlay

The canonical handoff and completion-audit protocol is
[`docs/agent-handoff/contract.md`](../docs/agent-handoff/contract.md), with
formats in [`docs/agent-handoff/mechanics.md`](../docs/agent-handoff/mechanics.md).
Templates are under `handoffs/templates/`; the `agent-handoff` skill is installed
for both Claude Code and Codex.

## Hackathon scope

Most sessions here are one-offs and need no handoff. Register a tracked root only
when demo work will continue in another session (for example, a teammate picks
it up or the context window runs out mid-feature). The highest scope is
normally "the demo works end to end," not the current feature.

When a handoff is needed, keep it short: what runs now, what is broken or
stubbed, the exact next step, and how to start the app.

## Commands

Validate a new record before presenting it:

```text
python .agent-handoff-toolkit/runner.py validate handoffs/<record>.md
```

Render the final response from it and send that output verbatim:

```text
python .agent-handoff-toolkit/runner.py render-tail handoffs/<record>.md
```

Name continuations `YYYY-MM-DD-<short-topic>-handoff.md`.
