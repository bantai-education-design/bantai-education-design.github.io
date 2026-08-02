#!/usr/bin/env python3
"""Regenerate the 校種×設置区分 matrix-style "収録範囲" tables used by the
prefectures whose individual page does NOT use the single-件数-column table
handled by enrich_prefecture_pages.py (東京都・埼玉県, both instead show a
column per establishment type).

Supersedes regenerate_tokyo_matrix.py (東京都限定) — now also regenerates
埼玉県, whose table previously grouped several school types together
(「中学校・義務教育学校」「高等学校・中等教育学校」) using stale counts.
Both prefectures are now broken out into the full 7 school-type rows,
computed directly from their data/school-database/{slug}.json files.

Establishment-type columns are included only if at least one record of
that type exists anywhere in the prefecture's data (currently 公立/私立
for both; 国立/その他 are omitted rather than shown as a permanent
placeholder column). A cell for a school type / establishment combination
that genuinely has zero records (e.g. 埼玉県の義務教育学校 has no 私立
schools) is rendered as "0校"/"0園" in muted gray, distinct from the green
"✓ (N校)" style used for a present-and-nonzero cell.

Re-running this script is idempotent (replaces the previously-generated
table via marker comments rather than duplicating it)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHOOL_DB_DIR = ROOT / "data" / "school-database"
PAGE_DIR = ROOT / "tools" / "school-database"

SCHOOL_TYPE_ORDER = [
    "幼稚園", "幼保連携型認定こども園", "小学校", "中学校",
    "義務教育学校", "高等学校", "中等教育学校", "特別支援学校",
]
UNIT = {"幼稚園": "園", "幼保連携型認定こども園": "園"}
ESTABLISHMENT_ORDER = ["国立", "公立", "私立", "その他"]

MATRIX_SLUGS = ["tokyo", "saitama"]


def format_number(n: int) -> str:
    return f"{n:,}"


def build_matrix_html(records: list[dict], marker_start: str, marker_end: str) -> tuple[str, int]:
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
    table_html = f"""{marker_start}
            <table style="width:100%; max-width:650px; border-collapse:collapse; margin-bottom:12px; font-size:0.8rem; background:#fff; border:1px solid #e6dbb8; text-align:left;">
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
            {marker_end}"""
    return table_html, total


def process_prefecture(slug: str) -> None:
    json_path = SCHOOL_DB_DIR / f"{slug}.json"
    page_path = PAGE_DIR / slug / "index.html"
    marker_start = f"<!-- {slug}-matrix-table:start -->"
    marker_end = f"<!-- {slug}-matrix-table:end -->"

    records = json.loads(json_path.read_text(encoding="utf-8"))
    table_html, total = build_matrix_html(records, marker_start, marker_end)

    html = page_path.read_text(encoding="utf-8")

    header_match = re.search(r"(本データベースの収録範囲[（(]\s*合計\s*)[\d,]+(\s*校・園[）)])", html)
    if not header_match:
        raise ValueError(f"{slug}: 収録範囲の見出しが見つかりません")
    html = html[: header_match.start()] + header_match.group(1) + format_number(total) + header_match.group(2) + html[header_match.end() :]

    if marker_start in html:
        pattern = re.compile(re.escape(marker_start) + r".*?" + re.escape(marker_end), re.S)
        html = pattern.sub(table_html, html)
    else:
        table_match = re.search(r"<table.*?</table>", html, re.S)
        if not table_match:
            raise ValueError(f"{slug}: 既存の収録範囲テーブルが見つかりません")
        html = html[: table_match.start()] + table_html + html[table_match.end() :]

    page_path.write_text(html, encoding="utf-8")
    print(f"Regenerated {slug} matrix table: total={total}")


def main() -> None:
    for slug in MATRIX_SLUGS:
        process_prefecture(slug)


if __name__ == "__main__":
    main()
