from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "product-details" / "class-roster.json"
OUTPUT_PATH = ROOT / "products" / "class-roster" / "index.html"
GENERATED_COMMENT = (
    "GENERATED FILE: edit data/product-details/class-roster.json and templates/product-detail.html"
)


REQUIRED_TOP_LEVEL_KEYS = {
    "pageTitle",
    "metaDescription",
    "bodyClass",
    "styleVersion",
    "scriptVersion",
    "productName",
    "productNameParts",
    "englishLabels",
    "badges",
    "heroLeadLines",
    "heroDescription",
    "image",
    "downloadUrl",
    "heroActions",
    "summary",
    "featuresSection",
    "documentsSection",
    "howtoSection",
    "distributionSection",
}


class DetailPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.generated_comment = False
        self.empty_hrefs: list[str] = []
        self.images: list[dict[str, str]] = []
        self.headings: list[str] = []
        self.feature_cards = 0
        self.document_items = 0
        self.howto_steps = 0
        self.in_heading: str | None = None
        self.in_document_list = False
        self.document_depth = 0
        self.in_howto_steps = False
        self.howto_depth = 0

    def handle_comment(self, data: str) -> None:
        if GENERATED_COMMENT in data:
            self.generated_comment = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "a" and not attr.get("href"):
            self.empty_hrefs.append(self.get_starttag_text() or "<a>")
        if tag == "img":
            self.images.append({"src": attr.get("src", ""), "alt": attr.get("alt", "")})
        if tag in {"h1", "h2", "h3"}:
            self.in_heading = tag
            self.headings.append("")
        if tag == "article" and "class-roster-feature-card" in classes:
            self.feature_cards += 1
        if tag == "ul" and "class-roster-document-list" in classes:
            self.in_document_list = True
            self.document_depth = 1
        elif self.in_document_list and tag not in VOID_TAGS:
            self.document_depth += 1
        if self.in_document_list and tag == "li":
            self.document_items += 1
        if tag == "ol" and "class-roster-steps" in classes:
            self.in_howto_steps = True
            self.howto_depth = 1
        elif self.in_howto_steps and tag not in VOID_TAGS:
            self.howto_depth += 1
        if self.in_howto_steps and tag == "li":
            self.howto_steps += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == self.in_heading:
            self.in_heading = None
        if self.in_document_list and tag not in VOID_TAGS:
            self.document_depth -= 1
            if self.document_depth <= 0:
                self.in_document_list = False
        if self.in_howto_steps and tag not in VOID_TAGS:
            self.howto_depth -= 1
            if self.howto_depth <= 0:
                self.in_howto_steps = False

    def handle_data(self, data: str) -> None:
        if self.in_heading and self.headings:
            self.headings[-1] += data.strip()


VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def require_keys(mapping: dict, keys: set[str], label: str) -> None:
    missing = sorted(keys - mapping.keys())
    require(not missing, f"{label}: missing required keys: {', '.join(missing)}")


def validate_json(data: dict) -> None:
    require_keys(data, REQUIRED_TOP_LEVEL_KEYS, "root")
    require(len(data["featuresSection"]["items"]) == 4, "featuresSection.items must have 4 items")
    require(len(data["documentsSection"]["items"]) == 8, "documentsSection.items must have 8 items")
    require(len(data["howtoSection"]["steps"]) == 4, "howtoSection.steps must have 4 steps")
    require(data["image"].get("src"), "image.src is required")
    image_path = ROOT / data["image"]["src"].lstrip("/")
    require(image_path.exists(), f"image file does not exist: {data['image']['src']}")
    download_url = data.get("downloadUrl", "")
    parsed = urlparse(download_url)
    require(parsed.scheme == "https" and parsed.netloc, "downloadUrl must be an absolute HTTPS URL")
    require(download_url.endswith(".zip"), "downloadUrl must point to the release ZIP file")


def validate_html(data: dict, html: str) -> None:
    parser = DetailPageParser()
    parser.feed(html)

    require(parser.generated_comment, "generated file comment is missing")
    require(not parser.empty_hrefs, "empty href found")
    require(data["productName"] in "".join(parser.headings), "product heading is missing")
    require(parser.feature_cards == 4, f"feature card count mismatch: {parser.feature_cards}")
    require(parser.document_items == 8, f"document item count mismatch: {parser.document_items}")
    require(parser.howto_steps == 4, f"howto step count mismatch: {parser.howto_steps}")
    expected_image = data["image"]["src"]
    require(any(image["src"] == expected_image for image in parser.images), "configured image is missing")
    require(data["downloadUrl"] in html, "download URL is missing from generated HTML")


def main() -> None:
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON: {exc}")

    validate_json(data)
    html = OUTPUT_PATH.read_text(encoding="utf-8")
    validate_html(data, html)
    print("OK: class roster detail page validated")


if __name__ == "__main__":
    main()
