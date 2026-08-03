#!/usr/bin/env python3
"""Generate/refresh SEO metadata for the 47 prefecture pages and the portal,
directly from data already in this repository — never hand-typed — so that
future data changes (school count, new prefecture, population update) only
require re-running this script.

Currently covers:
  - Phase 1: meta description school-count fix (was drifting out of sync
    with prefecture-metadata.json, independently of the "収録範囲" table
    fixed by enrich_prefecture_pages.py in PR #100 — this is a *different*
    location in <head> that PR #100's script never touched).
  - Phase 2: <link rel="canonical"> for all 47 pages (東京都 already had
    one from PR #101; this extends the same pattern to the rest).
  - Phase 2: sitemap.xml regenerated to include all 47 prefecture pages
    (previously only 7 were listed) plus the portal.
  - Phase 3: JSON-LD (BreadcrumbList + CollectionPage per prefecture page;
    WebSite + BreadcrumbList on the portal only).
  - Phase 4: visual breadcrumb nav, and an internal-links section (land-
    adjacent prefectures + other prefectures in the same region) on each
    of the 47 pages.

Re-running this script is idempotent."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFECTURE_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-metadata.json"
CARD_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
PAGE_DIR = ROOT / "tools" / "school-database"
PORTAL_PAGE = PAGE_DIR / "index.html"
SITEMAP_PATH = ROOT / "sitemap.xml"
SITE_ORIGIN = "https://bantai-education-design.github.io"

# 陸続きの隣接都道府県（地理的事実、海を挟むもの・離島は除く）。
# 出典: https://www.benricho.org/chimei/rinsetsuken/ で長野8県・埼玉/岐阜7県・
# 長崎1県・北海道/沖縄0県という代表的な事実を確認済み。全件は
# test_seo_metadata.py の対称性チェック（AがBの隣接ならBもAの隣接）で検証する。
PREFECTURE_ADJACENCY: dict[str, list[str]] = {
    "hokkaido": [],
    "aomori": ["iwate", "akita"],
    "iwate": ["aomori", "akita", "miyagi"],
    "akita": ["aomori", "iwate", "miyagi", "yamagata"],
    "miyagi": ["iwate", "akita", "yamagata", "fukushima"],
    "yamagata": ["akita", "miyagi", "fukushima", "niigata"],
    "fukushima": ["miyagi", "yamagata", "niigata", "gunma", "tochigi", "ibaraki"],
    "ibaraki": ["fukushima", "tochigi", "saitama", "chiba"],
    "tochigi": ["fukushima", "gunma", "saitama", "ibaraki"],
    "gunma": ["fukushima", "tochigi", "saitama", "niigata", "nagano"],
    "saitama": ["gunma", "tochigi", "ibaraki", "chiba", "tokyo", "yamanashi", "nagano"],
    "chiba": ["ibaraki", "saitama", "tokyo"],
    "tokyo": ["saitama", "chiba", "kanagawa", "yamanashi"],
    "kanagawa": ["tokyo", "yamanashi", "shizuoka"],
    "niigata": ["yamagata", "fukushima", "gunma", "nagano", "toyama"],
    "toyama": ["niigata", "nagano", "gifu", "ishikawa"],
    "ishikawa": ["toyama", "gifu", "fukui"],
    "fukui": ["ishikawa", "gifu", "shiga", "kyoto"],
    "yamanashi": ["saitama", "tokyo", "kanagawa", "shizuoka", "nagano"],
    "nagano": ["gunma", "saitama", "yamanashi", "shizuoka", "aichi", "gifu", "toyama", "niigata"],
    "gifu": ["toyama", "ishikawa", "fukui", "nagano", "aichi", "mie", "shiga"],
    "shizuoka": ["kanagawa", "yamanashi", "nagano", "aichi"],
    "aichi": ["nagano", "gifu", "shizuoka", "mie"],
    "mie": ["aichi", "gifu", "shiga", "kyoto", "nara", "wakayama"],
    "shiga": ["fukui", "gifu", "mie", "kyoto"],
    "kyoto": ["fukui", "shiga", "mie", "nara", "osaka", "hyogo"],
    "osaka": ["kyoto", "nara", "wakayama", "hyogo"],
    "hyogo": ["kyoto", "osaka", "okayama", "tottori"],
    "nara": ["mie", "kyoto", "osaka", "wakayama"],
    "wakayama": ["mie", "nara", "osaka"],
    "tottori": ["hyogo", "okayama", "shimane"],
    "shimane": ["tottori", "hiroshima", "yamaguchi"],
    "okayama": ["hyogo", "tottori", "hiroshima"],
    "hiroshima": ["shimane", "okayama", "yamaguchi"],
    "yamaguchi": ["shimane", "hiroshima", "fukuoka"],
    "tokushima": ["kagawa", "ehime", "kochi"],
    "kagawa": ["tokushima", "ehime"],
    "ehime": ["kagawa", "tokushima", "kochi"],
    "kochi": ["tokushima", "ehime"],
    "fukuoka": ["yamaguchi", "saga", "kumamoto", "oita"],
    "saga": ["fukuoka", "nagasaki", "kumamoto"],
    "nagasaki": ["saga"],
    "kumamoto": ["fukuoka", "saga", "oita", "miyazaki", "kagoshima"],
    "oita": ["fukuoka", "kumamoto", "miyazaki"],
    "miyazaki": ["kumamoto", "oita", "kagoshima"],
    "kagoshima": ["kumamoto", "miyazaki"],
    "okinawa": [],
}


def format_number(n: int) -> str:
    return f"{n:,}"


def fix_meta_description_counts(prefecture_metadata: list[dict]) -> list[str]:
    """Replace the stale school-count figure inside <meta name="description">
    with the current total from prefecture-metadata.json. Only touches the
    number itself — the school-type enumeration and all other wording in
    the description is already prefecture-specific and correct, so it is
    left untouched."""
    changed = []
    for meta in prefecture_metadata:
        slug = meta["slug"]
        total = meta["total"]
        page_path = PAGE_DIR / slug / "index.html"
        if not page_path.is_file():
            continue
        html = page_path.read_text(encoding="utf-8")

        desc_match = re.search(r'(<meta name="description" content="[^"]*?合計\s*)[\d,]+(\s*校・園[^"]*")', html)
        if not desc_match:
            # 東京都のように「合計」件数をdescriptionに含まない文面もある。対象外。
            continue

        current_value = re.search(r"合計\s*([\d,]+)\s*校・園", desc_match.group(0)).group(1)
        expected_value = format_number(total)
        if current_value == expected_value:
            continue

        new_html = html[: desc_match.start()] + desc_match.group(1) + expected_value + desc_match.group(2) + html[desc_match.end() :]
        page_path.write_text(new_html, encoding="utf-8")
        changed.append(f"{slug}: {current_value} -> {expected_value}")
    return changed


def fix_portal_description(prefecture_metadata: list[dict]) -> bool:
    """ポータルページのdescriptionは、対応県が少なかった時期に手で列挙した
    文面（一部県のみ・レガシー件数を含む）のまま残っていた。47都道府県対応・
    現行合計件数を反映した文面へ差し替える。"""
    national_total = sum(m["total"] for m in prefecture_metadata)
    assert len(prefecture_metadata) == 47, "47都道府県データが揃っていません"

    html = PORTAL_PAGE.read_text(encoding="utf-8")
    new_description = (
        f"学校封筒印刷・宛名作成に使える、全国47都道府県対応の学校データベースポータルです"
        f"（掲載校・園数 合計{format_number(national_total)}件）。都道府県を選択して、"
        f"学校名・住所・電話番号での検索、宛名コピー、CSV出力、Google Maps連携がご利用いただけます。"
    )
    match = re.search(r'<meta name="description" content="[^"]*">', html)
    if not match:
        raise ValueError("ポータルページのdescriptionが見つかりません")
    if f"合計{format_number(national_total)}件" in match.group(0):
        return False

    new_tag = f'<meta name="description" content="{new_description}">'
    html = html[: match.start()] + new_tag + html[match.end() :]
    PORTAL_PAGE.write_text(html, encoding="utf-8")
    return True


def ensure_canonical_tags(card_payload: dict) -> list[str]:
    """Insert <link rel="canonical"> right after the last <link rel="stylesheet">
    in <head> for any of the 47 pages that don't already have one (東京都 already
    does, from PR #101)."""
    added = []
    for pref in card_payload["prefectures"]:
        slug = pref["prefecture_code"]
        url_path = pref["url"]
        page_path = PAGE_DIR / slug / "index.html"
        if not page_path.is_file():
            continue
        html = page_path.read_text(encoding="utf-8")
        if "rel=\"canonical\"" in html:
            continue

        canonical_tag = f'  <link rel="canonical" href="{SITE_ORIGIN}{url_path}">\n'
        stylesheet_matches = list(re.finditer(r'^  <link rel="stylesheet"[^\n]*\n', html, re.M))
        if not stylesheet_matches:
            raise ValueError(f"{slug}: stylesheet linkが見つかりません")
        insert_at = stylesheet_matches[-1].end()
        html = html[:insert_at] + canonical_tag + html[insert_at:]
        page_path.write_text(html, encoding="utf-8")
        added.append(slug)
    return added


