---
name: bantai-db-updater
description: >-
  Use this skill when updating the Ban.Tai Education Design Nationwide School Database
  (data/school-database/*.json, tools/school-database/) or University Database
  (tools/university-database/), including adding research-designated schools, national music
  contest awards, or bulk multi-prefecture datasets from official primary sources.
---

# Ban.Tai DB Updater

Standard operating procedure for collecting, merging, validating, and shipping factual database updates for the Nationwide School Database and University Database.

## Non-Negotiable Rules

1. Use official primary sources only (MEXT, prefectural/municipal boards of education, AJBA, JCA, NHK, JSECC, official competition result pages). Never guess or invent school names, awards, years, or URLs.
2. Preserve existing records when adding new years or categories. Merge and deduplicate cleanly rather than overwriting prior years.
3. Never stage or delete unrelated untracked files under `scratch/`.
4. Never modify `simple-public-flow.marker`.
5. Never use `--admin` with `gh pr merge`. Always wait for all required GitHub Actions CI checks to pass and perform a normal merge.

## Procedure

### 1. Prepare Branch and Inspect Current State

```powershell
git checkout main
git pull origin main
git checkout -b feature/<descriptive-topic>
```

Check target JSON structure in `data/school-database/{prefecture}.json` and, if applicable, `tools/university-database/music/data/university_music_contests.json`.

### 2. Collect Primary Sources and Build Reproducible Importer

- Store temporary downloaded HTML/PDF/CSV extracts under the conversation scratch directory, not inside tracked repo paths.
- Write or update a reproducible Python importer under `tools/school-database/` (for example, `import_music_contests_past.py`) that:
  - Normalizes full-width/half-width characters, prefecture prefixes, and common school abbreviations.
  - Strictly excludes non-school community ensembles from school/university datasets unless explicitly requested.
  - Deduplicates entries by stable composite keys (e.g., contest + year + division + award).
  - Logs total matched records, unmatched records, and per-prefecture deltas.

### 3. Validate Locally Before Committing

- Run SEO and metadata verification:

```powershell
python tools/school-database/test_seo_metadata.py
```

- If any JavaScript files (`tools/school-database/*/search-*.js` or university DB JS) were edited, syntax-check them with `node --check <file>`.
- Spot-check representative updated records across multiple prefectures and years to confirm no data leakage or duplicate keys.

### 4. Ship via PR and Clean CI Merge

Stage only the intended tracked files (never `git add -A` when untracked `scratch/` files exist):

```powershell
git add data/school-database/*.json tools/school-database/<script>.py
git commit -m "<concise English or Japanese summary>"
git push -u origin feature/<descriptive-topic>
gh pr create --title "<title>" --body "<summary with counts and sources>"
gh pr checks <pr-number> --watch
gh pr merge <pr-number> --merge --delete-branch
git checkout main
git pull origin main
```

### 5. Report Results

Report to the user (without markdown bold symbols):
- PR number and CI merge confirmation.
- Before/after totals (prefectures covered, schools, entries).
- Official primary sources used and clickable file links to scripts/data updated.
