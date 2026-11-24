# Public Link Audit — safe pilot

- Separate workflow: each Tuesday at 08:00 JST, or manual dispatch.
- Only sitemap URLs on the official HTTPS domain are requested.
- Twelve pages per run, with priority entry pages and rotating sample across remaining pages. A success is not a full-site audit. An explicit `--all` is required for a full check.
- Definite 404/410: BROKEN and CI failure. Other responses such as 403, 429, 5xx, or network timeout: UNKNOWN (shown in job summary; do not confuse with healthy).
- Uses GET with a minimal byte range because HEAD is not universally supported. No credentials, modification, third-party crawling, or automated PR merge.
- First validate unit tests and scheduled runner networking. Review UNKNOWN counts and any persistent failures before escalating.
- The online runner's live checks and Antigravity native app remain separate acceptance gates. Keep changes in a draft PR pending human review.
