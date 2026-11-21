from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path
from string import Template

from ga4_snippet import inject_ga4


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "products.json"
CARD_TEMPLATE_PATH = ROOT / "templates" / "product-card.html"
PAGE_TEMPLATE_PATH = ROOT / "templates" / "products-page.html"
OUTPUT_PATH = ROOT / "products" / "index.html"
SITE_ORIGIN = "https://bantai-education-design.github.io"


def html_text(value: object) -> str:
    return escape(str(value), quote=False)


def html_attr(value: object) -> str:
    return escape(str(value), quote=True)


def indent_block(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in text.splitlines())


def render_recommend(product: dict) -> str:
    recommendation = product.get("recommendation")
    if recommendation:
        return f'    <span class="recommend-badge">{html_text(recommendation)}</span>'
    return ""


def render_badges(product: dict) -> str:
    status = product.get("status")
    if status:
        return f'    <span class="status-badge">{html_text(status)}</span>'
    return ""


def render_target_users(product: dict) -> str:
    users = product.get("targetUsers") or []
    if not users:
        return ""
    tags = "".join(f'<span class="user-tag">{html_text(u)}</span>' for u in users)
    return f'    <div class="target-users-row">{tags}</div>'


def render_media(product: dict) -> str:
    if product.get("usePlaceholder"):
        return '    <div class="catalog-placeholder" aria-hidden="true"></div>'
    image = product.get("image")
    if not image:
        raise ValueError(f"{product['id']}: image is required unless usePlaceholder is true")
    alt = product.get("imageAlt") or product.get("name") or ""
    return f'    <img src="{html_attr(image)}" alt="{html_attr(alt)}" class="card-img">'


def link_attrs(url: str) -> str:
    """ZIPは直接ダウンロード、外部サイトは別タブ、HP内のページはそのまま開く。"""
    if url.endswith(".zip"):
        return " download"
    if url.startswith("http") and not url.startswith(SITE_ORIGIN):
        return ' target="_blank" rel="noopener noreferrer"'
    return ""


def free_action(product: dict) -> tuple[str, str] | None:
    """無料の入り口。試用版・モニター版・無料ツールが実際に手に入る場所へ案内する。
    trialDownloadUrl（公式HPのZIP）を優先し、なければ trialUrl（BOOTHの0円体験版やVectorなど、確認済みの配布先）。
    購入ページを試用の代わりにはしない（trialUrl はデータで明示したものだけを使う）。"""
    trial = product.get("trialDownloadUrl") or product.get("trialUrl")
    if trial:
        return "10日間無料で試す", trial
    if product.get("status") == "無料ツール":
        url = product.get("webUrl") or product.get("downloadUrl")
        if url:
            return "無料で使う", url
    if product.get("monitorUrl"):
        return "無料モニター版を入手", product["monitorUrl"]
    return None


def purchase_action(product: dict) -> tuple[str, str] | None:
    """購入先。BOOTHの商品が見つからないもの（boothActive が false）は出さない。書籍はAmazon。"""
    if product.get("boothUrl") and product.get("boothActive", True):
        return "BOOTHで購入する", product["boothUrl"]
    if product.get("amazonUrl"):
        return "Amazonで購入する", product["amazonUrl"]
    return None


def render_actions(product: dict) -> str:
    """全製品同じ並び：①詳しく見る（黒）②無料の入り口（緑）③購入（金）。縦に並べる。
    一時休止中は①だけ。"""
    links: list[str] = []
    detail_url = product.get("detailUrl")
    if detail_url:
        links.append(f'      <a class="catalog-btn catalog-btn-secondary secondary-button" href="{html_attr(detail_url)}">詳しく見る</a>')

    if product.get("status") != "一時休止中":
        free = free_action(product)
        if free:
            label, url = free
            links.append(f'      <a class="catalog-btn catalog-btn-free" href="{html_attr(url)}"{link_attrs(url)}>{html_text(label)}</a>')
        buy = purchase_action(product)
        if buy:
            label, url = buy
            links.append(f'      <a class="catalog-btn catalog-btn-primary" href="{html_attr(url)}"{link_attrs(url)}>{html_text(label)}</a>')

    if not links:
        return ""
    return '<div class="catalog-card-actions is-stacked">\n' + "\n".join(links) + "\n    </div>"


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
        recommend_html=render_recommend(product),
        badges_html=render_badges(product),
        target_users_html=render_target_users(product),
        name=html_text(product["name"]),
        summary=html_text(product["summary"]),
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
    free = sum(1 for p in products if p.get("status") == "無料ツール")
    preparing = sum(1 for p in products if p.get("status") in ("公開準備中", "準備中"))
    paused = sum(1 for p in products if p.get("status") == "一時休止中")
    monitor = sum(1 for p in products if p.get("status") == "モニター募集中")

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
    output = inject_ga4(output)
    OUTPUT_PATH.write_text(output.rstrip() + "\n", encoding="utf-8", newline="\n")
    print(f"Generated {OUTPUT_PATH.relative_to(ROOT)} from data/products.json")

    # Update home page stats
    update_index_html_stats(products)


if __name__ == "__main__":
    main()
