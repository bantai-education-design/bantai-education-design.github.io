---
name: bantai-column-publisher
description: >-
  Use this skill when drafting, updating, or publishing columns, weekly education/AI/lesson
  improvement articles, or note curation pages for Ban.Tai Education Design. Enforces editorial
  formatting rules, image asset guidelines, GA4 tracking, and sitemap synchronization.
---

# Ban.Tai Column Publisher

Standard workflow for creating and publishing columns and note curations on `bantai-education-design.github.io`.

## Strict Editorial Guidelines

1. Never include markdown bold syntax (double asterisks) in titles, body text, excerpts, or captions. Express emphasis naturally using Japanese phrasing, corner brackets, or HTML/Markdown headings.
2. Never include English words, Latin alphabets, English logos, or English signatures inside any generated illustration, thumbnail, or diagram. Keep visuals completely textless or pure Japanese typography only.
3. For note article curations, omit personal impressions or one-line subjective commentary. Present curated articles respectfully and objectively as noteworthy educational practices sharing aligned values.

## Procedure

### 1. Branch Setup

```powershell
git checkout main
git pull origin main
git checkout -b feature/column-<topic-or-date>
```

### 2. Generate or Edit Column Content

- Reuse existing automation scripts where applicable:
  - `scripts/weekly_ai_news_column.py`
  - `scripts/weekly_education_news_column.py`
  - `scripts/weekly_lesson_improvement_column.py`
- Ensure top-page (`index.html`), column index (`columns/index.html`), and article detail HTML stay consistent in metadata, dates, thumbnails, and links.

### 3. Run Local Integrity Checks

- Check for forbidden bold markers in edited editorial files.
- Verify Google Analytics (GA4) tracking snippets:

```powershell
python scripts/check_ga_tracking.py
```

- Update `sitemap.xml` when new pages are added:

```powershell
python scripts/update_sitemap_for_new_pages.py
```

- Run SEO metadata tests if shared navigation or database links were touched:

```powershell
python tools/school-database/test_seo_metadata.py
```

### 4. Visual Verification and PR Merge

- For layout or visual changes, verify desktop and mobile rendering before merge.
- Create a PR, wait for all GitHub Actions guards (`ga-tracking-guard`, `sitemap-guard`, etc.) to pass, then request explicit human merge approval, merge normally without `--admin` only after authorization, and sync local `main`.
