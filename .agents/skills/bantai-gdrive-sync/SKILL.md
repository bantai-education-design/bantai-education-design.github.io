---
name: bantai-gdrive-sync
description: >-
  Use this skill when referencing, auditing, or syncing Ban.Tai Education Design originals
  (manuscripts, book assets, spreadsheets, PDFs) stored in Google Drive with GitHub repository
  deliverables. Enforces read-only-first Drive access, staging under scratch/, and PR-based review.
---

# Ban.Tai Google Drive to GitHub Safe Sync

Standard workflow for connecting Google Drive originals (正本) with GitHub deliverables in `bantai-education-design.github.io` without risking accidental deletion, permission leaks, or unapproved publication.

## Non-Negotiable Safety Boundaries

1. Default strictly to `gdrive readonly` commands (`ls`, `search`, `export`, `download`, `info`).
2. Never run `gdrive mutate` commands (upload, overwrite, move, delete, share, `empty-trash`) unless the user explicitly requests that specific mutation.
3. Never commit raw Google Drive exports, OAuth tokens, or temporary downloads directly into tracked directories. Stage downloaded references inside `scratch/gdrive/` (ignored by `.gitignore`).
4. Apply Ban.Tai editorial and database rules before preparing any GitHub PR:
   - No markdown bold symbols in Japanese editorial copy.
   - No English text inside generated illustrations or thumbnails.
   - Preserve existing historical records and require explicit human approval before merging to `main`.

## Procedure

### 1. Verify Drive Connection and Inspect Originals (Read-Only)

- Check plugin account status with `list_plugin_accounts` (confirm Google Drive plugin is connected).
- Inspect the target Drive folder or file URL using `gdrive readonly`:

```powershell
gdrive readonly ls <folder-id>
gdrive readonly info <file-id>
```

### 2. Stage Reference Copies Under `scratch/gdrive/`

- Download or export originals into `scratch/gdrive/<topic>/` (never directly over live site files):

```powershell
New-Item -ItemType Directory -Force -Path scratch/gdrive/<topic> | Out-Null
gdrive readonly download <file-id> --out scratch/gdrive/<topic>/
```

- For Google Docs or Sheets, export to Markdown or CSV:

```powershell
gdrive readonly export <file-id> --format markdown --out scratch/gdrive/<topic>/manuscript.md
```

### 3. Transform, Validate, and Prepare PR

- Apply the structured changes on a dedicated feature branch (using `bantai-column-publisher`, `bantai-book-product-page`, or `bantai-db-updater` as appropriate).
- Run `python scripts/weekly_health_audit.py` to validate JSON, sitemap, SEO, GA4, product pages, and guard tests.
- Open a DRAFT PR citing the Drive source file name/ID and last-modified timestamp, and wait for human review before merging.
