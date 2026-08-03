#!/usr/bin/env python3
"""Rewrite <title>, <meta name="description">, and the page-hero lead
paragraph on the 47 prefecture pages and the portal to naturally include the
phrases teachers actually search for — not just "学校データベース"/"教育統計"
but "学校一覧", "学校住所", "電話番号", "学校名簿", "転校先", "宛名" — per the
user's Phase 1 search-intent SEO plan (see PR description).

Run AFTER this script, generate_seo_metadata.py's add_prefecture_json_ld()
must be re-run: it extracts <title>/<meta description> to build the
CollectionPage JSON-LD, so re-running it resyncs the structured data with the
new visible text (no separate template needed here).

Idempotent: each regex targets a single, structurally-guaranteed tag/element,
and only writes the file if the computed value differs from what's already
there."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFECTURE_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-metadata.json"
PAGE_DIR = ROOT / "tools" / "school-database"
PORTAL_PAGE = PAGE_DIR / "index.html"


def format_number(n: int) -> str:
    return f"{n:,}"


def build_title(pref_name: str) -> str:
    return f"{pref_name}の学校一覧・住所検索データベース | Ban.Tai Education Design"


def build_description(pref_name: str, meta: dict) -> str:
    total = meta["total"]
    school_type_count = meta["school_type_count"]
    return (
        f"{pref_name}の学校一覧・住所検索データベースです。小学校・中学校・高等学校など"
        f"国公私立{school_type_count}種類、合計{format_number(total)}校・園を収録し、"
        f"学校名・市区町村・郵便番号・電話番号で検索できます。学校名簿の作成、転校先の確認、"
        f"封筒印刷用の宛名コピー、CSVダウンロードにも便利です。"
    )


def build_lead(pref_name: str) -> str:
    return (
        f"{pref_name}の学校一覧・住所検索データベースです。"
        "学校名簿の作成や転校先の確認、封筒印刷用の宛名作成にも使えます。"
    )


def _replace_title(html: str, new_title: str) -> str:
    return re.sub(r"<title>[^<]*</title>", f"<title>{new_title}</title>", html, count=1)


def _replace_description(html: str, new_description: str) -> str:
    return re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{new_description}">',
        html,
        count=1,
    )


def _replace_lead(html: str, new_lead: str) -> str:
    return re.sub(
        r'<p class="lead">[^<]*</p>',
        f'<p class="lead">{new_lead}</p>',
        html,
        count=1,
    )


def enrich_prefecture_pages(prefecture_metadata: list[dict]) -> list[str]:
    changed = []
    for meta in prefecture_metadata:
        slug = meta["slug"]
        page_path = PAGE_DIR / slug / "index.html"
        if not page_path.is_file():
            continue
        pref_name = meta["prefecture"]

        html = page_path.read_text(encoding="utf-8")
        new_html = _replace_title(html, build_title(pref_name))
        new_html = _replace_description(new_html, build_description(pref_name, meta))
        new_html = _replace_lead(new_html, build_lead(pref_name))

        if new_html != html:
            page_path.write_text(new_html, encoding="utf-8")
            changed.append(slug)
    return changed


PORTAL_TITLE = "全国47都道府県の学校一覧・住所検索データベース | Ban.Tai Education Design"


def build_portal_description(national_total: int) -> str:
    return (
        f"全国47都道府県対応、学校一覧・住所検索データベースです"
        f"（掲載校・園数 合計{format_number(national_total)}件）。都道府県を選んで、"
        "学校名・住所・郵便番号・電話番号で検索でき、学校名簿の作成、転校先の確認、"
        "封筒印刷用の宛名コピー、CSV出力にも便利です。"
    )


def enrich_portal(prefecture_metadata: list[dict]) -> bool:
    national_total = sum(m["total"] for m in prefecture_metadata)
    html = PORTAL_PAGE.read_text(encoding="utf-8")
    new_html = _replace_title(html, PORTAL_TITLE)
    new_html = _replace_description(new_html, build_portal_description(national_total))
    if new_html != html:
        PORTAL_PAGE.write_text(new_html, encoding="utf-8")
        return True
    return False


def main() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    assert len(prefecture_metadata) == 47, "47都道府県データが揃っていません"

    changed = enrich_prefecture_pages(prefecture_metadata)
    print(f"title/description/リード文を更新: {len(changed)}件")
    for slug in changed:
        print(f"  {slug}")

    portal_changed = enrich_portal(prefecture_metadata)
    print(f"ポータルのtitle/descriptionを更新: {portal_changed}")


if __name__ == "__main__":
    main()
