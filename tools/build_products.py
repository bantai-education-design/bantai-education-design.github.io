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


def render_recommend(product: dict) -> str:
    recommendation = product.get("recommendation")
    if recommendation:
        return f'    <span class="recommend-badge">{html_text(recommendation)}</span>'
    return ""


def render_badges(product: dict) -> str:
    # 絵日記・観察カードは一時除外のため旧互換処理
    if product.get("id") == "observation-card":
        badges = product.get("badges") or []
        if badges:
            return f'    <span class="status-badge">{html_text(badges[0])}</span>'
        return ""

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


def render_actions(product: dict) -> str:
    # 絵日記・観察カード作成メーカーは今回は統一対象から一時除外（既存の3ボタンを維持）
    if product.get("id") == "observation-card":
        trial_download_url = product.get("trialDownloadUrl")
        booth_url = product.get("boothUrl")
        detail_url = product.get("detailUrl")
        links: list[str] = []
        if trial_download_url:
            links.append(f'      <a class="catalog-btn catalog-btn-primary" href="{html_attr(trial_download_url)}" download>試用版をダウンロード</a>')
        if booth_url:
            links.append(f'      <a class="catalog-btn catalog-btn-primary" href="{html_attr(booth_url)}" target="_blank" rel="noopener noreferrer">BOOTHでライセンスを購入</a>')
        if detail_url:
            links.append(f'      <a class="catalog-btn catalog-btn-secondary secondary-button" href="{html_attr(detail_url)}">詳細を見る</a>')
        return '<div class="catalog-card-actions">\n' + "\n".join(links) + "\n    </div>"

    status = product.get("status")
    detail_url = product.get("detailUrl")
    links: list[str] = []

    # 1. 第1ボタン: 詳しく見る
    if detail_url:
        links.append(f'      <a class="catalog-btn catalog-btn-secondary secondary-button" href="{html_attr(detail_url)}">詳しく見る</a>')

    # 2. 第2ボタン (状態に応じて決定)
    if status == "一時休止中":
        pass  # 一時休止中は「詳しく見る」の1ボタンのみ
    elif status == "モニター募集中":
        monitor_url = product.get("monitorUrl") or "https://docs.google.com/forms/d/e/1FAIpQLSeIM0bNoL4mKfycoYLAkC11ajGvjRQ3NsX4cB_Y5lP0w840ww/viewform"
        links.append(f'      <a class="catalog-btn catalog-btn-primary" href="{html_attr(monitor_url)}" target="_blank" rel="noopener noreferrer">モニターに参加する</a>')
    elif status == "10日間無料体験":
        trial_dl = product.get("trialDownloadUrl")
        booth = product.get("boothUrl")
        vector = product.get("vectorUrl")
        action_url = trial_dl or booth or vector
        if trial_dl:
            links.append(f'      <a class="catalog-btn catalog-btn-primary" href="{html_attr(action_url)}" download>10日間無料で試す</a>')
        elif action_url:
            links.append(f'      <a class="catalog-btn catalog-btn-primary" href="{html_attr(action_url)}" target="_blank" rel="noopener noreferrer">10日間無料で試す</a>')
    elif status == "無料ツール":
        web_url = product.get("webUrl")
        download_url = product.get("downloadUrl")
        if web_url:
            links.append(f'      <a class="catalog-btn catalog-btn-primary" href="{html_attr(web_url)}">無料で使う</a>')
        elif download_url:
            dl_attr = " download" if download_url.startswith("/") or download_url.endswith(".zip") else ""
            rel_attr = ' target="_blank" rel="noopener noreferrer"' if not dl_attr else ""
            links.append(f'      <a class="catalog-btn catalog-btn-primary" href="{html_attr(download_url)}"{dl_attr}{rel_attr}>無料で使う</a>')
    elif status == "販売中":
        booth = product.get("boothUrl")
        if booth:
            links.append(f'      <a class="catalog-btn catalog-btn-primary" href="{html_attr(booth)}" target="_blank" rel="noopener noreferrer">BOOTHで購入する</a>')

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
    OUTPUT_PATH.write_text(output.rstrip() + "\n", encoding="utf-8", newline="\n")
    print(f"Generated {OUTPUT_PATH.relative_to(ROOT)} from data/products.json")

    # Update home page stats
    update_index_html_stats(products)


if __name__ == "__main__":
    main()