JSON_LD_START = "  <!-- json-ld:start -->\n"
JSON_LD_END = "  <!-- json-ld:end -->\n"


def _insert_json_ld(html: str, ld_objects: list[dict]) -> str:
    script_json = json.dumps(ld_objects if len(ld_objects) > 1 else ld_objects[0], ensure_ascii=False, indent=2)
    block = f'{JSON_LD_START}  <script type="application/ld+json">\n{script_json}\n  </script>\n{JSON_LD_END}'

    if JSON_LD_START in html:
        pattern = re.compile(re.escape(JSON_LD_START) + r".*?" + re.escape(JSON_LD_END), re.S)
        return pattern.sub(block, html)

    head_close = html.index("</head>")
    return html[:head_close] + block + html[head_close:]


def add_prefecture_json_ld(card_payload: dict) -> list[str]:
    """各都道府県ページへ BreadcrumbList + CollectionPage のJSON-LDを追加する。
    CollectionPageはWebPageのサブタイプであり、学校一覧という性質をより正確に
    表す（別途WebPageを重ねて宣言しない）。WebSiteはポータルページのみに置く。"""
    added = []
    for pref in card_payload["prefectures"]:
        slug = pref["prefecture_code"]
        name = pref["prefecture_name"]
        url_path = pref["url"]
        page_path = PAGE_DIR / slug / "index.html"
        if not page_path.is_file():
            continue
        html = page_path.read_text(encoding="utf-8")

        title_match = re.search(r"<title>([^<]*)</title>", html)
        desc_match = re.search(r'<meta name="description" content="([^"]*)">', html)
        page_url = f"{SITE_ORIGIN}{url_path}"

        breadcrumb = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "ホーム", "item": f"{SITE_ORIGIN}/"},
                {"@type": "ListItem", "position": 2, "name": "全国学校データベース", "item": f"{SITE_ORIGIN}/tools/school-database/"},
                {"@type": "ListItem", "position": 3, "name": f"{name}学校データベース", "item": page_url},
            ],
        }
        collection_page = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title_match.group(1) if title_match else f"{name}学校データベース",
            "description": desc_match.group(1) if desc_match else "",
            "url": page_url,
            "inLanguage": "ja",
            "isPartOf": {"@type": "WebSite", "@id": f"{SITE_ORIGIN}/tools/school-database/"},
        }

        new_html = _insert_json_ld(html, [breadcrumb, collection_page])
        if new_html != html:
            page_path.write_text(new_html, encoding="utf-8")
            added.append(slug)
    return added


