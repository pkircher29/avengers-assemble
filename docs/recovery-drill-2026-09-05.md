# Recovery drill evidence

Date: 2026-09-05

## Objective
Prove that the active local group-goal mission and processed request IDs survive a controlled bridge restart without duplicate Claude work.

## Observed sequence

1. Active mission state before stop: `active`, round `1`.
2. Bridge worker PID `13328` was explicitly stopped and verified `process_alive: false`.
3. Loopback console snapshot after stop retained the active mission, round count, and all three processed request IDs.
4. A new visible bridge worker was explicitly launched as PID `35852` and reported `waiting-for-chuck`, retaining the same Claude session ID and effective model `claude-sonnet-5`.
5. A deliberately replayed envelope used the already processed ID `1788651725181622100-145e4590`.
6. The restarted bridge moved that request to `state/rejected/replay-attempt.json` and emitted: `duplicate id: 1788651725181622100-145e4590`.
7. The worker remained `waiting-for-chuck`; no Claude child process was started for the replay.

## Result
Controlled restart and duplicate-rejection behavior passed for the V0 local Chuck–Claude bridge.

## Scope limits
This proves only the local file-backed bridge, local status/mission persistence, and Claude adapter. It does not prove crash resilience under power loss, atomic recovery of a request interrupted during a Claude call, cross-machine recovery, dashboard browser rendering on Paul's physical screen, or behavior of Codex/Antigravity/other adapters.
