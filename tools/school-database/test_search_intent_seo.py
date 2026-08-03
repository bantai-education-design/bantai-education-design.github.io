#!/usr/bin/env python3
"""Validate that the 47 prefecture pages and the portal naturally include
the phrases teachers actually search for (not just "学校データベース"/
"教育統計"): 学校一覧, 学校住所/住所, 電話番号, 宛名, 学校名簿, 転校先.

No pytest — plain assertions, run directly."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFECTURE_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-metadata.json"
PAGE_DIR = ROOT / "tools" / "school-database"
PORTAL_PAGE = PAGE_DIR / "index.html"

# 先生が実際に検索する語のうち、少なくとも1箇所は本文中に含まれてほしいもの
# （タイトル・description・リード文・SEOコンテンツセクションいずれか）。
REQUIRED_PHRASES = ["学校一覧", "住所", "電話番号", "宛名", "学校名簿", "転校先"]


def _title(html: str) -> str:
    return re.search(r"<title>([^<]*)</title>", html).group(1)


def _description(html: str) -> str:
    return re.search(r'<meta name="description" content="([^"]*)">', html).group(1)


def _lead(html: str) -> str:
    m = re.search(r'<p class="lead">([^<]*)</p>', html)
    return m.group(1) if m else ""


TITLE_MAX_LENGTH = 60


def test_title_length_stays_within_serp_friendly_bound() -> None:
    """タイトルが長すぎるとSERPで途中省略されるため、60字前後に収める。"""
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    for meta in prefecture_metadata:
        slug = meta["slug"]
        html = (PAGE_DIR / slug / "index.html").read_text(encoding="utf-8")
        title = _title(html)
        assert len(title) <= TITLE_MAX_LENGTH, f"{slug}: titleが{TITLE_MAX_LENGTH}字を超えています（{len(title)}字）: {title}"


def test_title_and_description_include_school_list_phrase() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    for meta in prefecture_metadata:
        slug = meta["slug"]
        pref_name = meta["prefecture"]
        html = (PAGE_DIR / slug / "index.html").read_text(encoding="utf-8")
        title = _title(html)
        desc = _description(html)
        assert "学校一覧" in title, f"{slug}: titleに「学校一覧」が含まれていません: {title}"
        assert pref_name in title, f"{slug}: titleに県名が含まれていません: {title}"
        assert "学校一覧" in desc, f"{slug}: descriptionに「学校一覧」が含まれていません"


def test_all_required_phrases_covered_somewhere_on_page() -> None:
    """タイトル・description・リード文・SEOコンテンツセクションのいずれかに、
    先生の検索語（学校一覧・住所・電話番号・宛名・学校名簿・転校先）が
    すべて含まれることを確認する。"""
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    for meta in prefecture_metadata:
        slug = meta["slug"]
        html = (PAGE_DIR / slug / "index.html").read_text(encoding="utf-8")
        searchable_text = _title(html) + _description(html) + _lead(html)
        seo_block_match = re.search(
            r"<!-- pref-seo-content:start -->(.*?)<!-- pref-seo-content:end -->", html, re.S
        )
        if seo_block_match:
            searchable_text += seo_block_match.group(1)

        missing = [p for p in REQUIRED_PHRASES if p not in searchable_text]
        assert not missing, f"{slug}: 次の検索意図フレーズが本文に含まれていません: {missing}"


def test_lead_paragraph_present_once_and_matches_title_intent() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    for meta in prefecture_metadata:
        slug = meta["slug"]
        html = (PAGE_DIR / slug / "index.html").read_text(encoding="utf-8")
        assert html.count('<p class="lead">') == 1, f"{slug}: リード文が重複または欠落しています"
        lead = _lead(html)
        assert "学校一覧" in lead, f"{slug}: リード文に「学校一覧」が含まれていません: {lead}"


def test_collection_page_json_ld_matches_updated_title_and_description() -> None:
    """generate_seo_metadata.pyのadd_prefecture_json_ld()が、新しいtitle/
    descriptionを反映してCollectionPageを再生成していることを確認する
    （enrich_search_intent_titles.py実行後にJSON-LDが古いままにならないか）。"""
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    for meta in prefecture_metadata:
        slug = meta["slug"]
        html = (PAGE_DIR / slug / "index.html").read_text(encoding="utf-8")
        title = _title(html)
        desc = _description(html)

        ld_match = re.search(r'<script type="application/ld\+json">\n(.*?)\n  </script>', html, re.S)
        ld_data = json.loads(ld_match.group(1))
        collection = next(o for o in ld_data if o["@type"] == "CollectionPage")
        assert collection["name"] == title, f"{slug}: CollectionPage.nameがtitleと一致しません"
        assert collection["description"] == desc, f"{slug}: CollectionPage.descriptionがdescriptionと一致しません"


def test_portal_title_and_description_include_school_list_phrase() -> None:
    html = PORTAL_PAGE.read_text(encoding="utf-8")
    title = _title(html)
    desc = _description(html)
    assert "学校一覧" in title, f"ポータルのtitleに「学校一覧」が含まれていません: {title}"
    assert "学校一覧" in desc, "ポータルのdescriptionに「学校一覧」が含まれていません"
    assert "47都道府県" in title or "47都道府県" in desc, "ポータルのtitle/descriptionに「47都道府県」が含まれていません"


def test_titles_are_unique_across_47_prefectures() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    titles = set()
    for meta in prefecture_metadata:
        slug = meta["slug"]
        html = (PAGE_DIR / slug / "index.html").read_text(encoding="utf-8")
        titles.add(_title(html))
    assert len(titles) == 47, "titleが重複しています（県固有になっていない可能性）"


if __name__ == "__main__":
    test_title_length_stays_within_serp_friendly_bound()
    test_title_and_description_include_school_list_phrase()
    test_all_required_phrases_covered_somewhere_on_page()
    test_lead_paragraph_present_once_and_matches_title_intent()
    test_collection_page_json_ld_matches_updated_title_and_description()
    test_portal_title_and_description_include_school_list_phrase()
    test_titles_are_unique_across_47_prefectures()
    print("Search-intent SEO validation passed successfully.")
