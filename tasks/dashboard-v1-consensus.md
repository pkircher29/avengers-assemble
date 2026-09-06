# Avengers Dashboard V1 — team consensus and Chuck decision

## Inputs and provenance
- Claude Code / `claude-sonnet-5`: runtime-backed proposal via the visible Claude worker session.
- Tally / `openrouter/free`: runtime-backed proposal from an explicitly no-tool OpenClaw turn. Tally attempted disabled web searches despite the prompt; no external data was returned. This reinforces that tool capability must be enforced by runtime policy, not prompt text alone.
- Codex / `gpt-6-astra`: runtime-backed, read-only text proposal. Tool-using sandbox work remains blocked by Windows process creation.
- Antigravity: installed and model-capable, but its proposal run has not completed reliably; it is recorded as unavailable rather than represented by guessed preferences.
- Chuck: final product decision.

## Consensus
All responding workers converged on: a dashboard claim must be traceable to runtime evidence. Model/effort must distinguish requested from effective; controls need confirmed receipts; missing data must be `unavailable` or `unknown`; work artifacts and tests should accompany claimed completion.

## Chuck decision

### V1
1. Real per-agent roster: lifecycle, current task, last event, blocker, adapter capability state.
2. Structured task/event stream sourced from actual runner records.
3. Token usage shown only when runtime-reported; no prompt-length estimates. Include per-task/per-agent totals and explicit unavailable states.
4. Requested/effective model and reasoning/effort, fallback indication, runtime/schema provenance.
5. Control surface: pause/resume/stop/retry only when a worker advertises a tested control endpoint. Receipts become timeline events.
6. Deliverables and verification panel: artifact path, tests/checks, verification owner, result, and uncertainty.
7. Local-only terminal cards: identify the actual native terminal/PTY owner, process/session handle, visibility status, and a supported open/attach action. Do not label a static log as a terminal.
8. Duplicate/replay guard and recovery evidence visible to Paul.

### Deferred / blocked
- Full embedded interactive terminal panes: requires real PTY/WebSocket input-output bridging, session access control, explicit retention policy, and secret-safety review. Until built, native terminals remain the authoritative full terminal experience.
- Hidden chain-of-thought display: rejected. Show reasoning setting and explicit agent-facing explanation, not private reasoning traces.
- Cross-runtime normalized usage/cost comparisons: blocked until multiple adapters expose compatible reported metadata.
- Team collaboration annotations, transcript search, multi-user RBAC, and incident replay: later.

## V1 acceptance
- Every roster field displays evidence source or `unavailable`.
- A stopped worker under active mission displays `waiting-to-launch`, not active.
- Token values come from response metadata; unknown values are not fabricated.
- A control action has a receipt and observed resulting state before the UI calls it successful.
- Terminal card links only to a real native terminal/session; no fake terminal transcript.
- Dashboard remains loopback-only during V1.
