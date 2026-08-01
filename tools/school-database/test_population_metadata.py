#!/usr/bin/env python3
"""Validate the 47-prefecture population metadata and its integration into
the prefecture card metadata / renderer (Phase B, decision C: 2020 Census
Table 2-1, Japanese population, same definition for all 47 prefectures)."""

from __future__ import annotations

import json
import math
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POPULATION_JSON = ROOT / "data" / "school-database" / "prefecture-population.json"
PILOT_JSON = ROOT / "data" / "school-database" / "prefecture-population-pilot.json"
CARD_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
INDEX_HTML = ROOT / "tools" / "school-database" / "index.html"

EXPECTED_GROUP_KEYS = [
    "census_preschool_3_5",
    "census_elementary_6_11",
    "census_junior_high_12_14",
    "census_high_school_15_17",
]

PROHIBITED_PLACEHOLDER_TEXT = (
    "全国他都道府県",
    "準備中",
    "順次拡張予定",
    "順次追加予定",
    "全国都道府県の学校データベースを順次追加予定です。",
)


class PortalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.prefecture_card_roots = 0
        self.renderer_scripts = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        if attr.get("data-prefecture-card-root") is not None:
            self.prefecture_card_roots += 1
        if attr.get("src") == "/assets/js/school-database/prefecture-card-renderer.js":
            self.renderer_scripts += 1


