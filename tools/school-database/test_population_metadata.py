#!/usr/bin/env python3
"""Validate the Tokyo population metadata pilot."""

from __future__ import annotations

import json
import math
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POPULATION_JSON = ROOT / "data" / "school-database" / "prefecture-population-pilot.json"
INDEX_HTML = ROOT / "tools" / "school-database" / "index.html"

EXPECTED_GROUPS = {
    "japanese_preschool_3_5": (3, 5),
    "japanese_elementary_6_11": (6, 11),
    "japanese_junior_high_12_14": (12, 14),
    "japanese_high_school_15_17": (15, 17),
    "japanese_age_3_17": (3, 17),
}

PROHIBITED_CARD_LABELS = ("総人口", "東京都の人口", "学齢人口", "教育年齢人口")


class CardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.prefecture_cards: list[set[str]] = []
        self.population_pilot_cards = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())
        if {"pref-card", "prefecture-card"}.issubset(classes):
            self.prefecture_cards.append(classes)
        if "population-pilot-card" in classes:
            self.population_pilot_cards += 1


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


def test_portal_html() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    parser = CardParser()
    parser.feed(html)

    assert len(parser.prefecture_cards) == 47
    assert parser.population_pilot_cards == 1
    assert "population-pilot-card" in html
    assert "日本人人口" in html
    assert "外国人人口は含みません。" in html
    assert "実際の在学者数ではありません。" in html
    assert "割合は日本人人口13,293,851人を分母として計算しています。" in html
    assert "13,293,851" in html
    assert "1,507,197" in html
    assert "日本人人口比 11.3%" in html
    assert html.count("population-pilot-card") == 1

    pilot_card = re.search(
        r'<article class="pref-card prefecture-card active-card region-kanto population-pilot-card".*?</article>',
        html,
        re.DOTALL,
    )
    assert pilot_card
    for prohibited in PROHIBITED_CARD_LABELS:
        assert prohibited not in pilot_card.group(0)

    non_tokyo_population_regions = re.findall(r"region-(?!kanto)[a-z]+[^>]*population-pilot-card", html)
    assert not non_tokyo_population_regions


if __name__ == "__main__":
    test_population_json()
    test_portal_html()
    print("population metadata pilot validation passed")
