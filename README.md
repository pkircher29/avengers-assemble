# Avengers Assemble — local mission console

A deliberately small, local-only control plane for Chuck-directed agent work.

## What is verified today

- Explicit local launch of a real Claude Code worker in a separate visible Windows console.
- Durable request, result, event, and status artifacts.
- Exact Chuck→Claude message-envelope validation.
- Claude session continuation.
- A restricted Claude worker can report inability to test; Chuck independently verifies it.
- `claude-workspace` unit suite: `(cd claude-workspace && python -m unittest -v)`.

## Phase 2 direction

A loopback-only mission console adds goal-style mission state, pause/resume/clear controls, honest worker/model status, and recovery evidence. Read `tasks/phase2-plan.md` for scope and acceptance criteria.

## Deliberate limits

This is not an interactive Claude TUI, generic peer bus, public service, autostart daemon, or a native Hermes `/goal` replacement. `/avengers-assemble` is a skill that establishes group-goal operating semantics; automatic group continuation in Hermes needs a later, separately verified integration.

## Safety

Paul explicitly activates teams. Chuck works solo otherwise. Chuck directs workers and verifies their claims. No agent may expand scope, spend, permissions, or external authority.
