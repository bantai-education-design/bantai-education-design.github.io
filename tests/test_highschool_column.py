"""Keep the approved column available in both the modal and standalone page."""

import json
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SLUG = "highschool-tuition-hidden-costs-20261021"


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def test_modal_contains_complete_approved_draft():
    columns = json.loads((ROOT / "data/columns.json").read_text(encoding="utf-8"))
    article = next(item for item in columns if item["slug"] == SLUG)
    draft = (ROOT / f"drafts/{SLUG}.md").read_text(encoding="utf-8").strip()
    assert len(draft) == 4362
    assert article["content"] == draft


def test_standalone_page_preserves_every_draft_line():
    draft = (ROOT / f"drafts/{SLUG}.md").read_text(encoding="utf-8")
    parser = TextParser()
    parser.feed((ROOT / f"columns/{SLUG}/index.html").read_text(encoding="utf-8"))
    page_text = "".join(parser.parts)
    for line in draft.splitlines():
        line = re.sub(r"^#+\s*", "", line.strip())
        line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
        if line and line != "---":
            assert line in page_text
