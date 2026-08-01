#!/usr/bin/env python3
"""Validate the prefecture emblem (都道府県章/公式シンボルマーク) integration
into prefecture-card-metadata.json.

Per docs/school-database/prefecture-emblems-source-manifest.md, only
prefectures with a confirmed, officially-licensed mark (no prior approval
required) get emblem.available === true — currently only Toyama. All other
46 prefectures are emblem.available === false with no other keys, no
placeholder image, no guessed mark.

This test also re-verifies that adding the emblem block did not alter any
of the pre-existing population / school_database / region / ordering data
(regression guard for the population feature completed in PR #93/#94).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CARD_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
POPULATION_JSON = ROOT / "data" / "school-database" / "prefecture-population.json"
RENDERER_JS = ROOT / "assets" / "js" / "school-database" / "prefecture-card-renderer.js"
CSS_PATH = ROOT / "assets" / "css" / "school-database.css"
EMBLEMS_DIR = ROOT / "assets" / "images" / "prefecture-emblems"

ALLOWED_EXTENSIONS = {".svg", ".png", ".webp"}

# JIS X 0401 都道府県コード（推奨ファイル名の2桁部分）。
PREFECTURE_CODE_NUMBER = {
    "hokkaido": "01", "aomori": "02", "iwate": "03", "miyagi": "04", "akita": "05",
    "yamagata": "06", "fukushima": "07", "ibaraki": "08", "tochigi": "09", "gunma": "10",
    "saitama": "11", "chiba": "12", "tokyo": "13", "kanagawa": "14", "niigata": "15",
    "toyama": "16", "ishikawa": "17", "fukui": "18", "yamanashi": "19", "nagano": "20",
    "gifu": "21", "shizuoka": "22", "aichi": "23", "mie": "24", "shiga": "25",
    "kyoto": "26", "osaka": "27", "hyogo": "28", "nara": "29", "wakayama": "30",
    "tottori": "31", "shimane": "32", "okayama": "33", "hiroshima": "34", "yamaguchi": "35",
    "tokushima": "36", "kagawa": "37", "ehime": "38", "kochi": "39", "fukuoka": "40",
    "saga": "41", "nagasaki": "42", "kumamoto": "43", "oita": "44", "miyazaki": "45",
    "kagoshima": "46", "okinawa": "47",
}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_emblem_key_present_and_well_formed_for_all_47():
    payload = _read_json(CARD_METADATA_JSON)
    prefectures = payload["prefectures"]
    assert len(prefectures) == 47, f"expected 47 prefectures, got {len(prefectures)}"

    available_count = 0
    seen_srcs = set()
    for pref in prefectures:
        assert "emblem" in pref, f"{pref['prefecture_name']}: emblemキーがありません"
        emblem = pref["emblem"]
        assert "available" in emblem

        if emblem["available"] is False:
            assert set(emblem.keys()) == {"available"}, (
                f"{pref['prefecture_name']}: 未確認県のemblemに余分なキーがあります: {emblem.keys()}"
            )
            continue

        available_count += 1
        assert emblem["src"], f"{pref['prefecture_name']}: srcが空です"
        assert emblem["official_source_url"], f"{pref['prefecture_name']}: official_source_urlがありません"
        assert emblem["official_source_url"].startswith("https://"), (
            f"{pref['prefecture_name']}: official_source_urlがhttps://で始まっていません"
        )
        assert "name" in emblem and emblem["name"], f"{pref['prefecture_name']}: nameが空です"
        assert "alt" in emblem, f"{pref['prefecture_name']}: altキーがありません"

        # ファイル拡張子
        ext = Path(emblem["src"]).suffix.lower()
        assert ext in ALLOWED_EXTENSIONS, f"{pref['prefecture_name']}: 拡張子{ext}が許可されていません"

        # srcファイルが実在する
        rel_path = emblem["src"].lstrip("/")
        file_path = ROOT / rel_path
        assert file_path.is_file(), f"{pref['prefecture_name']}: {file_path} が存在しません"

        # 都道府県コードとファイル名が一致する
        expected_code = PREFECTURE_CODE_NUMBER[pref["prefecture_code"]]
        filename = Path(emblem["src"]).name
        assert filename.startswith(f"{expected_code}-{pref['prefecture_code']}"), (
            f"{pref['prefecture_name']}: ファイル名 {filename!r} が都道府県コード規則"
            f" ({expected_code}-{pref['prefecture_code']}...) と一致しません"
        )

        # 画像重複なし
        assert emblem["src"] not in seen_srcs, f"{pref['prefecture_name']}: srcが他県と重複しています"
        seen_srcs.add(emblem["src"])

    print(f"emblem available for {available_count}/47 prefectures")


def test_alt_policy_is_uniform():
    payload = _read_json(CARD_METADATA_JSON)
    alt_values = {
        pref["emblem"]["alt"]
        for pref in payload["prefectures"]
        if pref["emblem"]["available"] is True
    }
    # 全県で同じ方針（本サイトは装飾目的のalt=""に統一）であること。
    assert alt_values in ({""}, set()), f"alt方針が統一されていません: {alt_values}"


def test_no_placeholder_or_unofficial_source():
    payload = _read_json(CARD_METADATA_JSON)
    for pref in payload["prefectures"]:
        emblem = pref["emblem"]
        if emblem["available"] is True:
            forbidden_domains = ("wikipedia.org", "wikimedia.org", "kunitori-jp.net")
            for domain in forbidden_domains:
                assert domain not in emblem["official_source_url"], (
                    f"{pref['prefecture_name']}: 非公式ソース({domain})が使用されています"
                )
            assert "pref." in emblem["official_source_url"] or ".lg.jp" in emblem["official_source_url"], (
                f"{pref['prefecture_name']}: official_source_urlが都道府県公式ドメインではありません"
            )


def test_svg_files_have_no_unsafe_content():
    """SVGファイルが1件もない場合は何もしない（将来SVGが追加された場合に備える）。"""
    svg_files = list(EMBLEMS_DIR.glob("*.svg")) if EMBLEMS_DIR.exists() else []
    for svg_path in svg_files:
        content = svg_path.read_text(encoding="utf-8")
        assert "<script" not in content.lower(), f"{svg_path.name}: scriptタグが含まれています"
        assert "foreignobject" not in content.lower(), f"{svg_path.name}: foreignObjectが含まれています"
        assert not re.search(r'(href|src)\s*=\s*["\']https?://', content, re.IGNORECASE), (
            f"{svg_path.name}: 外部URL参照が含まれています"
        )
        assert "viewbox" in content.lower(), f"{svg_path.name}: viewBoxがありません"
    print(f"checked {len(svg_files)} SVG file(s)")


def test_population_and_school_data_unchanged_by_emblem_addition():
    """emblem追加が既存の人口・学校DB・地方順・カードリンクに影響していないことを再確認する。"""
    card_payload = _read_json(CARD_METADATA_JSON)
    population_payload = _read_json(POPULATION_JSON)
    prefectures = card_payload["prefectures"]

    assert len(prefectures) == 47
    population_by_code = {p["prefecture_code"]: p for p in population_payload["prefectures"]}

    for pref in prefectures:
        assert pref["population"]["available"] is True
        source_ref = population_by_code[pref["prefecture_code"]]
        assert pref["population"]["census_population"] == source_ref["census_population"]
        assert pref["population"]["census_age_3_17"] == source_ref["census_age_3_17"]
        assert pref["school_database"]["record_count"] > 0
        assert pref["url"].startswith("/tools/school-database/")

    # 地方順・都道府県順は従来どおり関東地方が先頭、東京都が先頭であること。
    assert prefectures[0]["region"]["code"] == "kanto"
    assert prefectures[0]["prefecture_name"] == "東京都"

    region_order = []
    for pref in prefectures:
        code = pref["region"]["code"]
        if not region_order or region_order[-1] != code:
            region_order.append(code)
    assert region_order == [
        "kanto", "hokkaido", "tohoku", "chubu", "kinki", "chugoku", "shikoku", "kyushu",
    ], f"地方順が変更されています: {region_order}"


def test_renderer_wires_emblem_without_breaking_existing_behavior():
    js = RENDERER_JS.read_text(encoding="utf-8")

    assert "pref-card-title-row" in js
    assert "pref-emblem" in js
    assert 'emblem.available === true' in js or "emblem.available===true" in js

    # 既存のカード全体クリック・details除外・キーボード操作の仕組みが維持されていること。
    assert re.search(
        r'closest\(["\']a,\s*button,\s*summary,\s*details,\s*input,\s*select,\s*textarea["\']\)',
        js,
    ), "カード全体クリックのdetails除外処理が失われています"
    assert "keydown" in js and "Enter" in js

    # 画像自体には独立したリンク（href/data-card-href）を持たせていないこと。
    assert "emblemImage.href" not in js
    assert "emblemImage.dataset.cardHref" not in js

    # 遅延読み込み・非同期デコードを指定していること。
    assert 'emblemImage.loading = "lazy"' in js
    assert 'emblemImage.decoding = "async"' in js

    # 画像読み込み失敗時にレイアウトが壊れないよう、エラーハンドリングがあること。
    assert '"error"' in js


def test_css_defines_responsive_emblem_sizes():
    css = CSS_PATH.read_text(encoding="utf-8")
    assert re.search(r"\.pref-emblem\s*\{[^}]*width:\s*32px", css), "PC相当(32px)の定義が見つかりません"
    assert re.search(
        r"@media\s*\(max-width:\s*900px\)\s*\{[^{}]*\.pref-emblem\s*\{[^}]*width:\s*30px", css
    ), "タブレット相当(30px)の定義が見つかりません"
    assert re.search(
        r"@media\s*\(max-width:\s*640px\)\s*\{[^{}]*\.pref-emblem\s*\{[^}]*width:\s*28px", css
    ), "スマホ相当(28px)の定義が見つかりません"
    assert "object-fit: contain" in css
    assert re.search(r"\.pref-emblem\s*\{[^}]*flex-shrink:\s*0", css)


if __name__ == "__main__":
    test_emblem_key_present_and_well_formed_for_all_47()
    test_alt_policy_is_uniform()
    test_no_placeholder_or_unofficial_source()
    test_svg_files_have_no_unsafe_content()
    test_population_and_school_data_unchanged_by_emblem_addition()
    test_renderer_wires_emblem_without_breaking_existing_behavior()
    test_css_defines_responsive_emblem_sizes()
    print("Prefecture emblem integration tests passed successfully.")
