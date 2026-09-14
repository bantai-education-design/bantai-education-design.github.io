#!/usr/bin/env python3
"""Strict live Ground Truth audit for ICT capability and waiting children.

Every CI run downloads the current official source files directly and validates the
47 prefecture values against the committed external-stat master. There is no local
fallback.

Official sources:
- MEXT / e-Stat FY2024 School ICT survey, Table 2 (1) Total
  statInfId=000040365967
- Children and Families Agency, daycare-related status summary as of 2025-04-01
  official workbook "資料1～6", sheet "資料3"
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
CARD_METADATA_PATH = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
EXT_STATS_PATH = ROOT / "data" / "school-database" / "prefecture-education-external-stats.json"

ICT_STAT_ID = "000040365967"
ICT_URL = f"https://www.e-stat.go.jp/stat-search/file-download?fileKind=0&statInfId={ICT_STAT_ID}"
WAITING_CHILDREN_URL = (
    "https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/"
    "b0a8057b-34bf-4c20-84fb-ae592708ca9b/1a728dcc/"
    "20250828_policies_hoiku_torimatome_r7_02.xlsx"
)

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
    text = unicodedata.normalize("NFKC", str(value)).replace("\u3000", " ").strip()
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


def _fetch_xlsx(url: str, label: str) -> openpyxl.Workbook:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    assert data[:2] == b"PK", f"{label}: downloaded payload is not XLSX"
    print(f"[Official Live Audit] {label} downloaded live ({len(data):,} bytes)")
    return openpyxl.load_workbook(io.BytesIO(data), data_only=True)


def _find_prefecture_rows(sheet) -> dict[str, int]:
    found: dict[str, int] = {}
    for row in range(1, sheet.max_row + 1):
        for col in range(1, sheet.max_column + 1):
            text = _norm(sheet.cell(row, col).value)
            if text in PREFECTURE_SET:
                assert text not in found, f"{sheet.title}: duplicate prefecture row for {text}"
                found[text] = row
                break
    assert set(found) == PREFECTURE_SET, (
        f"{sheet.title}: expected all 47 prefectures, found {len(found)}"
    )
    return found


def _find_header_column(sheet, token: str, *, max_row: int = 8) -> int:
    wanted = _norm(token)
    matches: list[int] = []
    for row in range(1, min(sheet.max_row, max_row) + 1):
        for col in range(1, sheet.max_column + 1):
            text = _norm(sheet.cell(row, col).value)
            if wanted in text:
                matches.append(col)
    assert matches, f"{sheet.title}: header token {token!r} not found"
    return matches[0]


def build_live_ict_category_a() -> dict[str, float]:
    wb = _fetch_xlsx(ICT_URL, f"MEXT/e-Stat ICT Table 2 (1), statInfId={ICT_STAT_ID}")
    assert "県教員（合計）" in wb.sheetnames, f"Unexpected ICT sheets: {wb.sheetnames}"
    sheet = wb["県教員（合計）"]

    # The official table labels this metric explicitly as "大項目A 平均".
    metric_col = _find_header_column(sheet, "大項目A")
    assert _norm(sheet.cell(4, metric_col).value) == "大項目A平均", (
        f"ICT Category A header changed: {sheet.cell(4, metric_col).value!r}"
    )

    rows = _find_prefecture_rows(sheet)
    values: dict[str, float] = {}
    for name, row in rows.items():
        value = _number(sheet.cell(row, metric_col).value)
        assert value is not None and 0 <= value <= 100, f"{name}: invalid ICT value {value}"
        values[name] = round(value, 1)

    # Row after the 47 prefectures is the official aggregate row in this table.
    total_rows = [
        r for r in range(1, sheet.max_row + 1)
        if _norm(sheet.cell(r, 2).value) in {"合計", "計"}
    ]
    assert total_rows, "ICT official aggregate row not found"
    national = _number(sheet.cell(total_rows[-1], metric_col).value)
    assert national == 90.7, f"ICT official national Category A must be 90.7, got {national}"

    print(
        f"[Official Live Audit] ICT Category A: sheet={sheet.title!r}, "
        f"column={metric_col}, prefectures=47, national={national}"
    )
    return values


def build_live_waiting_children() -> dict[str, int]:
    wb = _fetch_xlsx(WAITING_CHILDREN_URL, "CFA waiting-children workbook (2025-04-01)")
    assert "資料3" in wb.sheetnames, f"CFA official sheet '資料3' missing: {wb.sheetnames}"
    sheet = wb["資料3"]
    assert "待機児童数集約表" in _norm(sheet.cell(1, 1).value), (
        f"Unexpected CFA 資料3 title: {sheet.cell(1, 1).value!r}"
    )

    rows = _find_prefecture_rows(sheet)

    # There are two waiting-child columns in 資料3: prefectures and designated/
    # core cities. Select the column whose 47 prefecture rows are all numeric and
    # whose sum equals the official national prefecture total, 2,254.
    candidate_cols = []
    for col in range(1, sheet.max_column + 1):
        header = _norm(sheet.cell(4, col).value)
        if "待機児童数" not in header:
            continue
        values = [_number(sheet.cell(row, col).value) for row in rows.values()]
        if all(value is not None for value in values):
            candidate_cols.append((col, values))

    matching = [
        (col, values) for col, values in candidate_cols
        if abs(sum(value for value in values if value is not None) - 2254.0) < 1e-9
    ]
    assert len(matching) == 1, (
        f"Could not uniquely identify prefecture waiting-child column: "
        f"candidates={[col for col, _ in candidate_cols]}, "
        f"matching={[col for col, _ in matching]}"
    )
    metric_col = matching[0][0]

    result: dict[str, int] = {}
    for name, row in rows.items():
        value = _number(sheet.cell(row, metric_col).value)
        assert value is not None and value >= 0 and value.is_integer(), (
            f"{name}: invalid waiting-children count {value}"
        )
        result[name] = int(value)

    assert sum(result.values()) == 2254
    print(
        f"[Official Live Audit] Waiting children: sheet={sheet.title!r}, "
        f"column={metric_col}, prefectures=47, total=2,254"
    )
    return result


def test_external_stats_live_ground_truth() -> None:
    card_payload = json.loads(CARD_METADATA_PATH.read_text(encoding="utf-8"))
    ext_payload = json.loads(EXT_STATS_PATH.read_text(encoding="utf-8"))

    name_to_slug = {
        entry["prefecture_name"]: entry["prefecture_code"]
        for entry in card_payload["prefectures"]
    }
    assert set(name_to_slug) == PREFECTURE_SET
    ext_by_slug = {entry["prefecture_code"]: entry for entry in ext_payload["prefectures"]}
    assert len(ext_by_slug) == 47

    live_ict = build_live_ict_category_a()
    live_waiting = build_live_waiting_children()

    for name in PREFECTURE_NAMES:
        slug = name_to_slug[name]
        committed = ext_by_slug[slug]
        assert live_ict[name] == committed["ict_teaching_capability"], (
            f"{name}: ICT live={live_ict[name]} committed={committed['ict_teaching_capability']}"
        )
        assert live_waiting[name] == committed["waiting_children_count"], (
            f"{name}: waiting live={live_waiting[name]} committed={committed['waiting_children_count']}"
        )


if __name__ == "__main__":
    test_external_stats_live_ground_truth()
    print(
        "ALL 47 PREFECTURES ICT & WAITING-CHILDREN LIVE OFFICIAL "
        "GROUND TRUTH TESTS PASSED SUCCESSFULLY!"
    )