def assert_number(value: object, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise AssertionError(f"{name} must be numeric")
    return float(value)


def test_prefecture_population_json() -> None:
    payload = json.loads(POPULATION_JSON.read_text(encoding="utf-8"))
    prefectures = payload["prefectures"]

    assert len(prefectures) == 47, f"expected 47 prefectures, got {len(prefectures)}"

    codes = [p["prefecture_code"] for p in prefectures]
    assert len(set(codes)) == 47, "prefecture_code に重複があります"
    names = [p["prefecture_name"] for p in prefectures]
    assert len(set(names)) == 47, "prefecture_name に重複があります"

    reference_dates = {p["reference_date"] for p in prefectures}
    assert reference_dates == {"2020-10-01"}, f"基準日が47県で統一されていません: {reference_dates}"

    scopes = {p["population_scope"] for p in prefectures}
    assert scopes == {"census_japanese_population"}, f"population_scope が統一されていません: {scopes}"

    table_ids = {p["source_table_id"] for p in prefectures}
    assert len(table_ids) == 1, f"source_table_id が47県で統一されていません: {table_ids}"

    for p in prefectures:
        assert p["census_population"] > 0, f"{p['prefecture_name']}: census_population <= 0"
        assert p["census_age_3_17"] > 0, f"{p['prefecture_name']}: census_age_3_17 <= 0"

        group_keys = [g["key"] for g in p["age_groups"]]
        assert group_keys == EXPECTED_GROUP_KEYS, f"{p['prefecture_name']}: age_groups keys mismatch"

        group_sum = sum(g["population"] for g in p["age_groups"])
        assert group_sum == p["census_age_3_17"], (
            f"{p['prefecture_name']}: 4区分合計({group_sum}) != census_age_3_17({p['census_age_3_17']})"
        )

        recomputed_share = round((p["census_age_3_17"] / p["census_population"]) * 100, 6)
        assert math.isclose(recomputed_share, p["share_of_census_population_percent"], abs_tol=1e-6), (
            f"{p['prefecture_name']}: 割合の再計算が一致しません"
        )

        for g in p["age_groups"]:
            g_share = round((g["population"] / p["census_population"]) * 100, 6)
            assert math.isclose(g_share, g["share_of_census_population_percent"], abs_tol=1e-6), (
                f"{p['prefecture_name']}/{g['key']}: 区分割合の再計算が一致しません"
            )

        assert p["definition_note"], f"{p['prefecture_name']}: definition_note が空です"
        assert p["source_url"].startswith("https://"), f"{p['prefecture_name']}: source_url が不正です"


def test_card_metadata_population_integration() -> None:
    payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    prefectures = payload["prefectures"]
    assert len(prefectures) == 47

    population_payload = json.loads(POPULATION_JSON.read_text(encoding="utf-8"))
    population_by_code = {p["prefecture_code"]: p for p in population_payload["prefectures"]}

    codes = [p["prefecture_code"] for p in prefectures]
    assert len(set(codes)) == 47, "prefecture_code に重複があります（カードメタデータ）"
    assert set(codes) == set(population_by_code), "47都道府県が一致しません（カードメタデータ vs 人口データ）"

    for prefecture in prefectures:
        pop = prefecture["population"]
        assert pop["available"] is True, f"{prefecture['prefecture_name']}: population.available が true ではありません"
        assert pop["population_scope"] == "census_japanese_population"
        assert pop["reference_date"] == "2020-10-01"

        source_ref = population_by_code[prefecture["prefecture_code"]]
        assert pop["census_population"] == source_ref["census_population"]
        assert pop["census_age_3_17"] == source_ref["census_age_3_17"]

        group_keys = [g["key"] for g in pop["age_groups"]]
        assert group_keys == EXPECTED_GROUP_KEYS
        group_sum = sum(g["population"] for g in pop["age_groups"])
        assert group_sum == pop["census_age_3_17"], (
            f"{prefecture['prefecture_name']}: カードメタデータの4区分合計が3〜17歳人口と一致しません"
        )

        assert pop["source"]["table_id"] == source_ref["source_table_id"]
        assert pop["notes"], f"{prefecture['prefecture_name']}: notes が空です"
        assert pop["population_scope_label"] == "人口（日本国籍）"
        assert pop["reference_date_label"] == "統計基準日"
        assert pop["reference_date_display"] == "2020年10月1日現在"
        assert pop["source_short_label"] == "令和2年国勢調査"
        assert pop["age_groups_label"] == "校種相当年齢人口"
        assert pop["footer_note"], f"{prefecture['prefecture_name']}: footer_note が空です"
        assert "実際の在学者数ではありません" in pop["footer_note"]
        for group in pop["age_groups"]:
            assert group["label"] in ("幼児期", "小学校期", "中学校期", "高校期"), (
                f"{prefecture['prefecture_name']}: 想定外の年齢区分ラベル {group['label']!r}"
            )

    # 東京都だけ別のキー・定義になっていないことを明示的に確認する。
    tokyo = next(p for p in prefectures if p["prefecture_code"] == "tokyo")
    other = next(p for p in prefectures if p["prefecture_code"] != "tokyo")
    assert set(tokyo["population"].keys()) == set(other["population"].keys()), (
        "東京都のpopulationキー構造が他都道府県と異なります"
    )
    assert "japanese_population" not in tokyo["population"], (
        "東京都のpopulationに旧住基パイロットのキーが残っています"
    )


def test_pilot_json_preserved_as_research_data() -> None:
    """2026年住基パイロット値は研究資料として保存するが、本番表示には使わない
    （Phase A/Bの決定Cに基づく方針）。"""
    payload = json.loads(PILOT_JSON.read_text(encoding="utf-8"))
    assert payload["pilot_scope"] == "tokyo-only"
    tokyo = payload["prefectures"]["tokyo"]
    assert tokyo["reference_date"] == "2026-01-01"
    assert tokyo["japanese_population"] == 13293851


def test_portal_html() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    parser = PortalParser()
    parser.feed(html)

    assert parser.prefecture_card_roots == 1
    assert parser.renderer_scripts == 1
    for prohibited in PROHIBITED_PLACEHOLDER_TEXT:
        assert prohibited not in html
    assert "<button disabled" not in html
    assert "population-pilot-card" not in html


if __name__ == "__main__":
    test_prefecture_population_json()
    test_card_metadata_population_integration()
    test_pilot_json_preserved_as_research_data()
    test_portal_html()
    print("47-prefecture population metadata validation passed")
