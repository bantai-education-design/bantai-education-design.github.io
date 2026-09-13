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

def test_official_2020_census_national_totals_and_aging_rates() -> None:
    dataset = json.loads(ANALYTICS_DATASET_JSON.read_text(encoding='utf-8'))
    nat = dataset['national_summary']
    prefs = dataset['prefectures']

    # 1. National Total Population (Official 2020 Census Confirmed Figure)
    assert nat['total_population'] == 126146099, f"全国総人口（期待値: 126,146,099人, 実際: {nat['total_population']:,}人）"
    
    # 2. National 65+ Population (Official 2020 Census Confirmed Figure with Age Imputed)
    assert nat['elderly_65_plus'] == 36026632, f"全国65歳以上人口（期待値: 36,026,632人, 実際: {nat['elderly_65_plus']:,}人）"
    
    # 3. National Aging Rate (Official 2020 Census Confirmed Figure)
    assert nat['aging_rate'] == 28.6, f"全国高齢化率（期待値: 28.6%, 実際: {nat['aging_rate']}%）"

    # 4. Prefecture Sum Total Population Match (Exact equality 126,146,099)
    sum_pref_pop = sum(p['total_population'] for p in prefs)
    assert sum_pref_pop == 126146099, f"47都道府県総人口合計が全国確定値126,146,099人と不一致（合計: {sum_pref_pop:,}人）"

    # 5. Akita Prefecture (Highest Aging Rate in Japan: 37.5%, 65+ Pop: 359,687)
    akita = next(p for p in prefs if p['code'] == 'akita')
    assert akita['elderly_65_plus'] == 359687, f"秋田県65歳以上人口（期待値: 359,687人, 実際: {akita['elderly_65_plus']:,}人）"
    assert akita['aging_rate'] == 37.5, f"秋田県高齢化率（期待値: 37.5%, 実際: {akita['aging_rate']}%）"
    assert akita['ranks']['aging_rate'] == 1, f"秋田県高齢化率順位（期待値: 1位, 実際: {akita['ranks']['aging_rate']}位）"

    # 6. Tokyo (Tokyo Aging Rate: 22.6%, 65+ Pop: 3,178,054)
    tokyo = next(p for p in prefs if p['code'] == 'tokyo')
    assert tokyo['elderly_65_plus'] == 3178054, f"東京都65歳以上人口（期待値: 3,178,054人, 実際: {tokyo['elderly_65_plus']:,}人）"
    assert tokyo['aging_rate'] == 22.6, f"東京都高齢化率（期待値: 22.6%, 実際: {tokyo['aging_rate']}%）"

    # 7. Okinawa Prefecture (Lowest Aging Rate in Japan: 22.5%, Rank 47)
    okinawa = next(p for p in prefs if p['code'] == 'okinawa')
    assert okinawa['aging_rate'] == 22.5, f"沖縄県高齢化率（期待値: 22.5%, 実際: {okinawa['aging_rate']}%）"
    assert okinawa['ranks']['aging_rate'] == 47, f"沖縄県高齢化率順位（期待値: 47位, 実際: {okinawa['ranks']['aging_rate']}位）"

    # 8. 24 Refined Indicators Dataset & MEXT 2025 Ground Truth Validation
    assert len(dataset['indicators_definition']) == 24, f"指標数が24件であること（実際: {len(dataset['indicators_definition'])}）"
    assert nat['child_under_15_ratio'] == 11.9, f"全国15歳未満人口割合（期待値: 11.9%, 実際: {nat['child_under_15_ratio']}%）"
    assert nat['pop_change_rate'] == -0.7, f"全国5年人口増減率（期待値: -0.7%, 実際: {nat['pop_change_rate']}%）"
    assert okinawa['child_under_15_ratio'] == 16.9, f"沖縄県15歳未満人口割合（期待値: 16.9%, 実際: {okinawa['child_under_15_ratio']}%）"
    assert okinawa['ranks']['child_under_15_ratio'] == 1, f"沖縄県15歳未満人口割合順位（期待値: 1位, 実際: {okinawa['ranks']['child_under_15_ratio']}位）"
    assert akita['child_under_15_ratio'] == 9.4, f"秋田県15歳未満人口割合（期待値: 9.4%, 実際: {akita['child_under_15_ratio']}%）"
    assert akita['ranks']['child_under_15_ratio'] == 47, f"秋田県15歳未満人口割合順位（期待値: 47位, 実際: {akita['ranks']['child_under_15_ratio']}位）"
    assert 'private_elem_school_ratio' in nat, "private_elem_school_ratioが全国サマリーに含まれること"
    assert 'special_needs_schools_per_100k_age_6_17' in nat, "special_needs_schools_per_100k_age_6_17が全国サマリーに含まれること"
    assert 'ict_teaching_capability' in nat, "ict_teaching_capabilityが全国サマリーに含まれること"
    assert 'waiting_children_per_10k_preschool' in nat, "waiting_children_per_10k_preschoolが全国サマリーに含まれること"

    # 9. MEXT 2025 Official Ground-Truth Exact Match Verification (Tokyo & Saitama & All 47 Prefectures)
    mext_official_path = ROOT / 'data' / 'school-database' / 'mext-school-basic-survey-2025-official.json'
    mext_official = json.loads(mext_official_path.read_text(encoding='utf-8'))
    tokyo_mext = next(p for p in mext_official['prefectures'] if p['prefecture_code'] == 'tokyo')
    assert tokyo_mext['jhs_students'] == 313930, f"東京都中学校生徒数（期待値: 313,930人, 実際: {tokyo_mext['jhs_students']:,}人）"
    assert tokyo_mext['jhs_teachers'] == 20880, f"東京都中学校教員数（期待値: 20,880人, 実際: {tokyo_mext['jhs_teachers']:,}人）"

    assert tokyo['elem_school_count'] == 1315, f"東京都小学校数（期待値: 1,315校, 実際: {tokyo['elem_school_count']}校）"
    assert tokyo['elem_students'] == 616084, f"東京都小学校児童数（期待値: 616,084人, 実際: {tokyo['tokyo_students'] if 'tokyo_students' in tokyo else tokyo['elem_students']:,}人）"
    assert tokyo['elem_teachers'] == 37441, f"東京都小学校教員数（期待値: 37,441人, 実際: {tokyo['elem_teachers']:,}人）"
    assert tokyo['jhs_school_count'] == 796, f"東京都中学校数（期待値: 796校, 実際: {tokyo['jhs_school_count']}校）"
    assert tokyo['private_elem_school_ratio'] == 4.1, f"東京都私立小学校比率（期待値: 4.1%, 実際: {tokyo['private_elem_school_ratio']}%）"
    assert tokyo['jhs_student_teacher_ratio'] == 15.0, f"東京都中学校教員1人あたり生徒数（期待値: 15.0人/教員, 実際: {tokyo['jhs_student_teacher_ratio']}人/教員）"
    assert tokyo['elem_enrolled_per_school'] == 468.5, f"東京都小学校1校あたり実児童数（期待値: 468.5人/校, 実際: {tokyo['elem_enrolled_per_school']}人/校）"
    assert tokyo['jhs_enrolled_per_school'] == 394.4, f"東京都中学校1校あたり生徒数（期待値: 394.4人/校, 実際: {tokyo['jhs_enrolled_per_school']}人/校）"

    # Saitama Ground Truth Exact Match
    saitama_mext = next(p for p in mext_official['prefectures'] if p['prefecture_code'] == 'saitama')
    saitama = next(p for p in prefs if p['code'] == 'saitama')
    assert saitama_mext['elem_schools'] == 787, f"埼玉県小学校数（期待値: 787校, 実際: {saitama_mext['elem_schools']}校）"
    assert saitama_mext['private_elem_schools'] == 6, f"埼玉県私立小学校数（期待値: 6校, 実際: {saitama_mext['private_elem_schools']}校）"
    assert saitama_mext['elem_classes'] == 14162, f"埼玉県小学校学級数（期待値: 14,162学級, 実際: {saitama_mext['elem_classes']:,}学級）"
    assert saitama_mext['elem_students'] == 345524, f"埼玉県小学校児童数（期待値: 345,524人, 実際: {saitama_mext['elem_students']:,}人）"
    assert saitama_mext['elem_teachers'] == 22072, f"埼玉県小学校教員数（期待値: 22,072人, 実際: {saitama_mext['elem_teachers']:,}人）"
    assert saitama_mext['jhs_schools'] == 441, f"埼玉県中学校数（期待値: 441校, 実際: {saitama_mext['jhs_schools']}校）"
    assert saitama_mext['jhs_classes'] == 6112, f"埼玉県中学校学級数（期待値: 6,112学級, 実際: {saitama_mext['jhs_classes']:,}学級）"
    assert saitama_mext['jhs_students'] == 180252, f"埼玉県中学校生徒数（期待値: 180,252人, 実際: {saitama_mext['jhs_students']:,}人）"
    assert saitama['private_elem_school_ratio'] == 0.8, f"埼玉県私立小学校比率（期待値: 0.8%, 実際: {saitama['private_elem_school_ratio']}%）"

    # All 47 Prefectures Consistency Check against MEXT Master
    mext_dict = {p['prefecture_code']: p for p in mext_official['prefectures']}
    for pref_item in prefs:
        p_code = pref_item['code']
        assert p_code in mext_dict, f"{p_code}がMEXTマスターJSONに見つかりません"
        m_item = mext_dict[p_code]
        assert pref_item['elem_school_count'] == m_item['elem_schools'], f"{p_code}: elem_school_count不一致"
        assert pref_item['jhs_school_count'] == m_item['jhs_schools'], f"{p_code}: jhs_school_count不一致"
        assert pref_item['elem_students'] == m_item['elem_students'], f"{p_code}: elem_students不一致"
        assert pref_item['elem_teachers'] == m_item['elem_teachers'], f"{p_code}: elem_teachers不一致"