def add_portal_json_ld() -> bool:
    html = PORTAL_PAGE.read_text(encoding="utf-8")
    website = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Ban.Tai 全国学校データベース",
        "url": f"{SITE_ORIGIN}/tools/school-database/",
        "inLanguage": "ja",
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ホーム", "item": f"{SITE_ORIGIN}/"},
            {"@type": "ListItem", "position": 2, "name": "全国学校データベース", "item": f"{SITE_ORIGIN}/tools/school-database/"},
        ],
    }
    new_html = _insert_json_ld(html, [website, breadcrumb])
    if new_html == html:
        return False
    PORTAL_PAGE.write_text(new_html, encoding="utf-8")
    return True


BREADCRUMB_START = "    <!-- pref-breadcrumb:start -->\n"
BREADCRUMB_END = "    <!-- pref-breadcrumb:end -->\n"
RELATED_LINKS_START = "    <!-- pref-related-links:start -->\n"
RELATED_LINKS_END = "    <!-- pref-related-links:end -->\n"


def add_visual_breadcrumb(card_payload: dict) -> list[str]:
    """<main>の直後（page-heroの手前）に、JSON-LDのBreadcrumbListと対応する
    視覚的なパンくずリストを追加する。"""
    added = []
    for pref in card_payload["prefectures"]:
        slug = pref["prefecture_code"]
        name = pref["prefecture_name"]
        url_path = pref["url"]
        page_path = PAGE_DIR / slug / "index.html"
        if not page_path.is_file():
            continue
        html = page_path.read_text(encoding="utf-8")

        block = (
            f'{BREADCRUMB_START}'
            f'    <nav class="pref-breadcrumb" aria-label="パンくずリスト">\n'
            f'      <div class="container">\n'
            f'        <a href="/">ホーム</a>\n'
            f'        <span aria-hidden="true"> &gt; </span>\n'
            f'        <a href="/tools/school-database/">全国学校データベース</a>\n'
            f'        <span aria-hidden="true"> &gt; </span>\n'
            f'        <span aria-current="page">{name}学校データベース</span>\n'
            f"      </div>\n"
            f"    </nav>\n"
            f"{BREADCRUMB_END}"
        )

        if BREADCRUMB_START in html:
            pattern = re.compile(re.escape(BREADCRUMB_START) + r".*?" + re.escape(BREADCRUMB_END), re.S)
            new_html = pattern.sub(block, html)
        else:
            main_open = re.search(r"<main>\n", html)
            if not main_open:
                raise ValueError(f"{slug}: <main>が見つかりません")
            insert_at = main_open.end()
            new_html = html[:insert_at] + block + html[insert_at:]

        if new_html != html:
            page_path.write_text(new_html, encoding="utf-8")
            added.append(slug)
    return added


