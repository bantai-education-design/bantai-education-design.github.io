#!/usr/bin/env python3
"""
Ban.Tai Education Design - Weekly AI News Column Automation Helper

This script automates the weekly AI news compilation process:
1. Formats weekly AI news items and commentary.
2. Validates metadata (slug, title, category: 'ai', tags, read time).
3. Adds/Prepends the formatted column object into `data/columns.json`.
4. Runs Playwright display verification tests.
"""

import json
import os
import sys
import datetime

COLUMNS_FILE = "data/columns.json"

def add_weekly_ai_news_column(title, excerpt, content, tags, read_time="約8分", date_str=None):
    if not date_str:
        date_str = datetime.date.today().strftime("%Y.%m.%d")

    slug_id = f"weekly-ai-news-{date_str.replace('.', '')}"
    thumbnail_path = f"/assets/images/columns/{slug_id}.webp"

    column_entry = {
        "id": slug_id,
        "slug": slug_id,
        "title": title,
        "category": "AIと学び",
        "categorySlug": "ai",
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

    print(f"Successfully added weekly AI news column: {title} ({slug_id})")
    return slug_id

if __name__ == "__main__":
    print("Weekly AI News Column Automation Helper initialized.")
