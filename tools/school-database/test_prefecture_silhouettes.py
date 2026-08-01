#!/usr/bin/env python3
"""Validate the prefecture silhouette (都道府県地域マーク) integration into
prefecture-card-metadata.json and the generated SVG files themselves.

This is NOT a test of official prefectural crests/flags — see
docs/school-database/prefecture-silhouettes-source-manifest.md. All 47
prefectures must have silhouette.available === true, since these marks are
generated from freely-licensed (CC BY 4.0 compatible) administrative
boundary data, unlike the abandoned official-crest approach (PR #95, only
1/47 usable) whose leftover `emblem` key must NOT appear in production data.
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
SILHOUETTES_DIR = ROOT / "assets" / "images" / "prefecture-silhouettes"
INDEX_HTML = ROOT / "tools" / "school-database" / "index.html"
SCHOOL_DB_DIR = ROOT / "tools" / "school-database"

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


def test_47_svg_files_exist_with_correct_codes():
    svg_files = sorted(SILHOUETTES_DIR.glob("*.svg"))
    assert len(svg_files) == 47, f"expected 47 SVG files, got {len(svg_files)}"

    seen_codes = set()
    for path in svg_files:
        match = re.match(r"^(\d{2})-([a-z]+)\.svg$", path.name)
        assert match, f"unexpected filename format: {path.name}"
        code, slug = match.group(1), match.group(2)
        assert PREFECTURE_CODE_NUMBER.get(slug) == code, (
            f"{path.name}: コードとslugの対応が想定と異なります"
        )
        assert code not in seen_codes, f"都道府県コード{code}が重複しています"
        seen_codes.add(code)

    expected_codes = set(PREFECTURE_CODE_NUMBER.values())
    assert seen_codes == expected_codes, (
        f"01〜47のコードが揃っていません。欠落={expected_codes - seen_codes}, "
        f"余分={seen_codes - expected_codes}"
    )


def test_svg_content_is_safe_and_non_empty():
    svg_files = sorted(SILHOUETTES_DIR.glob("*.svg"))
    assert len(svg_files) == 47

    for path in svg_files:
        content = path.read_text(encoding="utf-8")
        assert content.strip(), f"{path.name}: 空ファイルです"
        assert "viewbox" in content.lower(), f"{path.name}: viewBoxがありません"
        assert "<script" not in content.lower(), f"{path.name}: scriptタグが含まれています"
        assert "foreignobject" not in content.lower(), f"{path.name}: foreignObjectが含まれています"
        assert not re.search(r'(href|src)\s*=\s*["\']https?://', content, re.IGNORECASE), (
            f"{path.name}: 外部URL参照が含まれています"
        )
        assert "<path" in content or "<polygon" in content, (
            f"{path.name}: pathまたはpolygon要素が見つかりません"
        )


def test_card_metadata_silhouette_for_all_47():
    payload = _read_json(CARD_METADATA_JSON)
    prefectures = payload["prefectures"]
    assert len(prefectures) == 47

    seen_srcs = set()
    for pref in prefectures:
        assert "silhouette" in pref, f"{pref['prefecture_name']}: silhouetteキーがありません"
        silhouette = pref["silhouette"]
        assert silhouette["available"] is True, (
            f"{pref['prefecture_name']}: silhouette.available が true ではありません"
        )
        assert silhouette["alt"] == "", f"{pref['prefecture_name']}: altが\"\"で統一されていません"
        assert silhouette["src"], f"{pref['prefecture_name']}: srcが空です"

        rel_path = silhouette["src"].lstrip("/")
        file_path = ROOT / rel_path
        assert file_path.is_file(), f"{pref['prefecture_name']}: {file_path} が存在しません"

        expected_code = PREFECTURE_CODE_NUMBER[pref["prefecture_code"]]
        filename = Path(silhouette["src"]).name
        assert filename == f"{expected_code}-{pref['prefecture_code']}.svg", (
            f"{pref['prefecture_name']}: ファイル名 {filename!r} が都道府県コードと一致しません"
        )

        assert silhouette["src"] not in seen_srcs, f"{pref['prefecture_name']}: srcが他県と重複しています"
        seen_srcs.add(silhouette["src"])

        assert silhouette["source"], f"{pref['prefecture_name']}: sourceが空です"
        assert silhouette["reference_date"] == "2026-01-01"

        # 公式章方式（見送り済み）の残骸が本番データに残っていないこと。
        assert "emblem" not in pref, (
            f"{pref['prefecture_name']}: 公式章用のemblemキーが本番データに残っています"
        )


def test_population_and_school_data_unchanged_by_silhouette_addition():
    """silhouette追加が既存の人口・学校DB・地方順・カードリンクに影響
    していないことを再確認する（PR #93/#94の回帰guard）。"""
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