def _related_link_chips(slugs: list[str], name_by_slug: dict[str, str]) -> str:
    return "".join(
        f'<a class="related-pref-chip" href="{name_by_slug[s][1]}">{name_by_slug[s][0]}</a>\n          '
        for s in slugs
    )


def add_related_prefecture_links(card_payload: dict) -> list[str]:
    """隣接都道府県・同地方の他都道府県への内部リンクセクションを追加する
    （SEOの内部リンク最適化と、利用者が近隣県のデータベースを見つけやすくする
    導線の両方を兼ねる）。隣接・同地方のいずれも存在しない場合
    （北海道など、単独で1地方かつ陸続きの隣接県がない場合）はセクション自体
    を省略する。"""
    name_by_slug = {p["prefecture_code"]: (p["prefecture_name"], p["url"]) for p in card_payload["prefectures"]}
    region_by_slug = {p["prefecture_code"]: p["region"] for p in card_payload["prefectures"]}
    slugs_by_region: dict[str, list[str]] = {}
    for p in card_payload["prefectures"]:
        slugs_by_region.setdefault(p["region"]["code"], []).append(p["prefecture_code"])

    added = []
    for pref in card_payload["prefectures"]:
        slug = pref["prefecture_code"]
        page_path = PAGE_DIR / slug / "index.html"
        if not page_path.is_file():
            continue

        adjacent = [s for s in PREFECTURE_ADJACENCY.get(slug, []) if s in name_by_slug]
        region = region_by_slug[slug]
        same_region = [s for s in slugs_by_region.get(region["code"], []) if s != slug and s not in adjacent]

        if not adjacent and not same_region:
            content = ""
        else:
            parts = ['    <section class="related-prefectures-section">\n      <div class="container">\n']
            if adjacent:
                parts.append('        <h3 class="related-prefectures-heading">隣接都道府県のデータベース</h3>\n        <div class="related-pref-chips">\n          ')
                parts.append(_related_link_chips(adjacent, name_by_slug))
                parts.append("</div>\n")
            if same_region:
                parts.append(f'        <h3 class="related-prefectures-heading">{region["name"]}の他の都道府県</h3>\n        <div class="related-pref-chips">\n          ')
                parts.append(_related_link_chips(same_region, name_by_slug))
                parts.append("</div>\n")
            parts.append("      </div>\n    </section>\n")
            content = "".join(parts)

        block = f"{RELATED_LINKS_START}{content}{RELATED_LINKS_END}"

        html = page_path.read_text(encoding="utf-8")
        if RELATED_LINKS_START in html:
            pattern = re.compile(re.escape(RELATED_LINKS_START) + r".*?" + re.escape(RELATED_LINKS_END), re.S)
            new_html = pattern.sub(block, html)
        else:
            main_close = html.rindex("  </main>\n")
            new_html = html[:main_close] + block + html[main_close:]

        if new_html != html:
            page_path.write_text(new_html, encoding="utf-8")
            added.append(slug)
    return added


