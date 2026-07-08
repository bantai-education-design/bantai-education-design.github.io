from __future__ import annotations

import json
from html import escape
from pathlib import Path
from string import Template


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "products.json"
CARD_TEMPLATE_PATH = ROOT / "templates" / "product-card.html"
PAGE_TEMPLATE_PATH = ROOT / "templates" / "products-page.html"
OUTPUT_PATH = ROOT / "products" / "index.html"


def html_text(value: object) -> str:
    return escape(str(value), quote=False)


def html_attr(value: object) -> str:
    return escape(str(value), quote=True)


def indent_block(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in text.splitlines())


def render_badges(product: dict) -> str:
    badges = product.get("badges") or []
    if len(badges) > 1:
        spans = "\n".join(
            f'      <span class="status-badge">{html_text(badge)}</span>' for badge in badges
        )
        return f'    <div class="catalog-badge-row">\n{spans}\n    </div>'
    if badges:
        return f'    <span class="status-badge">{html_text(badges[0])}</span>'
    status = product.get("status")
    if status:
        return f'    <span class="status-badge">{html_text(status)}</span>'
    return ""


def render_media(product: dict) -> str:
    if product.get("usePlaceholder"):
        return '    <div class="catalog-placeholder" aria-hidden="true"></div>'
    image = product.get("image")
    if not image:
        raise ValueError(f"{product['id']}: image is required unless usePlaceholder is true")
    alt = product.get("imageAlt") or product.get("name") or ""
    return f'    <img src="{html_attr(image)}" alt="{html_attr(alt)}">'


def render_features(product: dict) -> str:
    features = product.get("features") or []
    if not features:
        return ""
    items = "\n".join(f"      <li>{html_text(feature)}</li>" for feature in features)
    return f'    <ul class="catalog-feature-list">\n{items}\n    </ul>'


def render_actions(product: dict) -> str:
    primary_label = product.get("primaryActionLabel")
    secondary_label = product.get("secondaryActionLabel")
    category_url = product.get("categoryUrl")
    detail_url = product.get("detailUrl")

    links: list[str] = []
    if primary_label and category_url:
        links.append(
            f'      <a class="secondary-button" href="{html_attr(category_url)}">{html_text(primary_label)}</a>'
        )
    if secondary_label and detail_url:
        links.append(
            f'      <a class="secondary-button" href="{html_attr(detail_url)}">{html_text(secondary_label)}</a>'
        )

    if not links:
        return ""
    if product.get("category") == "featured":
        return '<div class="catalog-card-actions">\n' + "\n".join(links) + "\n    </div>"
    return "\n".join(line[6:] if line.startswith("      ") else line for line in links)


def render_card(product: dict, template: Template) -> str:
    detail_url = product.get("detailUrl")
    card_class = "catalog-card catalog-feature-card" if product.get("category") == "featured" else "catalog-card"
    
    is_flagship_str = "true" if product.get("isFlagship") else "false"
    has_trial_str = "true" if product.get("hasTrial") else "false"
    has_booth_str = "true" if product.get("boothUrl") else "false"
    has_vector_str = "true" if product.get("vectorUrl") else "false"
    status_str = product.get("status") or ""
    features_data_str = " ".join(product.get("features") or [])

    return template.substitute(
        card_class=card_class,
        detail_url=html_attr(detail_url),
        aria_label=html_attr(f"{product['name']}の詳細を見る"),
        media_html=render_media(product),
        badges_html=render_badges(product),
        name=html_text(product["name"]),
        summary=html_text(product["summary"]),
        features_html=render_features(product),
        actions_html=render_actions(product),
        is_flagship=is_flagship_str,
        has_trial=has_trial_str,
        has_booth=has_booth_str,
        has_vector=has_vector_str,
        status=html_attr(status_str),
        features_data=html_attr(features_data_str),
    )


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    products = sorted(data["products"], key=lambda item: item["order"])
    card_template = Template(CARD_TEMPLATE_PATH.read_text(encoding="utf-8"))
    page_template = Template(PAGE_TEMPLATE_PATH.read_text(encoding="utf-8"))

    featured_cards = []
    standard_cards = []
    for product in products:
        rendered = render_card(product, card_template)
        if product["category"] == "featured":
            featured_cards.append(indent_block(rendered, 12))
        else:
            standard_cards.append(indent_block(rendered, 12))

    output = page_template.substitute(
        featured_cards="\n".join(featured_cards),
        standard_cards="\n".join(standard_cards),
    )
    OUTPUT_PATH.write_text(output.rstrip() + "\n", encoding="utf-8", newline="\n")
    print(f"Generated {OUTPUT_PATH.relative_to(ROOT)} from data/products.json")


if __name__ == "__main__":
    main()
