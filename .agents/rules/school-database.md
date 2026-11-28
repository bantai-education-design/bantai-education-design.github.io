---
trigger: model_decision
description: Use when editing nationwide school data or school database tools.
---
# School database rules
Applies to `data/school-database/` and `tools/school-database/`.
- Prefer official primary sources and keep a source trace for each data update.
- Preserve historical records; normalize school identifiers and report unmatched entries instead of guessing.
- Validate format, duplicates, 47-prefecture completeness where applicable, and representative values.
- Run focused tests and `python tools/school-database/test_seo_metadata.py` when SEO output is affected.
- Do not modify unrelated files or stage `scratch/` contents.
- Prepare a pull request; merge only after checks and required human approval.
