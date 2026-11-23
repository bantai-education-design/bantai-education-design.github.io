---
name: bantai-book-product-page
description: >-
  Use this skill when creating or updating a book introduction page or product detail page
  on Ban.Tai Education Design (books/, book2/, products/, index.html), including Amazon link
  buttons, pre-launch pending states, and top-page showcase cards.
---

# Ban.Tai Book and Product Page Builder

Standard workflow for adding a new book or educational product introduction page consistent with existing Ban.Tai Education Design pages.

## Procedure

### 1. Inspect Existing Reference Pages

Before editing, read the existing book pages (`books/`, `book2/`) and `index.html` to match:
- Visual hierarchy, typography, card spacing, and responsive CSS classes.
- Header/footer navigation and GA4 tracking snippets.
- Section boundaries on `index.html` so a new book card never intrudes into an adjacent book's showcase block.

### 2. Implement the Page and Links

- Follow all Ban.Tai editorial rules: no markdown bold symbols in copy, no English text in generated illustrations.
- Add the Amazon link button:
  - If the book is currently pending review (申請中), render a clear, accessible Amazon button/badge indicating the pending status without broken links, and make the URL easy to swap in once live.
- Update `index.html` and `books/` or `products/` listings so the new book stands cleanly in its own card/section without overlapping sibling books.

### 3. Validate Locally

```powershell
python scripts/check_ga_tracking.py
python scripts/update_sitemap_for_new_pages.py
python tools/school-database/test_seo_metadata.py
```

### 4. Visual Check and PR Ship

- Verify desktop and mobile layout in the browser (especially card boundaries and button alignment).
- Commit only intended files on a feature branch, open a PR, wait for all CI guards to pass, merge cleanly without `--admin`, and sync local `main`.
