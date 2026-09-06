# Review quarantine — Tally Dashboard V1 acceptance matrix

Source artifact: `C:/Users/Paul/GITHUB/avengers-openclaw-free-workspace/dashboard-v1-acceptance.md`
Producer: Tally / OpenClaw, 2026-09-06.
Disposition: needs-evidence; not integrated.

## Why
The artifact correctly excludes hidden chain-of-thought and includes useful manual viewport checks. However, it asserts implementation-specific evidence sources and dashboard behavior that this project does not have, including `memory_search`, `memory_get`, `sessions_list`, `session_status`, node descriptions, 30/60-second polling, current-run token cards, and gateway/config control semantics. It also claims a 1200px centered desktop layout and labels truncation behavior that the current `dashboard.html` does not implement.

These are proposals, not verified acceptance facts. Converting them into the dashboard’s V1 contract would violate the team’s evidence rule.

## Salvageable requirements
- Keep hidden chain-of-thought excluded.
- Test responsive layout manually at 320, 768, 1024, and 1440 pixels.
- Represent unavailable/offline data explicitly.
- Define privacy/retention before full terminal capture or transcript replay.

## Required revision from producer
Provide a V1 acceptance matrix that refers only to artifacts and endpoints actually named in `tasks/dashboard-v1-consensus.md` and the current repository. Label proposed later features separately, with no invented data-source/API names.
