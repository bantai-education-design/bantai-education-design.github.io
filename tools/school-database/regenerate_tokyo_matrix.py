#!/usr/bin/env python3
"""Regenerate the 東京都 "収録範囲" 校種×設置区分 matrix table in
tools/school-database/tokyo/index.html directly from
data/school-database/tokyo.json (the current, authoritative 3,493-record
dataset — not the legacy data/tokyo_public_schools_address_2025.json,
3,509 records).

Unlike the other 46 prefectures (single 件数 column, handled by
enrich_prefecture_pages.py), Tokyo's page has always used a 校種×設置区分
matrix table (columns per establishment type). This script recomputes that
matrix, and the header total, from source data so the two can never drift
out of sync again.

Establishment-type columns are included only if at least one record of
that type exists anywhere in the data (currently 公立/私立; 国立 has zero
records and is omitted rather than shown as a permanent "準備中" column).
A cell for a school type / establishment combination that genuinely has
zero records (e.g. 義務教育学校 has no 私立 schools) is rendered as "0校"
in muted gray, distinct from the green "✓ (N校)" style used for a
present-and-nonzero cell.

Re-running this script is idempotent (replaces the previously-generated
table via marker comments rather than duplicating it)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOKYO_JSON = ROOT / "data" / "school-database" / "tokyo.json"
PAGE_PATH = ROOT / "tools" / "school-database" / "tokyo" / "index.html"

SCHOOL_TYPE_ORDER = [
    "幼稚園", "幼保連携型認定こども園", "小学校", "中学校",
    "義務教育学校", "高等学校", "中等教育学校", "特別支援学校",
]
UNIT = {"幼稚園": "園", "幼保連携型認定こども園": "園"}
ESTABLISHMENT_ORDER = ["国立", "公立", "私立", "その他"]

MATRIX_START = "<!-- tokyo-matrix-table:start -->"
MATRIX_END = "<!-- tokyo-matrix-table:end -->"


def format_number(n: int) -> str:
    return f"{n:,}"


def build_matrix_html(records: list[dict]) -> tuple[str, int]:
    cross: dict[str, dict[str, int]] = {}
    for r in records:
        cross.setdefault(r["school_type"], {})
        cross[r["school_type"]][r["establishment_type"]] = cross[r["school_type"]].get(r["establishment_type"], 0) + 1

    est_present = [e for e in ESTABLISHMENT_ORDER if any(e in ests for ests in cross.values())]
    type_present = [t for t in SCHOOL_TYPE_ORDER if t in cross]

    header_cells = "".join(f'<th style="padding:4px 8px; text-align:center;">{est}</th>' for est in est_present)
    header_cells += '<th style="padding:4px 8px; text-align:center;">計</th>'

    body_rows = []
    for t in type_present:
        unit = UNIT.get(t, "校")
        cells = []
        row_total = 0
        for est in est_present:
            count = cross[t].get(est, 0)
            row_total += count
            if count > 0:
                cells.append(
                    f'<td style="padding:4px 8px; text-align:center; color:#27ae60; font-weight:700;">'
                    f"✓ ({format_number(count)}{unit})</td>"
                )
            else:
                cells.append(f'<td style="padding:4px 8px; text-align:center; color:#95a5a6;">0{unit}</td>')
        cells.append(f'<td style="padding:4px 8px; text-align:center; font-weight:700;">{format_number(row_total)}{unit}</td>')
        body_rows.append(
            f'<tr style="border-bottom:1px solid #f2e9cc;"><td style="padding:4px 8px; font-weight:600;">{t}</td>'
            + "".join(cells) + "</tr>"
        )

    total = len(records)
    table_html = f"""{MATRIX_START}
            <table style="width:100%; max-width:600px; border-collapse:collapse; margin-bottom:12px; font-size:0.8rem; background:#fff; border:1px solid #e6dbb8; text-align:left;">
              <thead>
                <tr style="background:#fcf8e3; border-bottom:1px solid #e6dbb8; font-weight:700; color:#8c6b00;">
                  <th style="padding:4px 8px;">学校種別</th>
                  {header_cells}
                </tr>
              </thead>
              <tbody>
                {"".join(body_rows)}
              </tbody>
            </table>
            {MATRIX_END}"""
    return table_html, total


def main() -> None:
    records = json.loads(TOKYO_JSON.read_text(encoding="utf-8"))
    table_html, total = build_matrix_html(records)

    html = PAGE_PATH.read_text(encoding="utf-8")

    header_match = re.search(r"(本データベースの収録範囲[（(]\s*合計\s*)[\d,]+(\s*校・園[）)])", html)
    if not header_match:
        raise ValueError("収録範囲の見出しが見つかりません")
    html = html[: header_match.start()] + header_match.group(1) + format_number(total) + header_match.group(2) + html[header_match.end() :]

    if MATRIX_START in html:
        pattern = re.compile(re.escape(MATRIX_START) + r".*?" + re.escape(MATRIX_END), re.S)
        html = pattern.sub(table_html, html)
    else:
        table_match = re.search(r"<table.*?</table>", html, re.S)
        if not table_match:
            raise ValueError("既存の収録範囲テーブルが見つかりません")
        html = html[: table_match.start()] + table_html + html[table_match.end() :]

    PAGE_PATH.write_text(html, encoding="utf-8")
    print(f"Regenerated Tokyo matrix table: total={total}")


if __name__ == "__main__":
    main()
