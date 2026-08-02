#!/usr/bin/env python3
"""Validate the migration of the official 東京都学校データベース page
(tools/school-database/tokyo/index.html) off the legacy
tools/tokyo-school-address/ search engine and dataset, onto the current
data/school-database/tokyo.json (3,493 records) using the same
assets/js/school-database/search-{slug}.js pattern as the other 46
prefectures.

Every count shown on the official page (収録範囲見出し・校種×設置区分
マトリクス・JSON件数) must trace back to the same 3,493-record dataset,
and the legacy 3,509-record dataset/script must no longer be referenced
from the official page."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOKYO_JSON = ROOT / "data" / "school-database" / "tokyo.json"
OFFICIAL_PAGE = ROOT / "tools" / "school-database" / "tokyo" / "index.html"
SEARCH_JS = ROOT / "assets" / "js" / "school-database" / "search-tokyo.js"
LEGACY_DATA_JSON = ROOT / "data" / "tokyo_public_schools_address_2025.json"

SCHOOL_TYPE_ORDER = [
    "幼稚園", "幼保連携型認定こども園", "小学校", "中学校",
    "義務教育学校", "高等学校", "中等教育学校", "特別支援学校",
]


def format_number(n: int) -> str:
    return f"{n:,}"


def test_official_page_does_not_reference_legacy_assets() -> None:
    html = OFFICIAL_PAGE.read_text(encoding="utf-8")
    assert "/tools/tokyo-school-address/style.css" not in html, "正式ページがレガシーCSSを参照しています"
    assert "/tools/tokyo-school-address/search.js" not in html, "正式ページがレガシーsearch.jsを参照しています"
    assert "tokyo_public_schools_address_2025.json" not in html, "正式ページがレガシーデータファイルを参照しています"
    assert "3,509" not in html, "正式ページに旧3,509が残っています"


def test_official_page_uses_modern_assets() -> None:
    html = OFFICIAL_PAGE.read_text(encoding="utf-8")
    assert "/assets/css/school-database.css" in html, "正式ページが共通CSSを読み込んでいません"
    assert "/assets/js/school-database/search-tokyo.js" in html, "正式ページがsearch-tokyo.jsを読み込んでいません"
    assert '<select id="sort-order"' in html, "並び順セレクトがありません"
    assert 'value="園長先生"' in html, "園長先生宛て敬称オプションがありません（幼稚園データが含まれるため必要）"


def test_search_tokyo_js_uses_current_dataset() -> None:
    js = SEARCH_JS.read_text(encoding="utf-8")
    fetch_match = re.search(r"fetch\('([^']+)'\)", js)
    assert fetch_match, "search-tokyo.jsにfetch呼び出しが見つかりません"
    assert fetch_match.group(1) == "/data/school-database/tokyo.json", (
        f"search-tokyo.jsが現行データセットを取得していません（実際={fetch_match.group(1)}）"
    )
    assert "3,509" not in js and "3509" not in js, "search-tokyo.jsに旧3,509件が残っています"
    assert '"都道府県"' in js, "CSVヘッダーに都道府県列がありません"
    assert "|| '東京都'" in js, "CSVの都道府県デフォルト値が東京都になっていません"
    assert "school.school_name + ' ' + school.address" in js, "Google Mapsクエリが学校名＋住所の形式になっていません"


def test_tokyo_json_record_count_is_3493() -> None:
    records = json.loads(TOKYO_JSON.read_text(encoding="utf-8"))
    assert len(records) == 3493, f"tokyo.jsonの件数が3,493件ではありません（{len(records)}件）"


def test_legacy_dataset_untouched_but_not_referenced_by_official_page() -> None:
    # レガシーファイルは削除しない方針のため、存在自体は維持されているはず。
    assert LEGACY_DATA_JSON.is_file(), "レガシーデータファイルが見つかりません（削除しない方針のはずです）"
    legacy = json.loads(LEGACY_DATA_JSON.read_text(encoding="utf-8"))
    assert len(legacy) == 3509, "レガシーデータの件数が変化しています（レガシーは変更しない方針のはずです）"


def test_matrix_table_matches_current_data_cross_tab() -> None:
    records = json.loads(TOKYO_JSON.read_text(encoding="utf-8"))
    html = OFFICIAL_PAGE.read_text(encoding="utf-8")

    header_match = re.search(r"本データベースの収録範囲[（(]\s*合計\s*([\d,]+)\s*校・園[）)]", html)
    assert header_match, "収録範囲の見出しが見つかりません"
    assert header_match.group(1) == format_number(len(records)), (
        f"収録範囲見出しがJSON件数と一致しません（表示={header_match.group(1)} / 実件数={len(records)}）"
    )

    cross: dict[str, dict[str, int]] = {}
    for r in records:
        cross.setdefault(r["school_type"], {})
        cross[r["school_type"]][r["establishment_type"]] = cross[r["school_type"]].get(r["establishment_type"], 0) + 1

    est_present = [e for e in ["国立", "公立", "私立", "その他"] if any(e in ests for ests in cross.values())]
    assert est_present == ["公立", "私立"], f"現行データの設置区分が想定と異なります: {est_present}"

    matrix_match = re.search(r"<!-- tokyo-matrix-table:start -->(.*?)<!-- tokyo-matrix-table:end -->", html, re.S)
    assert matrix_match, "マトリクステーブルが見つかりません"
    matrix_html = matrix_match.group(1)

    grand_total = 0
    for t in SCHOOL_TYPE_ORDER:
        if t not in cross:
            continue
        row_total = sum(cross[t].values())
        grand_total += row_total
        for est in est_present:
            count = cross[t].get(est, 0)
            if count > 0:
                expected_cell = f"✓ ({format_number(count)}校)" if t not in ("幼稚園", "幼保連携型認定こども園") else f"✓ ({format_number(count)}園)"
                assert expected_cell in matrix_html, (
                    f"{t}/{est}: マトリクスのセル表示が一致しません（期待値含む文字列: {expected_cell}）"
                )
            else:
                expected_zero = "0校" if t not in ("幼稚園", "幼保連携型認定こども園") else "0園"
                # 行内に該当校種の0件セルが存在することを確認（他行の0件と混同しないよう行単位で確認）
                row_pattern = re.search(re.escape(t) + r"</td>(.*?)</tr>", matrix_html, re.S)
                assert row_pattern and expected_zero in row_pattern.group(1), (
                    f"{t}/{est}: 0件セルの表示が見つかりません（期待値: {expected_zero}）"
                )

    assert grand_total == len(records) == 3493, (
        f"マトリクス全行合計がJSON件数と一致しません（マトリクス={grand_total} / JSON={len(records)}）"
    )


if __name__ == "__main__":
    test_official_page_does_not_reference_legacy_assets()
    test_official_page_uses_modern_assets()
    test_search_tokyo_js_uses_current_dataset()
    test_tokyo_json_record_count_is_3493()
    test_legacy_dataset_untouched_but_not_referenced_by_official_page()
    test_matrix_table_matches_current_data_cross_tab()
    print("Tokyo search migration validation passed successfully.")