def test_renderer_wires_silhouette_without_breaking_existing_behavior():
    js = RENDERER_JS.read_text(encoding="utf-8")

    assert "pref-card-title-row" in js
    assert "pref-silhouette" in js
    assert "silhouette.available === true" in js
    assert "--silhouette-url" in js
    assert 'setAttribute("aria-hidden", "true")' in js

    # 既存のカード全体クリック・details除外・キーボード操作の仕組みが維持されていること。
    assert re.search(
        r'closest\(["\']a,\s*button,\s*summary,\s*details,\s*input,\s*select,\s*textarea["\']\)',
        js,
    ), "カード全体クリックのdetails除外処理が失われています"
    assert "keydown" in js and "Enter" in js

    # シルエット自体には独立したリンク（href/data-card-href）を持たせていないこと。
    assert "silhouetteEl.href" not in js
    assert "silhouetteEl.dataset.cardHref" not in js


def test_css_defines_mask_based_silhouette_with_responsive_sizes():
    css = CSS_PATH.read_text(encoding="utf-8")
    assert re.search(r"\.pref-silhouette\s*\{[^}]*width:\s*32px", css), "PC相当(32px)の定義が見つかりません"
    assert re.search(
        r"@media\s*\(max-width:\s*900px\)\s*\{[^{}]*\.pref-silhouette\s*\{[^}]*width:\s*30px", css
    ), "タブレット相当(30px)の定義が見つかりません"
    assert re.search(
        r"@media\s*\(max-width:\s*640px\)\s*\{[^{}]*\.pref-silhouette\s*\{[^}]*width:\s*28px", css
    ), "スマホ相当(28px)の定義が見つかりません"
    assert "mask-image: var(--silhouette-url)" in css
    assert "flex-shrink: 0" in css
    assert ".pref-card:hover .pref-silhouette" in css


def test_all_47_prefecture_pages_show_hero_silhouette():
    """都道府県ポータルのカードだけでなく、各都道府県別ページ（例:
    tools/school-database/tokyo/index.html）のタイトル帯にも同じ地域マーク
    を表示する。"""
    for slug, code in PREFECTURE_CODE_NUMBER.items():
        page_path = SCHOOL_DB_DIR / slug / "index.html"
        assert page_path.is_file(), f"{slug}: index.htmlが見つかりません"
        html = page_path.read_text(encoding="utf-8")

        assert "hero-silhouette" in html, f"{slug}: hero-silhouetteが見つかりません"
        expected_src = f"/assets/images/prefecture-silhouettes/{code}-{slug}.svg"
        assert expected_src in html, f"{slug}: 期待するsrc({expected_src})が見つかりません"
        assert 'aria-hidden="true"' in html
        assert "<h1" in html, f"{slug}: h1が見つかりません"


def test_portal_html_shows_attribution():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "国土数値情報（行政区域データ）」を加工して作成しています" in html, (
        "国土数値情報の出典表記がindex.htmlに見つかりません"
    )
    # 都道府県章・県旗・公式シンボルマークという表記を使っていないこと。
    for prohibited in ("都道府県章", "県章", "公式マーク", "公式シンボル", "県旗"):
        assert prohibited not in html, f"禁止表記 '{prohibited}' がindex.htmlに含まれています"


if __name__ == "__main__":
    test_47_svg_files_exist_with_correct_codes()
    test_svg_content_is_safe_and_non_empty()
    test_card_metadata_silhouette_for_all_47()
    test_population_and_school_data_unchanged_by_silhouette_addition()
    test_renderer_wires_silhouette_without_breaking_existing_behavior()
    test_css_defines_mask_based_silhouette_with_responsive_sizes()
    test_all_47_prefecture_pages_show_hero_silhouette()
    test_portal_html_shows_attribution()
    print("Prefecture silhouette integration tests passed successfully.")
