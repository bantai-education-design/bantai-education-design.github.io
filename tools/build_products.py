from __future__ import annotations

import json
import re
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
    status = product.get("status")
    booth_url = product.get("boothUrl")
    vector_url = product.get("vectorUrl")
    note_url = product.get("noteUrl")
    download_url = product.get("downloadUrl")
    detail_url = product.get("detailUrl")
    category_url = product.get("categoryUrl")
    primary_label = product.get("primaryActionLabel")
    secondary_label = product.get("secondaryActionLabel")

    links: list[str] = []

    # 1. 一時休止中 または 公開準備中 の場合は、非活性ステータス表示を先頭に配置 (外部リンクは出力しない)
    if status == "一時休止中":
        links.append('      <span class="catalog-btn catalog-btn-disabled">現在一時休止中</span>')
    elif status in ("公開準備中", "準備中"):
        links.append('      <span class="catalog-btn catalog-btn-disabled">公開準備中</span>')
    else:
        # 2. 無料ダウンロード
        if status == "無料" and download_url:
            links.append(
                f'      <a class="catalog-btn catalog-btn-primary" href="{html_attr(download_url)}" download>無料でダウンロードする</a>'
            )
        
        # 3. BOOTH
        if booth_url:
            links.append(
                f'      <a class="catalog-btn catalog-btn-primary" href="{html_attr(booth_url)}" target="_blank" rel="noopener noreferrer">BOOTHで購入・ダウンロードする</a>'
            )
            
        # 4. Vector
        if vector_url:
            links.append(
                f'      <a class="catalog-btn catalog-btn-primary" href="{html_attr(vector_url)}" target="_blank" rel="noopener noreferrer">Vectorからダウンロードする</a>'
            )

        # 5. note
        if note_url:
            links.append(
                f'      <a class="catalog-btn catalog-btn-note" href="{html_attr(note_url)}" target="_blank" rel="noopener noreferrer">noteで紹介記事を読む</a>'
            )

    # 6. 分野を見る / 詳細を見る (既存の導線を維持)
    if primary_label and category_url:
        links.append(
            f'      <a class="catalog-btn catalog-btn-secondary secondary-button" href="{html_attr(category_url)}">{html_text(primary_label)}</a>'
        )
    if secondary_label and detail_url:
        links.append(
            f'      <a class="catalog-btn catalog-btn-secondary secondary-button" href="{html_attr(detail_url)}">{html_text(secondary_label)}</a>'
        )

    if not links:
        return ""
    
    return '<div class="catalog-card-actions">\n' + "\n".join(links) + "\n    </div>"


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


def update_index_html_stats(products: list) -> None:
    total = len(products)
    sales = sum(1 for p in products if p.get("status") in ("販売中", "10日間無料体験"))
    free = sum(1 for p in products if p.get("status") == "無料")
    preparing = sum(1 for p in products if p.get("status") in ("公開準備中", "準備中"))
    paused = sum(1 for p in products if p.get("status") == "一時休止中")
    monitor = sum(1 for p in products if p.get("status") == "主力製品")

    index_path = ROOT / "index.html"
    if not index_path.exists():
        print(f"Error: index.html not found at {index_path}")
        return

    html = index_path.read_text(encoding="utf-8")

    def replace_placeholder(content: str, tag: str, value: int) -> str:
        pattern = rf"(<!--\s*{tag}\s*-->).*?(<!--\s*/{tag}\s*-->)"
        return re.sub(pattern, rf"\g<1>{value}\g<2>", content)

    html = replace_placeholder(html, "STAT_TOTAL", total)
    html = replace_placeholder(html, "STAT_SALES", sales)
    html = replace_placeholder(html, "STAT_MONITOR", monitor)
    html = replace_placeholder(html, "STAT_FREE", free)
    html = replace_placeholder(html, "STAT_PREPARING", preparing)
    html = replace_placeholder(html, "STAT_PAUSED", paused)

    index_path.write_text(html, encoding="utf-8", newline="\n")
    print(f"Updated index.html stats (Total: {total}, Sales: {sales}, Monitor: {monitor}, Free: {free}, Preparing: {preparing}, Paused: {paused})")


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

    # Update home page stats
    update_index_html_stats(products)


if __name__ == "__main__":
    main()

