"""Validate the unpublished club activity column's complete text and tables."""

import json
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SLUG = "club-activity-instructor-school-responsibility-20261022"


def test_modal_has_complete_draft():
    columns = json.loads((ROOT / "data/columns.json").read_text(encoding="utf-8"))
    item = next(c for c in columns if c["slug"] == SLUG)
    draft = (ROOT / f"drafts/{SLUG}.md").read_text(encoding="utf-8").strip()
    assert 4000 <= len(draft) <= 5000
    assert item["content"] == draft
    assert item["date"] == "2026.10.22"


def test_article_has_tables_and_corrected_reference():
    class Parser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tables = 0
            self.links = []

        def handle_starttag(self, tag, attrs):
            if tag == "table":
                self.tables += 1
            if tag == "a":
                self.links.append(dict(attrs).get("href"))

    html = (ROOT / f"columns/{SLUG}/index.html").read_text(encoding="utf-8")
    parser = Parser()
    parser.feed(html)
    assert parser.tables == 2
    assert "https://www.mext.go.jp/sports/content/20251226-spt_oripara-000046627_00234.pdf#page=62" in parser.links
    assert "20251215-spt_oripara-000046180_00234.pdf" not in html
