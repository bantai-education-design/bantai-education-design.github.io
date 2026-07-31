#!/usr/bin/env python3
"""Validate the prefecture card metadata renderer."""

from __future__ import annotations

import json
import math
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POPULATION_JSON = ROOT / "data" / "school-database" / "prefecture-population-pilot.json"
CARD_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
INDEX_HTML = ROOT / "tools" / "school-database" / "index.html"

EXPECTED_GROUPS = {
    "japanese_preschool_3_5": (3, 5),
    "japanese_elementary_6_11": (6, 11),
    "japanese_junior_high_12_14": (12, 14),
    "japanese_high_school_15_17": (15, 17),
    "japanese_age_3_17": (3, 17),
}

PROHIBITED_CARD_LABELS = ("総人口", "東京都の人口", "学齢人口", "教育年齢人口")
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


def test_population_json() -> None:
    payload = json.loads(POPULATION_JSON.read_text(encoding="utf-8"))
    assert payload["pilot_scope"] == "tokyo-only"
    assert set(payload["prefectures"]) == {"tokyo"}

    tokyo = payload["prefectures"]["tokyo"]
    assert tokyo["reference_date"] == "2026-01-01"
    assert tokyo["population_definition"] == "住民基本台帳に記載された日本人人口"
    assert tokyo["source"]["publisher"] == "東京都総務局統計部"
    assert tokyo["source"]["csv_url"].startswith("https://www.toukei.metro.tokyo.lg.jp/")

    assert tokyo["population_scope"] == "Japanese residents"
    assert tokyo["denominator"] == "japanese_population"
    assert tokyo["foreign_residents_included"] is False
    assert tokyo["all_residents_age_3_17"] is None
    assert "total_population" not in tokyo

    japanese_population = assert_number(tokyo["japanese_population"], "japanese_population")
    assert japanese_population == 13293851

    groups = tokyo["age_groups"]
    assert set(groups) == set(EXPECTED_GROUPS)

    component_population = 0
    for key, age_range in EXPECTED_GROUPS.items():
        group = groups[key]
        assert group["age_range"] == list(age_range)
        assert group["denominator"] == "japanese_population"
        population = assert_number(group["population"], f"{key}.population")
        share = assert_number(
            group["share_of_japanese_population_percent"],
            f"{key}.share_of_japanese_population_percent",
        )
        assert population > 0
        assert 0 < share < 100
        assert math.isclose(share, round(population / japanese_population * 100, 6), abs_tol=0.000001)
        if key != "japanese_age_3_17":
            component_population += int(population)

    assert groups["japanese_age_3_17"]["population"] == 1507197
    assert groups["japanese_age_3_17"]["population"] == component_population

    ratios = tokyo["additional_analysis"]["population_per_school_simple_ratio"]
    for key in (
        "japanese_preschool_3_5",
        "japanese_elementary_6_11",
        "japanese_junior_high_12_14",
        "japanese_high_school_15_17",
    ):
        ratio = ratios[key]
        assert ratio["school_count"] > 0
        assert ratio["population"] == groups[key]["population"]
        assert ratio["population_per_school"] > 0


def test_card_metadata_json() -> None:
    payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    assert payload["population_policy"]["no_dummy_values"] is True
    assert payload["population_policy"]["no_estimates"] is True

    prefectures = payload["prefectures"]
    assert len(prefectures) == 47
    assert prefectures[0]["prefecture_name"] == "東京都"
    assert prefectures[1]["prefecture_name"] == "神奈川県"
    assert prefectures[2]["prefecture_name"] == "埼玉県"
    assert prefectures[3]["prefecture_name"] == "千葉県"
    assert prefectures[-1]["prefecture_name"] == "沖縄県"

    urls = [prefecture["url"] for prefecture in prefectures]
    assert len(set(urls)) == 47
    assert all(url.startswith("/tools/school-database/") for url in urls)

    available_population = [prefecture for prefecture in prefectures if prefecture["population"]["available"]]
    assert [prefecture["prefecture_code"] for prefecture in available_population] == ["tokyo"]

    tokyo = available_population[0]
    assert tokyo["school_database"]["record_count"] == 3493
    assert tokyo["population"]["japanese_population"] == 13293851
    assert tokyo["population"]["japanese_age_3_17"] == 1507197
    assert tokyo["population"]["share_of_japanese_population_percent"] == 11.3
    assert tokyo["population"]["denominator"] == "japanese_population"
    assert tokyo["population"]["all_residents_age_3_17"] is None

    for prefecture in prefectures:
        school_database = prefecture["school_database"]
        assert school_database["record_count"] > 0
        assert school_database["municipality_count"] >= 0
        assert school_database["school_type_count"] > 0
        assert set(school_database["establishment"]) == {"national", "public", "private", "other"}
        if prefecture["prefecture_code"] != "tokyo":
            assert prefecture["population"] == {"available": False}
            assert "japanese_population" not in prefecture["population"]


def test_portal_html() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    parser = PortalParser()
    parser.feed(html)

    assert parser.prefecture_card_roots == 1
    assert parser.renderer_scripts == 1
    for prohibited in PROHIBITED_PLACEHOLDER_TEXT:
        assert prohibited not in html
    assert "<button disabled" not in html
    assert "東京都版を開く" not in html
    assert "日本人人口" not in html
    assert "日本人人口比" not in html
    assert "population-pilot-card" not in html


if __name__ == "__main__":
    test_population_json()
    test_card_metadata_json()
    test_portal_html()
    print("prefecture card metadata validation passed")
