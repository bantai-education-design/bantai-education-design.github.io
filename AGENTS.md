# Ban.Tai Education Design — Standard AGENTS.md

Version: 1.0

This is the canonical common policy for AI coding agents working in this repository. Directory-level `AGENTS.md` files may add stricter, more specific rules. For other Ban.Tai repositories, copy/adapt this common core into the repository-local `AGENTS.md` so the agent can read it without depending on external context.

## Priority

1. Correctness
2. Usability
3. Preservation of existing behavior
4. Data/source reliability
5. Maintainability
6. Visual quality
7. Speed

Never trade correctness, verification, or existing behavior for speed.

## Before editing

- Read the applicable `AGENTS.md` and related README/docs.
- Inspect the current branch, working state, and existing implementation.
- Preserve unrelated user changes.
- Understand the cause and affected area before modifying code.

## No guessing

Never invent URLs, paths, APIs, factual records, addresses, postal codes, statistics, commit IDs, PR numbers, or test results. Investigate first. If something cannot be verified, label it unverified.

## Data quality

Prefer official primary sources for schools, universities, publishers, addresses, and other factual datasets. Do not fill missing facts by inference. For bulk changes, validate counts, duplicates, missing values, format, representative records, and source agreement where practical.

## Code quality

Prefer simple, readable, focused code. Avoid unnecessary abstraction, deep nesting, oversized functions, duplicated logic, unexplained magic values, and unrelated refactors. Follow established project patterns unless there is a clear reason not to.

Comments should explain non-obvious reasons, not restate code.

## Existing behavior

A fix must not break unrelated working features. Treat changes to shared CSS, JavaScript, components, schemas, and data pipelines as regression risks and test representative consumers.

## Bug fixes

When practical: reproduce the defect, demonstrate failure, implement the smallest sound fix, verify success, and run relevant regression checks. Do not report symptom suppression as a completed fix.

## UI / UX

Ban.Tai products should be understandable to non-technical education users: readable, approachable, visually clear, and easy to operate. Avoid text-heavy, bureaucratic, cramped, or decorative-but-unreadable interfaces.

For UI changes, inspect rendered output when the environment permits. Check desktop and mobile where applicable. Code compilation alone is not visual verification.

## Images

Respect original user-provided photographs. Do not replace real photographs with AI reconstructions unless explicitly requested. Preserve originals where the project supports them; use crop, position, rotation/tilt correction, resizing, and minimal tonal correction when appropriate.

## Tests and validation

Run the most relevant focused checks, then appropriate regression/build/lint/type checks. For UI changes, inspect the browser output when possible. For data changes, validate the resulting data rather than only the generator code.

Never claim a check was run unless it was actually run.

## Git and pull requests

Before committing, inspect the diff and exclude unrelated or temporary files. Keep commits focused and explain what changed and why.

Do not merge automatically when user review, visual approval, or explicit merge authorization is required. A PR is not proof of completion.

## Definition of Done

Work is complete only when requested behavior is implemented, relevant checks pass, regressions are considered, UI/data are verified when relevant, documentation is updated when needed, Git state is understood, and remaining risks or unverified items are reported.

Distinguish clearly between: implemented, verified, unverified, and remaining work.

## Long sessions and context dilution

Re-read the applicable `AGENTS.md` before major implementation/refactoring, before final verification, after repeated failures, when quality declines, when requirements appear to drift, or whenever the user requests it. After rereading, check current work against the rules.

## Improve the rules from recurring failures

If the same class of mistake can recur, consider adding a concise preventive rule to the relevant `AGENTS.md`. Do not turn one-off task details into permanent policy. Keep agent instructions short enough to remain actionable.

## Project-specific rules

Repository or directory-level `AGENTS.md` files should add concrete setup, build, test, deploy, data-validation, architecture, and project-specific safety rules. The closest applicable instructions should be the most specific.

## Final report

For substantial work, report what changed, why, main files, tests/checks and results, UI verification when relevant, Git/commit/PR state, deployment state when relevant, and unresolved or unverified items.

## Core rule

Verify rather than guess. Prefer the smallest sound change. A code change is not completion; working, verified behavior is.
