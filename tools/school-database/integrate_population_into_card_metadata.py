#!/usr/bin/env python3
"""Merge data/school-database/prefecture-population.json (47 prefectures,
2020 Census Table 2-1, decision C) into
data/school-database/prefecture-card-metadata.json.

Replaces the `population` object on every one of the 47 prefecture entries
(including Tokyo's prior 2026 resident-registry pilot figures) with the
same census-based structure and labels, so no prefecture uses a different
population definition or key set than the others.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POPULATION_PATH = ROOT / "data" / "school-database" / "prefecture-population.json"
CARD_METADATA_PATH = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"

SOURCE_PUBLISHER = "総務省統計局"


def round1(value: float) -> float:
    return round(value, 1)


def build_population_block(pref: dict) -> dict:
    age_groups = [
        {
            "key": group["key"],
            "label": group["label"],
            "age_range_label": group["age_range_label"],
            "population": group["population"],
            "share_of_census_population_percent": round1(group["share_of_census_population_percent"]),
        }
        for group in pref["age_groups"]
    ]

    return {
        "available": True,
        "population_scope_label": "人口（日本国籍）",
        "population_scope": pref["population_scope"],
        "population_definition": "令和2年国勢調査における日本人人口",
        "census_population": pref["census_population"],
        "census_age_3_17": pref["census_age_3_17"],
        "share_of_census_population_percent": round1(pref["share_of_census_population_percent"]),
        "reference_date": pref["reference_date"],
        "reference_date_label": pref["reference_date_label"],
        "reference_date_display": pref["reference_date_display"],
        "source_short_label": pref["source_short_label"],
        "age_groups_label": "校種相当年齢人口",
        "age_groups": age_groups,
        "footer_note": "学校規模を考える参考となる統計です。実際の在学者数ではありません。",
        "summary_note": "日本国籍の住民が対象です。外国籍の住民は含みません。",
        "notes": [
            "年齢別人口は、各校種に相当する年齢層の人口であり、実際の在学者数ではありません。就学猶予、留年、早生まれの学年境界、区域外通学、国私立校への進学、未就園、通信制などは反映していません。",
            "割合は、人口（日本国籍）を分母として計算しています。年齢「不詳」の人は含みません。",
        ],
        "source": {
            "publisher": SOURCE_PUBLISHER,
            "title": pref["source_title"],
            "short_label": pref["source_short_label"],
            "page_url": pref["source_url"],
            "table_id": pref["source_table_id"],
            "format": "Excel",
            "accessed_at": pref["accessed_at"],
        },
    }


def main() -> None:
    population_payload = json.loads(POPULATION_PATH.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_PATH.read_text(encoding="utf-8"))

    population_by_code = {p["prefecture_code"]: p for p in population_payload["prefectures"]}

    missing = []
    for card_pref in card_payload["prefectures"]:
        code = card_pref["prefecture_code"]
        pref_population = population_by_code.get(code)
        if pref_population is None:
            missing.append(code)
            continue
        card_pref["population"] = build_population_block(pref_population)

    if missing:
        raise ValueError(f"no population data found for prefecture codes: {missing}")

    covered = {card_pref["prefecture_code"] for card_pref in card_payload["prefectures"]}
    if len(covered) != 47:
        raise ValueError(f"expected 47 prefectures in card metadata, got {len(covered)}")
    if any(card_pref["population"]["available"] is not True for card_pref in card_payload["prefectures"]):
        raise ValueError("not every prefecture ended up with population.available == true")

    CARD_METADATA_PATH.write_text(
        json.dumps(card_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {CARD_METADATA_PATH} with population data for {len(covered)} prefectures")


if __name__ == "__main__":
    main()
