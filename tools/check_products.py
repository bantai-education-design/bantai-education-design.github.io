from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "products.json"
OUTPUT_PATH = ROOT / "products" / "index.html"


class ProductPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_card = False
        self.card_depth = 0
        self.current: dict | None = None
        self.cards: list[dict] = []
        self.current_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())

        if tag == "article" and "catalog-card" in classes:
            self.in_card = True
            self.card_depth = 1
            self.current = {
                "name": "",
                "detail_links": [],
                "button_links": [],
                "images": [],
                "badges": [],
            }
            self.cards.append(self.current)
            return

        if self.in_card:
            if tag not in {"br", "img", "input", "meta", "link"}:
                self.card_depth += 1
            if tag == "a":
                href = attr.get("href", "")
                if "catalog-card-hit-area" in classes:
                    self.current["detail_links"].append(href)
                if "secondary-button" in classes:
                    self.current["button_links"].append(href)
            if tag == "img":
                self.current["images"].append(attr.get("src", ""))
            if tag in {"h3", "span"}:
                self.current_tag = tag

    def handle_endtag(self, tag: str) -> None:
        if self.in_card:
            if tag == self.current_tag:
                self.current_tag = None
            if tag not in {"br", "img", "input", "meta", "link"}:
                self.card_depth -= 1
            if tag == "article" and self.card_depth <= 0:
                self.in_card = False
                self.current = None

    def handle_data(self, data: str) -> None:
        if not self.in_card or not self.current:
            return
        text = data.strip()
        if not text:
            return
        if self.current_tag == "h3":
            self.current["name"] += text
        elif self.current_tag == "span":
            self.current["badges"].append(text)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def path_exists_for_url(url: str) -> bool:
    if not url or not url.startswith("/"):
        return False
    path = ROOT / url.lstrip("/")
    if url.endswith("/"):
        return (path / "index.html").exists()
    return path.exists()


def main() -> None:
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON: {exc}")

    products = data.get("products")
    if not isinstance(products, list) or not products:
        fail("products must be a non-empty list")

    ids = [item.get("id") for item in products]
    orders = [item.get("order") for item in products]
    if len(ids) != len(set(ids)):
        fail("duplicate product id")
    if len(orders) != len(set(orders)):
        fail("duplicate product order")

    sorted_products = sorted(products, key=lambda item: item["order"])
    for product in sorted_products:
        if not product.get("name"):
            fail(f"{product.get('id')}: name is required")
        if not product.get("detailUrl"):
            fail(f"{product['id']}: detailUrl is required")
        if product.get("image"):
            image_path = ROOT / product["image"].lstrip("/")
            if not image_path.exists():
                fail(f"{product['id']}: image not found: {product['image']}")
        elif not product.get("usePlaceholder"):
            fail(f"{product['id']}: image or usePlaceholder is required")
        if not path_exists_for_url(product["detailUrl"]):
            fail(f"{product['id']}: detailUrl does not exist: {product['detailUrl']}")
        if product.get("published") and not path_exists_for_url(product["detailUrl"]):
            fail(f"{product['id']}: published detail page missing")

    html = OUTPUT_PATH.read_text(encoding="utf-8")
    if 'href=""' in html or "href=''" in html:
        fail("empty href found in generated HTML")
    if "GENERATED FILE" not in html:
        fail("generated file comment is missing")

    parser = ProductPageParser()
    parser.feed(html)
    if len(parser.cards) != len(sorted_products):
        fail(f"card count mismatch: expected {len(sorted_products)}, found {len(parser.cards)}")

    card_names = [card["name"] for card in parser.cards]
    product_names = [product["name"] for product in sorted_products]
    if card_names != product_names:
        fail(f"product order mismatch: {card_names} != {product_names}")

    for product, card in zip(sorted_products, parser.cards):
        if product["detailUrl"] not in card["detail_links"]:
            fail(f"{product['id']}: card hit area link missing")
        if product["detailUrl"] not in card["button_links"]:
            fail(f"{product['id']}: detail button link missing")

    print(f"OK: {len(sorted_products)} products validated")


if __name__ == "__main__":
    main()
