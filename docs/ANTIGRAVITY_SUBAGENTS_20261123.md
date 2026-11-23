# Ban.Tai Database Subagents — pilot design (2026-11-23)

## Objective and boundaries
Three workspace-scoped Antigravity agents provide source verification, integration planning, and independent review. Their configuration files live under `.agents/agents/` and have `subagent: true`, `mainAgent: false`, and read-only `view_file` / `grep_search` tools. This is a **definition-only pilot**. Defining them does not prove the Antigravity application discovered or invoked them.

## Delegation order and artifacts
1. `bantai-source-researcher`: parent supplies official URLs/documents and scope; returns traceable evidence and unresolved items. Do not guess missing fields.
2. `bantai-record-integrator`: parent supplies evidence and existing schema; returns a *proposed* change/deduplication plan with record IDs, historical preservation, and conflict list.
3. `bantai-independent-verifier`: review evidence and change plan independently; return per-gate PASS/FAIL/NOT VERIFIED. Do not equate unexecuted tests with success.

The parent agent owns tool calls for external browsing, local command execution, actual edits, Git/PR, and CI. GitHub Actions remains the merge gate. Do not allow any subagent to alter published records or bypass approval. Use an isolated worktree for any future write-enabled version.

## Trial acceptance protocol
- Verify all three are listed in the Antigravity App Project > Customizations > Custom Agents, or in the CLI `/agents` panel (with workspace root opened).
- In a small, non-sensitive sample, invoke each agent with source evidence and inspect its output. Confirm no files changed.
- Deliberately supply an unverifiable school record and confirm researcher and verifier mark it NOT VERIFIED rather than filling a value.
- Deliberately supply a duplicate institutional name across differing official identifiers and confirm the integrator does not merge them automatically.
- Confirm parent keeps PR merge/publishing under explicit human control.
- Report observed tool usage, tested Antigravity version, and results. No pass claim until performed.

## Later phases
- Introduce explicit source-fetch tools to researcher only after validating exact tool identifiers and permission boundaries.
- Separately evaluate controlled write permissions for integrator with worktree isolation, reproducible importer, focused tests and manual approval.
- Add scheduled jobs and MCP last, after security, privacy, idempotency and operation logging checks.
