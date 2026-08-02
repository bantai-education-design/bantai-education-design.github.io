#!/usr/bin/env python3
"""Enrich each of the 47 individual prefecture pages
(tools/school-database/{slug}/index.html) with a compact summary section
(population, education statistics, school count, school-type composition,
establishment breakdown) placed right after the page-hero, and refresh the
existing "収録範囲" (school-type count) table with current data.

These pages are static HTML (not JS-rendered like the portal), so all
values are inlined per page from data already in this repository
(prefecture-metadata.json / prefecture-card-metadata.json) rather than
computed client-side. This mirrors add_silhouette_to_prefecture_pages.py's
approach of patching static HTML via regex.

This script is idempotent: re-running it replaces the previously-inserted
summary block (marked by PREF_SUMMARY_START/END comments) and regenerates
the 収録範囲 table from current data, rather than appending duplicates.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHOOL_DB_DIR = ROOT / "tools" / "school-database"
PREFECTURE_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-metadata.json"
CARD_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"

# 学校種の表示順（MEXT学校基本調査の分類順に準拠）。値が0の種別は表示しない。
SCHOOL_TYPE_ORDER = [
    "幼稚園", "幼保連携型認定こども園", "小学校", "中学校",
    "義務教育学校", "高等学校", "中等教育学校", "特別支援学校",
]
# 件数の単位（校 or 園）。
SCHOOL_TYPE_UNIT = {
    "幼稚園": "園",
    "幼保連携型認定こども園": "園",
}

ESTABLISHMENT_LABELS = [("national", "国立"), ("public", "公立"), ("private", "私立"), ("other", "その他")]

PREF_SUMMARY_START = "<!-- pref-summary-section:start -->"
PREF_SUMMARY_END = "<!-- pref-summary-section:end -->"


def format_number(n: int) -> str:
    return f"{n:,}"


def build_summary_section(meta: dict, card: dict) -> str:
    population = card["population"]
    education = card["education_profile"]
    school_db = card["school_database"]

    total = meta["total"]
    type_counts = meta["school_type_counts"]
    type_chips = "".join(
        f'<span class="pref-summary-chip">{name}{format_number(type_counts[name])}{SCHOOL_TYPE_UNIT.get(name, "校")}</span>'
        for name in SCHOOL_TYPE_ORDER
        if type_counts.get(name, 0) > 0
    )

    est_counts = meta["establishment_counts"]
    est_chips = "".join(
        f'<span class="pref-summary-chip">{label}{format_number(est_counts[key])}</span>'
        for key, label in ESTABLISHMENT_LABELS
        if est_counts.get(key, 0) > 0
    )

    population_html = ""
    if population.get("available"):
        population_html = f"""
          <div class="pref-summary-card">
            <div class="pref-summary-label">{population["population_scope_label"]}</div>
            <div class="pref-summary-value">{format_number(population["census_population"])}<span>人</span></div>
            <div class="pref-summary-sub">3〜17歳人口 {format_number(population["census_age_3_17"])}人（{population["share_of_census_population_percent"]:.1f}%）</div>
            <div class="pref-summary-source">出典：{population["source_short_label"]}　{population["reference_date_label"]}：{population["reference_date_display"]}</div>
          </div>"""

    education_html = ""
    if education.get("available"):
        education_html = f"""
          <div class="pref-summary-card">
            <div class="pref-summary-label">{education["metric_label"]}</div>
            <div class="pref-summary-value">{education["value"]}<span>{education["unit"]}</span></div>
            <div class="pref-summary-sub">全国平均 {education["national_average"]}{education["unit"]}</div>
            <div class="pref-summary-source">出典：{education["source_short_label"]}　{education["reference_date_display"]}</div>
          </div>"""

    school_count_html = f"""
          <div class="pref-summary-card">
            <div class="pref-summary-label">学校数</div>
            <div class="pref-summary-value">{format_number(total)}<span>校・園</span></div>
            <div class="pref-summary-chips">{type_chips}</div>
          </div>"""

    establishment_html = f"""
          <div class="pref-summary-card">
            <div class="pref-summary-label">設置区分</div>
            <div class="pref-summary-chips pref-summary-chips-large">{est_chips}</div>
          </div>"""

    return f"""{PREF_SUMMARY_START}
    <section class="pref-summary-section">
      <div class="container">
        <div class="pref-summary-grid">{population_html}{education_html}{school_count_html}{establishment_html}
        </div>
        <p class="pref-summary-note">教育統計は特定の1指標を客観的な統計値として表示しているものであり、教育水準を順位付け・評価するものではありません（詳細は<a href="/tools/school-database/">全国学校データベース</a>ページ下部の「教育統計について」を参照）。</p>
      </div>
    </section>
    {PREF_SUMMARY_END}"""


def insert_or_replace_summary(html: str, summary_html: str) -> str:
    if PREF_SUMMARY_START in html:
        pattern = re.compile(
            re.escape(PREF_SUMMARY_START) + r".*?" + re.escape(PREF_SUMMARY_END), re.S
        )
        return pattern.sub(summary_html, html)

    match = re.search(r'<section class="page-hero[^"]*">.*?</section>', html, re.S)
    if not match:
        raise ValueError("page-heroセクションが見つかりません")
    insert_at = match.end()
    return html[:insert_at] + "\n\n    " + summary_html + html[insert_at:]


def refresh_school_type_table(html: str, meta: dict) -> tuple[str, bool]:
    """収録範囲テーブルを現行データで再生成する。見出しの合計件数は、表の
    形式によらず常に現行値へ揃える（東京都のような設置区分別マトリクス表
    でも、新しい統計サマリーと同じ合計数を表示し、ページ内で数字が食い違う
    ことを防ぐ）。単純な学校種別×件数の表（件数列を持つもの）に限り、行の
    内訳も再生成する。マトリクス表（件数列ではなく公立/私立/国立列を持つ）
    は見出しの合計のみ更新し、内訳行は対象外とする。"""
    total = meta["total"]
    type_counts = meta["school_type_counts"]

    header_match = re.search(r"(本データベースの収録範囲[（(]\s*合計\s*)[\d,]+(\s*校・園[）)])", html)
    if header_match:
        html = html[: header_match.start()] + header_match.group(1) + format_number(total) + header_match.group(2) + html[header_match.end() :]

    if not re.search(r"<th[^>]*>件数</th>", html):
        return html, False

    tbody_match = re.search(r"(<tbody>).*?(</tbody>)", html, re.S)
    if not tbody_match:
        return html, False

    pad = "6px 10px" if "padding:6px 10px" in tbody_match.group(0) else "4px 8px"
    rows = "".join(
        f'<tr style="border-bottom:1px solid #f2e9cc;"><td style="padding:{pad}; font-weight:600;">{name}</td>'
        f'<td style="padding:{pad}; text-align:center; font-weight:700;">{format_number(type_counts[name])}{SCHOOL_TYPE_UNIT.get(name, "校")}</td></tr>'
        for name in SCHOOL_TYPE_ORDER
        if type_counts.get(name, 0) > 0
    )
    new_tbody = f"<tbody>\n                {rows}\n              </tbody>"
    html = html[: tbody_match.start()] + new_tbody + html[tbody_match.end() :]
    return html, True


def main() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    meta_by_slug = {m["slug"]: m for m in prefecture_metadata}
    card_by_slug = {p["prefecture_code"]: p for p in card_payload["prefectures"]}

    results = []
    for slug, meta in meta_by_slug.items():
        page_path = SCHOOL_DB_DIR / slug / "index.html"
        if not page_path.is_file():
            results.append(f"SKIP {slug}: index.htmlが見つかりません")
            continue

        card = card_by_slug.get(slug)
        if not card:
            results.append(f"SKIP {slug}: card-metadataが見つかりません")
            continue

        html = page_path.read_text(encoding="utf-8")
        summary_html = build_summary_section(meta, card)
        html = insert_or_replace_summary(html, summary_html)
        html, table_refreshed = refresh_school_type_table(html, meta)
        page_path.write_text(html, encoding="utf-8")
        results.append(f"OK {slug}: summary追加/更新, table_refreshed={table_refreshed}")

    for line in results:
        print(line)
    print(f"\n{len(results)}件処理完了")


if __name__ == "__main__":
    main()
