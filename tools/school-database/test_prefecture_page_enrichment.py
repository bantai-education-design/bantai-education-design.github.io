#!/usr/bin/env python3
"""Validate the per-prefecture page summary section (population / education
statistics / school count / school-type composition) against national-analytics-dataset.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHOOL_DB_DIR = ROOT / 'tools' / 'school-database'
PREFECTURE_METADATA_JSON = ROOT / 'data' / 'school-database' / 'prefecture-metadata.json'
ANALYTICS_DATASET_JSON = ROOT / 'data' / 'school-database' / 'national-analytics-dataset.json'
CSS_PATH = ROOT / 'assets' / 'css' / 'school-database.css'

SPECIAL_TABLE_SLUGS = {'tokyo', 'saitama'}

def format_number(n: int) -> str:
    return f"{n:,}"

def test_summary_section_present_exactly_once_all_47() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding='utf-8'))
    for meta in prefecture_metadata:
        slug = meta['slug']
        html = (SCHOOL_DB_DIR / slug / 'index.html').read_text(encoding='utf-8')
        count = html.count('<!-- pref-summary-section:start -->')
        assert count == 1, f"{slug}: pref-summary-sectionが{count}回出現しています"
        assert html.count('<!-- pref-summary-section:end -->') == 1, f"{slug}: 終了マーカーの出現回数が不正です"

def test_summary_values_recomputable_from_source() -> None:
    dataset = json.loads(ANALYTICS_DATASET_JSON.read_text(encoding='utf-8'))
    pref_by_code = {p['code']: p for p in dataset['prefectures']}

    for code, pref in pref_by_code.items():
        html = (SCHOOL_DB_DIR / code / 'index.html').read_text(encoding='utf-8')
        section_match = re.search(
            r'<!-- pref-summary-section:start -->(.*?)<!-- pref-summary-section:end -->', html, re.S
        )
        assert section_match, f"{code}: サマリーセクションが見つかりません"
        section = section_match.group(1)

        # Card 1: Total pop
        tot_man = pref['total_population'] / 10000.0
        tot_man_str = f"{tot_man:,.1f}"
        assert tot_man_str in section, f"{code}: 総人口（{tot_man_str}万人）がサマリーに見つかりません"

        # Card 2: Elem pop per school & rank
        elem_per_sch = pref['elem_pop_per_school']
        rank = pref['ranks']['elem_pop_per_school']
        assert f"{elem_per_sch:.1f}" in section, f"{code}: 1校あたり学齢人口（{elem_per_sch:.1f}）が見つかりません"
        assert f"全国{rank}位" in section, f"{code}: 順位（全国{rank}位）が見つかりません"

        # Card 3: Total school count
        tot_sch = format_number(pref['total_school_count'])
        assert tot_sch in section, f"{code}: 学校数合計（{tot_sch}）が一致しません"

        # Card 4: Student-teacher ratio
        st_ratio = f"{pref['student_teacher_ratio']:.1f}"
        assert st_ratio in section, f"{code}: 教員1人あたり児童数（{st_ratio}）が一致しません"

def test_shuuroku_header_total_matches_current_data_all_47() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding='utf-8'))
    for meta in prefecture_metadata:
        slug = meta['slug']
        html = (SCHOOL_DB_DIR / slug / 'index.html').read_text(encoding='utf-8')
        header_match = re.search(r'本データベースの収録範囲[（(]\s*合計\s*([\d,]+)\s*校・園[）)]', html)
        assert header_match, f"{slug}: 収録範囲の見出しが見つかりません"
        assert header_match.group(1) == format_number(meta['total']), (
            f"{slug}: 収録範囲見出しの合計が現行データと一致しません"
        )

def test_shuuroku_table_rows_refreshed_for_simple_table_pages() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding='utf-8'))
    for meta in prefecture_metadata:
        slug = meta['slug']
        if slug in SPECIAL_TABLE_SLUGS:
            continue
        html = (SCHOOL_DB_DIR / slug / 'index.html').read_text(encoding='utf-8')
        rows = re.findall(
            r'font-weight:600;">([^<]+)</td><td[^>]*font-weight:700;">([\d,]+)[校園]</td>', html
        )
        row_counts = {name: int(count.replace(',', '')) for name, count in rows}
        expected_counts = {k: v for k, v in meta['school_type_counts'].items() if v > 0}
        assert row_counts == expected_counts, (
            f"{slug}: 収録範囲テーブルの内訳が現行データと一致しません"
        )

def test_css_classes_defined() -> None:
    css = CSS_PATH.read_text(encoding='utf-8')
    for cls in [
        '.pref-summary-section', '.pref-summary-grid', '.pref-summary-card',
        '.pref-summary-label', '.pref-summary-value', '.pref-summary-sub',
        '.pref-summary-source', '.pref-summary-chips', '.pref-summary-chip',
        '.pref-summary-note',
    ]:
        assert cls in css, f"CSSに{cls}が定義されていません"

if __name__ == '__main__':
    test_summary_section_present_exactly_once_all_47()
    test_summary_values_recomputable_from_source()
    test_shuuroku_header_total_matches_current_data_all_47()
    test_shuuroku_table_rows_refreshed_for_simple_table_pages()
    test_css_classes_defined()
    print('Prefecture page enrichment validation passed successfully.')
