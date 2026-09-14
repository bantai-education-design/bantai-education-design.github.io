#!/usr/bin/env python3
"""Live official Ground Truth audit for IPSS 0-14 population indices.

Every CI run downloads the official IPSS Result Table 2-1 directly and compares
2035/2050 indices (2020=100) for all 47 prefectures with the committed canonical
projection JSON. Prefecture aggregate rows are identified by the official
"市などの別" code `a`; municipality rows are excluded. There is no local-source fallback.
"""

from __future__ import annotations

import io
import json
import re
import unicodedata
import urllib.request
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
MASTER_PATH = ROOT / "data" / "school-database" / "ipss-child-population-projection-2023.json"
IPSS_XLSX_URL = "https://www.ipss.go.jp/pp-shicyoson/j/shicyoson23/2gaiyo_hyo/kekkahyo2_1.xlsx"

PREFECTURE_NAMES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]
PREFECTURE_SET = set(PREFECTURE_NAMES)


def _norm(value: object) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).replace("\u3000", " ").replace("\n", " ").strip()
    return re.sub(r"\s+", "", text)


def _number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = _norm(value).replace(",", "").replace("%", "")
    if not text or text in {"-", "－", "…", "―"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _fetch_workbook() -> openpyxl.Workbook:
    request = urllib.request.Request(IPSS_XLSX_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    assert data[:2] == b"PK", "IPSS live source is not an XLSX payload"
    print(f"[IPSS Live Audit] official result table downloaded live ({len(data):,} bytes)")
    return openpyxl.load_workbook(io.BytesIO(data), data_only=True)


def _find_year_column(sheet, start_col: int, end_col: int, year: int) -> int:
    candidates = [
        col for col in range(start_col, end_col + 1)
        if _norm(sheet.cell(5, col).value) == f"{year}年"
    ]
    assert len(candidates) == 1, f"IPSS {year} column is ambiguous: {candidates}"
    return candidates[0]


def build_live_ipss_indices() -> tuple[dict[str, dict[str, float]], dict[str, float]]:
    wb = _fetch_workbook()
    assert wb.sheetnames == ["Sheet1"], f"Unexpected IPSS workbook sheets: {wb.sheetnames}"
    sheet = wb["Sheet1"]

    assert "0~14歳人口および指数" in _norm(sheet.cell(1, 1).value), f"Unexpected IPSS title: {sheet.cell(1, 1).value!r}"
    assert _norm(sheet.cell(4, 2).value) == "市などの別"
    assert _norm(sheet.cell(4, 3).value) == "都道府県"
    assert "0~14歳人口(人)" in _norm(sheet.cell(4, 5).value)
    assert "指数" in _norm(sheet.cell(4, 12).value)

    pop_2020_col = _find_year_column(sheet, 5, 11, 2020)
    pop_2035_col = _find_year_column(sheet, 5, 11, 2035)
    pop_2050_col = _find_year_column(sheet, 5, 11, 2050)
    idx_2035_col = _find_year_column(sheet, 12, 18, 2035)
    idx_2050_col = _find_year_column(sheet, 12, 18, 2050)

    live: dict[str, dict[str, float]] = {}
    total_2020 = 0.0
    total_2035 = 0.0
    total_2050 = 0.0

    for row in range(6, sheet.max_row + 1):
        if _norm(sheet.cell(row, 2).value).lower() != "a":
            continue
        name = _norm(sheet.cell(row, 3).value)
        assert name in PREFECTURE_SET, f"Unexpected prefecture aggregate label at row {row}: {name!r}"
        assert name not in live, f"Duplicate prefecture aggregate row: {name}"

        idx_2035 = _number(sheet.cell(row, idx_2035_col).value)
        idx_2050 = _number(sheet.cell(row, idx_2050_col).value)
        pop_2020 = _number(sheet.cell(row, pop_2020_col).value)
        pop_2035 = _number(sheet.cell(row, pop_2035_col).value)
        pop_2050 = _number(sheet.cell(row, pop_2050_col).value)
        assert all(value is not None and value >= 0 for value in [idx_2035, idx_2050, pop_2020, pop_2035, pop_2050])

        live[name] = {
            "child_population_index_2035": round(float(idx_2035), 1),
            "child_population_index_2050": round(float(idx_2050), 1),
        }
        total_2020 += float(pop_2020)
        total_2035 += float(pop_2035)
        total_2050 += float(pop_2050)

    assert set(live) == PREFECTURE_SET, f"Expected 47 prefecture aggregate rows, found {len(live)}"

    national = {
        "child_population_index_2035": round(total_2035 / total_2020 * 100, 1),
        "child_population_index_2050": round(total_2050 / total_2020 * 100, 1),
    }
    assert national["child_population_index_2035"] == 77.8, national
    assert national["child_population_index_2050"] == 69.2, national

    print(
        f"[IPSS Live Audit] prefecture aggregate rows=47, index_cols={idx_2035_col}/{idx_2050_col}, "
        f"national={national['child_population_index_2035']}/{national['child_population_index_2050']}"
    )
    return live, national


def test_ipss_future_child_population_ground_truth() -> None:
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    assert master["source"]["xlsx_url"] == IPSS_XLSX_URL
    assert master["source"]["base_year"] == 2020
    assert len(master["prefectures"]) == 47

    committed_by_name = {item["prefecture_name"]: item for item in master["prefectures"]}
    assert set(committed_by_name) == PREFECTURE_SET

    live, national = build_live_ipss_indices()
    assert national == master["national"]

    for name in PREFECTURE_NAMES:
        committed = committed_by_name[name]
        assert live[name]["child_population_index_2035"] == committed["child_population_index_2035"], (
            f"{name}: 2035 live={live[name]['child_population_index_2035']} committed={committed['child_population_index_2035']}"
        )
        assert live[name]["child_population_index_2050"] == committed["child_population_index_2050"], (
            f"{name}: 2050 live={live[name]['child_population_index_2050']} committed={committed['child_population_index_2050']}"
        )


if __name__ == "__main__":
    test_ipss_future_child_population_ground_truth()
    print("ALL 47 PREFECTURES IPSS FUTURE CHILD POPULATION INDICES PASSED LIVE OFFICIAL GROUND TRUTH!")
