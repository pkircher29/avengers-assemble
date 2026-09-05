# Phase 2 Plan: Avengers Mission Console

## Objective
Turn the verified Chuck–Claude prototype into a local-only, inspectable mission console. `/avengers-assemble <goal>` will be treated as the group’s standing goal contract: persisted objective, visible status, pause/resume/clear lifecycle, bounded worker rounds, evidence, and explicit human control.

## Scope and honest boundary
This phase supports Chuck-directed Claude work only. It does not modify Hermes’s native `/goal` command or create automatic group reasoning/dispatch in the Hermes loop. A skill invocation can establish and maintain the same goal contract, but true automatic multi-agent continuation requires a later Hermes integration after the local control plane is proven.

No public listener, autostart, remote access, generic peer bus, or additional runtime adapter is included.

## Architecture
- `bridge.py`: local runner and local HTTP control plane bound only to `127.0.0.1`; retains explicit visible Claude console.
- `state/mission.json`: atomic durable group-goal record.
- `state/status.json`, `events.jsonl`, request/results folders: existing evidence plane.
- `dashboard.html`: dependency-free local dashboard served by the bridge.
- Claude worker: isolated `claude-workspace`, restricted file tools, explicit assignment only.

## Goal-style group lifecycle
- `start`: create/replace a mission only after Paul explicitly activates the team; record objective, acceptance checks, budget, requested model/effort, and state `active`.
- `status`: show goal, participant state, worker runtime settings, turns/rounds, evidence and blockers.
- `pause`: stop new dispatch; retain state and current evidence. A running worker finishes only if no hard stop is requested.
- `resume`: reactivate the existing mission; do not duplicate processed request IDs.
- `clear`: require stopped/paused mission, preserve evidence, then archive the mission state.
- `stop-worker`: request hard stop for active runner and verify process state.

## Plan / checklist

### Slice 1 — Stable baseline
- [ ] Create `.gitignore`, `README.md`, repository, and initial commit.
- [ ] Preserve prototype limitations and known-good test command.
- [ ] Verify clean working tree after commit.

### Slice 2 — Mission contract and goal lifecycle
- [ ] Add a pure mission-state module with validation and atomic persistence.
- [ ] Add unit tests for start/status/pause/resume/clear and invalid transitions.
- [ ] Add bridge commands for mission state without auto-launching a worker.
- [ ] Verify all Python tests and commit.

### Slice 3 — Local console
- [ ] Serve a dependency-free dashboard only at `127.0.0.1`.
- [ ] Show mission objective/state, explicit boundaries, worker status, requested/effective model + effort, and event timeline.
- [ ] Provide keyboard-accessible pause, resume, stop-worker, and refresh controls; use POST endpoints and CSRF-free localhost-only scope.
- [ ] Verify served response and control endpoints; commit.

### Slice 4 — Group-goal proof and recovery
- [ ] Start a mission, explicitly launch Claude, send one bounded worker task, and verify visible state/output.
- [ ] Pause/resume without duplicating the request; verify processed IDs and same session where applicable.
- [ ] Stop worker, verify stopped state, and preserve mission/event evidence.
- [ ] Commit verified final state.

### Slice 5 — Skill semantics
- [ ] Update `/avengers-assemble` instructions with `status`, `pause`, `resume`, `clear`, `wait`, and gate semantics modeled on `/goal`.
- [ ] Clearly distinguish goal-like persistence from native Hermes auto-continuation.
- [ ] Read back skill and verify commands point to real prototype operations.

## Acceptance criteria
- [ ] Mission record survives runner stop/start and invalid transitions are rejected.
- [ ] Dashboard is reachable only through loopback and reflects actual stored state; no fake terminal/activity is shown.
- [ ] Model/effort requested and effective values are visibly distinguished.
- [ ] Pause prevents new dispatch; resume does not duplicate work; hard stop is verifiable.
- [ ] Claude performs at least one bounded task in its separate visible console, with Chuck independently verifying the artifact.
- [ ] Test suite passes, module syntax checks pass, Git has no uncommitted change, and all claims match evidence.

## Risks
| Risk | Mitigation |
|---|---|
| Dashboard implies capabilities it does not have | Prominent V0/worker scope boundary and only source state from real events. |
| Worker duplication after restart | Validate and persist request IDs before run. |
| Native `/goal` equivalence overclaimed | Document that skill semantics are goal-shaped; defer Hermes core integration. |
| Local controls accidentally become LAN service | Bind to `127.0.0.1` only and test listener address. |
| Agent changes collide | Chuck owns bridge/control-plane files; Claude owns only its isolated worker artifacts. |
