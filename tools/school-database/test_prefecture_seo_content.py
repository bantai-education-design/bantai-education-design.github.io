#!/usr/bin/env python3
"""Validate the per-prefecture SEO content section
(tools/school-database/{slug}/index.html, marker pref-seo-content:start/end)
and its matching FAQPage JSON-LD, for all 47 prefectures.

No pytest — plain assertions, run directly."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFECTURE_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-metadata.json"
CARD_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
PAGE_DIR = ROOT / "tools" / "school-database"

sys.path.insert(0, str(PAGE_DIR))
from prefecture_seo_content import build_content, build_faq_items  # noqa: E402

SEO_CONTENT_START = "<!-- pref-seo-content:start -->"
SEO_CONTENT_END = "<!-- pref-seo-content:end -->"

# 根拠のない評価・順位表現の禁止語（education-profile-source-manifest.mdの
# 方針を踏襲）。「認定」は「幼保連携型認定こども園」という実在の学校種名に
# 含まれるため対象外（自己評価的な「〇〇認定」の意味では使用していない）。
PROHIBITED_WORDS = [
    "盛ん", "先進", "優れ", "日本一", "ランキング", "公式ランキング",
    "都道府県章",
]


def test_all_47_have_seo_content_section() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    assert len(prefecture_metadata) == 47

    for meta in prefecture_metadata:
        slug = meta["slug"]
        html = (PAGE_DIR / slug / "index.html").read_text(encoding="utf-8")
        assert SEO_CONTENT_START in html, f"{slug}: pref-seo-contentセクションが見つかりません"
        assert html.count(SEO_CONTENT_START) == 1, f"{slug}: pref-seo-contentセクションが重複しています"

        block_match = re.search(
            re.escape(SEO_CONTENT_START) + r"(.*?)" + re.escape(SEO_CONTENT_END), html, re.S
        )
        assert block_match, f"{slug}: pref-seo-contentの終了マーカーが見つかりません"
        block = block_match.group(1)

        pref_name = meta["prefecture"]
        assert pref_name in block, f"{slug}: 紹介文に県名が含まれていません"
        assert f'{meta["total"]:,}校・園' in block, f"{slug}: 学校数が本文に含まれていません"
        assert "<h3" in block and "よくある質問" in block, f"{slug}: FAQ見出しが見つかりません"
        assert block.count('<details class="pref-faq-item">') == 5, f"{slug}: FAQ件数が5件ではありません"


def test_seo_content_values_match_source_data() -> None:
    """本文中の数値がprefecture-metadata.json/ prefecture-card-metadata.jsonと
    独立に再計算した値と一致することを確認する（ハードコードではないか検証）。"""
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    card_by_slug = {p["prefecture_code"]: p for p in card_payload["prefectures"]}

    for meta in prefecture_metadata:
        slug = meta["slug"]
        card_pref = card_by_slug[slug]
        pref_name = meta["prefecture"]
        expected = build_content(pref_name, meta, card_pref)

        html = (PAGE_DIR / slug / "index.html").read_text(encoding="utf-8")
        block_match = re.search(
            re.escape(SEO_CONTENT_START) + r"(.*?)" + re.escape(SEO_CONTENT_END), html, re.S
        )
        block = block_match.group(1)

        assert expected["intro"] in block, f"{slug}: 紹介文が期待値と一致しません"
        assert expected["stats"] in block, f"{slug}: 統計解説文が期待値と一致しません"
        for feature in expected["features"]:
            assert feature in block, f"{slug}: 機能一覧に「{feature}」が含まれていません"
        for use_case in expected["use_cases"]:
            assert use_case in block, f"{slug}: 利用例に「{use_case}」が含まれていません"


def test_no_prohibited_evaluative_wording() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    for meta in prefecture_metadata:
        slug = meta["slug"]
        html = (PAGE_DIR / slug / "index.html").read_text(encoding="utf-8")
        block_match = re.search(
            re.escape(SEO_CONTENT_START) + r"(.*?)" + re.escape(SEO_CONTENT_END), html, re.S
        )
        block = block_match.group(1)
        for word in PROHIBITED_WORDS:
            assert word not in block, f"{slug}: 禁止表現「{word}」が本文に含まれています"


def test_faq_visible_content_matches_json_ld_exactly() -> None:
    """可視のFAQ（<details>）とFAQPage JSON-LDのQ&Aが完全に一致することを
    確認する（別々に生成されて食い違うことを防ぐ）。"""
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    card_by_slug = {p["prefecture_code"]: p for p in card_payload["prefectures"]}

    for meta in prefecture_metadata:
        slug = meta["slug"]
        pref_name = meta["prefecture"]
        html = (PAGE_DIR / slug / "index.html").read_text(encoding="utf-8")

        # 可視のFAQ抽出
        visible_faq = re.findall(
            r'<summary>([^<]*)</summary>\s*<p>([^<]*)</p>', html
        )
        assert len(visible_faq) == 5, f"{slug}: 可視FAQが5件見つかりません（{len(visible_faq)}件）"

        # JSON-LDのFAQPage抽出
        ld_match = re.search(r'<script type="application/ld\+json">\n(.*?)\n  </script>', html, re.S)
        assert ld_match, f"{slug}: JSON-LDが見つかりません"
        ld_data = json.loads(ld_match.group(1))
        ld_objects = ld_data if isinstance(ld_data, list) else [ld_data]
        faq_page = next((o for o in ld_objects if o["@type"] == "FAQPage"), None)
        assert faq_page is not None, f"{slug}: FAQPageのJSON-LDが見つかりません"
        assert len(faq_page["mainEntity"]) == 5, f"{slug}: JSON-LDのFAQ件数が5件ではありません"

        for i, (q, a) in enumerate(visible_faq):
            ld_q = faq_page["mainEntity"][i]["name"]
            ld_a = faq_page["mainEntity"][i]["acceptedAnswer"]["text"]
            assert q == ld_q, f"{slug}: FAQ質問{i}が可視コンテンツとJSON-LDで不一致 ({q!r} != {ld_q!r})"
            assert a == ld_a, f"{slug}: FAQ回答{i}が可視コンテンツとJSON-LDで不一致 ({a!r} != {ld_a!r})"

        # build_faq_items()（唯一の情報源）との一致も確認
        expected_faq = build_faq_items(pref_name, meta["total"], meta["municipality_count"], meta["school_type_count"])
        for i, item in enumerate(expected_faq):
            assert visible_faq[i][0] == item["question"], f"{slug}: FAQ質問{i}がbuild_faq_items()と不一致"
            assert visible_faq[i][1] == item["answer"], f"{slug}: FAQ回答{i}がbuild_faq_items()と不一致"


def test_content_is_prefecture_specific_not_generic() -> None:
    """複数県の本文が完全に同一（機械的な使い回し）になっていないことを
    確認する。"""
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    intros = set()
    for meta in prefecture_metadata:
        slug = meta["slug"]
        html = (PAGE_DIR / slug / "index.html").read_text(encoding="utf-8")
        block_match = re.search(
            re.escape(SEO_CONTENT_START) + r"(.*?)" + re.escape(SEO_CONTENT_END), html, re.S
        )
        intro_match = re.search(r'pref-seo-content-text">([^<]*)</p>', block_match.group(1))
        intros.add(intro_match.group(1))
    assert len(intros) == 47, "紹介文が重複しています（県固有の内容になっていない可能性）"


def test_generation_is_idempotent() -> None:
    """generate_prefecture_seo_content.pyを再実行しても差分が出ないことを
    確認する（マーカーベースの置換が正しく機能しているか）。"""
    sys.path.insert(0, str(PAGE_DIR))
    import generate_prefecture_seo_content as gen

    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))

    before = {
        m["slug"]: (PAGE_DIR / m["slug"] / "index.html").read_text(encoding="utf-8")
        for m in prefecture_metadata
    }
    added = gen.insert_seo_content(prefecture_metadata, card_payload)
    assert added == [], f"再実行で差分が発生しました（冪等ではありません）: {added}"
    after = {
        m["slug"]: (PAGE_DIR / m["slug"] / "index.html").read_text(encoding="utf-8")
        for m in prefecture_metadata
    }
    assert before == after, "再実行でファイル内容が変化しました"


if __name__ == "__main__":
    test_all_47_have_seo_content_section()
    test_seo_content_values_match_source_data()
    test_no_prohibited_evaluative_wording()
    test_faq_visible_content_matches_json_ld_exactly()
    test_content_is_prefecture_specific_not_generic()
    test_generation_is_idempotent()
    print("Prefecture SEO content validation passed successfully.")
