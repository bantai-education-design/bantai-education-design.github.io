#!/usr/bin/env python3
"""Validate the per-prefecture page summary section (population / education
statistics / school count / school-type composition / establishment
breakdown) inserted by enrich_prefecture_pages.py, and the refreshed
収録範囲 table.

Every displayed number must be independently recomputable from
prefecture-metadata.json / prefecture-card-metadata.json (no hardcoded or
stale values), and the summary block must appear exactly once per page (no
duplicate insertion from repeated script runs)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHOOL_DB_DIR = ROOT / "tools" / "school-database"
PREFECTURE_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-metadata.json"
CARD_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
CSS_PATH = ROOT / "assets" / "css" / "school-database.css"

# refresh_school_type_table()が対象外とする特殊な内訳表（設置区分別マト
# リクス表）を持つページ。収録範囲テーブルの再生成検証からは除外する。
SPECIAL_TABLE_SLUGS = {"tokyo", "saitama"}


def format_number(n: int) -> str:
    return f"{n:,}"


def test_summary_section_present_exactly_once_all_47() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    for meta in prefecture_metadata:
        slug = meta["slug"]
        html = (SCHOOL_DB_DIR / slug / "index.html").read_text(encoding="utf-8")
        count = html.count("<!-- pref-summary-section:start -->")
        assert count == 1, f"{slug}: pref-summary-sectionが{count}回出現しています（重複挿入の疑い）"
        assert html.count("<!-- pref-summary-section:end -->") == 1, f"{slug}: 終了マーカーの出現回数が不正です"


def test_summary_values_recomputable_from_source() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    card_by_slug = {p["prefecture_code"]: p for p in card_payload["prefectures"]}

    for meta in prefecture_metadata:
        slug = meta["slug"]
        card = card_by_slug[slug]
        html = (SCHOOL_DB_DIR / slug / "index.html").read_text(encoding="utf-8")
        section_match = re.search(
            r"<!-- pref-summary-section:start -->(.*?)<!-- pref-summary-section:end -->", html, re.S
        )
        assert section_match, f"{slug}: サマリーセクションが見つかりません"
        section = section_match.group(1)

        population = card["population"]
        if population.get("available"):
            expected_pop = format_number(population["census_population"])
            assert expected_pop in section, f"{slug}: 人口の値が一致しません（期待値{expected_pop}）"
            expected_age = format_number(population["census_age_3_17"])
            assert expected_age in section, f"{slug}: 3〜17歳人口の値が一致しません"
            expected_share = f'{population["share_of_census_population_percent"]:.1f}%'
            assert expected_share in section, f"{slug}: 学齢人口割合の値が一致しません"

        education = card["education_profile"]
        if education.get("available"):
            assert education["metric_label"] in section, f"{slug}: 教育統計の指標名が一致しません"
            assert str(education["value"]) in section, f"{slug}: 教育統計の値が一致しません"
            assert str(education["national_average"]) in section, f"{slug}: 教育統計の全国平均が一致しません"

        expected_total = format_number(meta["total"])
        assert expected_total in section, f"{slug}: 学校数合計が一致しません（期待値{expected_total}）"

        for name, count in meta["school_type_counts"].items():
            if count > 0:
                assert f"{name}{format_number(count)}" in section, (
                    f"{slug}: 校種構成「{name}」の件数がサマリーに一致しません（期待値{count}）"
                )

        est = meta["establishment_counts"]
        est_labels = {"national": "国立", "public": "公立", "private": "私立", "other": "その他"}
        for key, label in est_labels.items():
            if est.get(key, 0) > 0:
                assert f"{label}{format_number(est[key])}" in section, (
                    f"{slug}: 設置区分「{label}」の件数がサマリーに一致しません"
                )


def test_shuuroku_header_total_matches_current_data_all_47() -> None:
    """収録範囲見出しの合計件数は、表の形式（単純表/マトリクス表）に関わらず、
    サマリーセクションと同じ現行の合計と一致していなければならない
    （ページ内で数字が食い違わないことを保証する）。"""
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    for meta in prefecture_metadata:
        slug = meta["slug"]
        html = (SCHOOL_DB_DIR / slug / "index.html").read_text(encoding="utf-8")
        header_match = re.search(r"本データベースの収録範囲[（(]\s*合計\s*([\d,]+)\s*校・園[）)]", html)
        assert header_match, f"{slug}: 収録範囲の見出しが見つかりません"
        assert header_match.group(1) == format_number(meta["total"]), (
            f"{slug}: 収録範囲見出しの合計が現行データと一致しません"
            f"（表示={header_match.group(1)} / 現行={format_number(meta['total'])}）"
        )


def test_shuuroku_table_rows_refreshed_for_simple_table_pages() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    for meta in prefecture_metadata:
        slug = meta["slug"]
        if slug in SPECIAL_TABLE_SLUGS:
            continue
        html = (SCHOOL_DB_DIR / slug / "index.html").read_text(encoding="utf-8")

        rows = re.findall(
            r'font-weight:600;">([^<]+)</td><td[^>]*font-weight:700;">([\d,]+)[校園]</td>', html
        )
        row_counts = {name: int(count.replace(",", "")) for name, count in rows}
        expected_counts = {k: v for k, v in meta["school_type_counts"].items() if v > 0}
        assert row_counts == expected_counts, (
            f"{slug}: 収録範囲テーブルの内訳が現行データと一致しません"
            f"（表示={row_counts} / 現行={expected_counts}）"
        )


def test_css_classes_defined() -> None:
    css = CSS_PATH.read_text(encoding="utf-8")
    for cls in [
        ".pref-summary-section", ".pref-summary-grid", ".pref-summary-card",
        ".pref-summary-label", ".pref-summary-value", ".pref-summary-sub",
        ".pref-summary-source", ".pref-summary-chips", ".pref-summary-chip",
        ".pref-summary-note",
    ]:
        assert cls in css, f"CSSに{cls}が定義されていません"


if __name__ == "__main__":
    test_summary_section_present_exactly_once_all_47()
    test_summary_values_recomputable_from_source()
    test_shuuroku_header_total_matches_current_data_all_47()
    test_shuuroku_table_rows_refreshed_for_simple_table_pages()
    test_css_classes_defined()
    print("Prefecture page enrichment validation passed successfully.")
