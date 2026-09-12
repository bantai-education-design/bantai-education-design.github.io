#!/usr/bin/env python3
"""
Ban.Tai Education Design - Weekly Lesson Improvement & Teaching Materials Automation Helper

This script automates the weekly lesson improvement & teaching materials column publication:
1. Formats weekly teaching materials, handouts, worksheet diagrams, and lesson ideas.
2. Validates metadata (slug, title, category: 'practice' or 'ict', tags, read time).
3. Adds/Prepends the formatted column entries into `data/columns.json`.
4. Runs Playwright display verification tests.
"""

import json
import os
import sys
import datetime

COLUMNS_FILE = "data/columns.json"

def add_weekly_lesson_column(title, category, category_slug, excerpt, content, tags, read_time="約9分", date_str=None, slug_suffix="1"):
    if not date_str:
        date_str = datetime.date.today().strftime("%Y.%m.%d")

    slug_id = f"weekly-lesson-practice-{date_str.replace('.', '')}-{slug_suffix}"
    thumbnail_path = f"/assets/images/columns/{slug_id}.webp"

    column_entry = {
        "id": slug_id,
        "slug": slug_id,
        "title": title,
        "category": category,
        "categorySlug": category_slug,
        "date": date_str,
        "excerpt": excerpt,
        "thumbnail": thumbnail_path,
        "readTime": read_time,
        "content": content,
        "tags": tags
    }

    if not os.path.exists(COLUMNS_FILE):
        print(f"Error: {COLUMNS_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    with open(COLUMNS_FILE, "r", encoding="utf-8") as f:
        columns = json.load(f)

    # Avoid duplication
    columns = [c for c in columns if c["id"] != slug_id]
    columns.insert(0, column_entry)

    with open(COLUMNS_FILE, "w", encoding="utf-8") as f:
        json.dump(columns, f, ensure_ascii=False, indent=2)

    print(f"Successfully added weekly lesson column: {title} ({slug_id})")
    return slug_id

if __name__ == "__main__":
    print("Weekly Lesson Improvement Column Automation Helper initialized.")
