# Codex adapter repair gate

Status: blocked for tool-using work; text-only read-only invocation passes.

## Verified
- Codex CLI `0.153.2`, ChatGPT auth, model `gpt-6-astra`.
- `codex exec --sandbox read-only --ephemeral 'Reply with exactly: CODEX_SANDBOX_OK. Do not use tools.'` succeeded and returned `CODEX_SANDBOX_OK`.
- A bounded repository review previously failed when Codex attempted its first sandboxed child process: `CreateProcessAsUserW failed: 5 (Access is denied.)`.

## Codex Doctor evidence
- Microsoft Defender may interfere with Codex; exclusions for Codex and helper executables are not verified.
- Expected paths include the signed Codex app, `codex.exe`, `codex-windows-sandbox-setup.exe`, `codex-command-runner.exe`, and `codex-code-mode-host.exe`.
- Codex `0.153.4` is available; current is `0.153.2`.
- The worktree is not on a Windows Dev Drive; this is a performance note, not the confirmed failure cause.

## Required repair proof
1. Apply a user-approved Defender/Controlled Folder Access exemption or other supported repair path; do not disable Defender broadly.
2. Update Codex only after preserving/confirming auth state.
3. Re-run a read-only repository inspection that necessarily invokes a sandboxed command.
4. Verify it reads the isolated worktree, returns output, and makes no changes.
5. Only then add Codex to the live worker roster.