def regenerate_sitemap(card_payload: dict) -> None:
    urls = [(f"{SITE_ORIGIN}/tools/school-database/", "2026-07-26")]
    for pref in card_payload["prefectures"]:
        urls.append((f"{SITE_ORIGIN}{pref['url']}", "2026-08-03"))

    existing = SITEMAP_PATH.read_text(encoding="utf-8")
    # school-database配下の既存<url>ブロックをすべて除去し、後で全件を並べ直す。
    existing = re.sub(
        r"  <url>\n    <loc>https://bantai-education-design\.github\.io/tools/school-database/[^\n]*\n(?:.*\n)*?  </url>\n",
        "",
        existing,
    )

    blocks = "".join(
        f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>\n"
        for loc, lastmod in urls
    )

    new_sitemap = existing.replace("</urlset>", blocks + "</urlset>")
    SITEMAP_PATH.write_text(new_sitemap, encoding="utf-8")


def main() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))

    changed = fix_meta_description_counts(prefecture_metadata)
    print(f"meta description件数を修正: {len(changed)}件")
    for line in changed:
        print(f"  {line}")

    portal_changed = fix_portal_description(prefecture_metadata)
    print(f"ポータルdescriptionを更新: {portal_changed}")

    added = ensure_canonical_tags(card_payload)
    print(f"canonicalタグを追加: {len(added)}件 ({', '.join(added) if added else 'なし'})")

    ld_added = add_prefecture_json_ld(card_payload)
    print(f"都道府県ページへJSON-LDを追加/更新: {len(ld_added)}件")

    portal_ld_added = add_portal_json_ld()
    print(f"ポータルへJSON-LDを追加/更新: {portal_ld_added}")

    breadcrumb_added = add_visual_breadcrumb(card_payload)
    print(f"視覚的パンくずを追加/更新: {len(breadcrumb_added)}件")

    related_added = add_related_prefecture_links(card_payload)
    print(f"関連都道府県リンクを追加/更新: {len(related_added)}件")

    regenerate_sitemap(card_payload)
    print("sitemap.xmlを47都道府県+ポータルで再生成しました")


if __name__ == "__main__":
    main()
