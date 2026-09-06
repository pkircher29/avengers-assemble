# Dashboard V1 implementation plan

## Phase 1: Data contract
- [ ] Define `agent_registry.json` with agent id, adapter, lifecycle state, workspace, terminal/session handle, controls, requested/effective model/effort, evidence source, and known limitations.
- [ ] Create a pure Python telemetry aggregator that reads only real runner/status/session records and returns `unavailable` for absent data.
- [ ] Unit-test lifecycle and unavailable-state derivation.

## Phase 2: Console API and roster UI
- [ ] Add `/api/roster`, `/api/telemetry`, and control receipt events.
- [ ] Expand dashboard into roster, task/event stream, usage, model/effort, controls, deliverables, and terminal cards.
- [ ] Provide local-only native terminal action only for adapters with an actual supported launch/attach path.
- [ ] Test endpoint shape and browser rendering.

## Phase 3: Claude adapter
- [ ] Register Claude from real bridge state/events/results.
- [ ] Surface API-reported cost/token data where present and `unavailable` otherwise.
- [ ] Implement/verify open-or-focus native terminal action without inventing an embedded PTY.

## Phase 4: Tally adapter
- [ ] Register Tally as foundation-created with runtime-probed model route and bounded-task evidence.
- [ ] Parse its session metadata for reported usage/model/reasoning, not raw prompt content.
- [ ] Keep controls unavailable until its sandbox/capability policy is truly enforced.

## Phase 5: Runtime roster truth
- [ ] Register Antigravity as `adapter-proof-pending` and Codex as `blocked` with evidence.
- [ ] Do not expose controls or terminal claims that their adapters cannot satisfy.
- [ ] Verify all V1 acceptance gates, commit, push, and verify GitHub SHA.
