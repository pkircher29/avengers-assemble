# OpenClaw free-model probe — 2026-09-05

## Profile
`openclaw --profile avengers-free`

## Credential handling
The OpenRouter key remains only in `C:/Users/Paul/.hermes/.env`. It was parsed transiently into the OpenClaw process environment for scanning/probes and was not copied to the profile config, project, agent Soul, logs, or backup material.

## Live scan
`openclaw models scan` performed live completion/tool probes against the current OpenRouter free catalog.

Tool-capable candidates that returned successful probes included:
- `openrouter/poolside/laguna-xs-2.1:free`
- `openrouter/google/gemma-4-26b-a4b-it:free`
- `openrouter/minimax/minimax-m3:free`
- `openrouter/liquid/lfm-2.5-2.6b:free`
- `openrouter/google/gemma-4-31b-it:free`
- `openrouter/inclusionai/ling-3.0-flash-sante:free`
- `openrouter/openrouter/free`

## Runtime selection
The first direct probe of `poolside/laguna-xs-2.1:free` subsequently received an upstream `429` rate-limit response. It remains a candidate, not a reliable default. The profile default is therefore `openrouter/openrouter/free`, which passed a direct local OpenClaw inference probe returning exactly `OPENCLAW_FREE_OK`.

Fallback candidates are recorded in the profile config. Free-tier availability is transient: every launch should visibly report model/provider failure and fall back only through the configured list; no model is labeled permanently healthy based on this one scan.

## Remaining lifecycle limits
This proves profile config and a harmless inference route. It does not grant operational status: name selection after Soul review, isolated worktree capability test, private backup remote + verified SHA, daily backup schedule, and a bounded real team task remain required.