def test_summary_values_recomputable_from_source() -> None:
    card_meta_path = ROOT / 'data' / 'school-database' / 'prefecture-card-metadata.json'
    card_meta_json = json.loads(card_meta_path.read_text(encoding='utf-8'))
    card_by_code = {p['prefecture_code']: p for p in card_meta_json['prefectures']}

    for code, card in card_by_code.items():
        if code in SPECIAL_TABLE_SLUGS:
            continue
        html = (SCHOOL_DB_DIR / code / 'index.html').read_text(encoding='utf-8')
        section_match = re.search(
            r'<!-- pref-summary-section:start -->(.*?)<!-- pref-summary-section:end -->', html, re.S
        )
        assert section_match, f"{code}: サマリーセクションが見つかりません"
        section = section_match.group(1)

        # Card 1: Total pop
        pop_str = format_number(card['population']['census_population'])
        assert pop_str in section, f"{code}: 人口（{pop_str}人）がサマリーに見つかりません"

        # Card 3: Total school count
        tot_sch = format_number(card['school_database']['record_count'])
        assert tot_sch in section, f"{code}: 学校数合計（{tot_sch}）が一致しません"

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
    test_official_2020_census_national_totals_and_aging_rates()
    test_summary_values_recomputable_from_source()
    test_shuuroku_header_total_matches_current_data_all_47()
    test_shuuroku_table_rows_refreshed_for_simple_table_pages()
    test_css_classes_defined()
    print('Prefecture page enrichment & 2020 Census official statistics validation passed successfully.')
