# AGENTS.md — 全国学校データベース

Apply the Ban.Tai Standard AGENTS.md v1.0 plus these rules to `tools/school-database/` work.

## Mission

Maintain a trustworthy, easy-to-use nationwide school database. Accuracy and source traceability take priority over speed.

## Source policy

- Prefer official national, prefectural, municipal, school, or other authoritative primary sources.
- Never fabricate or infer official school names, addresses, postal codes, school types, establishment types, URLs, or counts.
- Keep source dates/basis dates when the dataset tracks them.
- Treat unverified values as unverified rather than filling them by guesswork.

## Data changes

For prefecture additions or bulk updates, validate at minimum where applicable:

- total record count and school-type subtotals
- duplicate records/identifiers
- required-field missing values
- municipality and establishment classifications
- representative official school names
- address/postal-code consistency
- JSON/CSV/schema validity

Do not silently change inclusion/exclusion criteria. Document exclusions such as closed/suspended schools or non-target institution types.

## UI and regression

Changes to shared portal/database CSS or JavaScript must be checked against the target prefecture and representative existing prefectures. Verify search, filters, result count, official-name display, map/official links, copy/export functions when affected, and responsive layouts.

Do not use dummy statistics or mismatched-year population figures as if they were verified current facts.

## URLs

Never construct an official URL from a pattern unless the project explicitly defines that pattern as authoritative. Verify external destinations before adding them.

## Completion

A prefecture/data task is not done merely because records were generated. The generated output, representative records, counts, UI rendering, and relevant regressions must be checked. Clearly report source basis dates and anything not verified.