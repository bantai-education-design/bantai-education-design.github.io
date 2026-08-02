#!/usr/bin/env python3
"""Merge data/school-database/prefecture-education-profile.json (47
prefectures, statistics-derived taglines) into
data/school-database/prefecture-card-metadata.json.

Adds an `education_profile` object to every one of the 47 prefecture
entries, mirroring how `integrate_population_into_card_metadata.py`
integrated the `population` block.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "data" / "school-database" / "prefecture-education-profile.json"
CARD_METADATA_PATH = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"


def build_education_profile_block(pref: dict) -> dict:
    return {
        "available": pref["available"],
        "metric_id": pref["metric_id"],
        "metric_label": pref["metric_label"],
        "value": pref["value"],
        "unit": pref["unit"],
        "national_average": pref["national_average"],
        "headline_text": pref["headline_text"],
        "source_short_label": pref["source_short_label"],
        "reference_date_display": pref["reference_date_display"],
        "statistic_name": pref["statistic_name"],
        "not_an_official_ranking": True,
    }


def main() -> None:
    profile_payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_PATH.read_text(encoding="utf-8"))

    profile_by_code = {p["prefecture_code"]: p for p in profile_payload["prefectures"]}

    missing = []
    for card_pref in card_payload["prefectures"]:
        code = card_pref["prefecture_code"]
        profile = profile_by_code.get(code)
        if profile is None:
            missing.append(code)
            continue
        card_pref["education_profile"] = build_education_profile_block(profile)

    if missing:
        raise ValueError(f"no education profile data found for prefecture codes: {missing}")

    covered = {card_pref["prefecture_code"] for card_pref in card_payload["prefectures"]}
    if len(covered) != 47:
        raise ValueError(f"expected 47 prefectures in card metadata, got {len(covered)}")
    if any(card_pref["education_profile"]["available"] is not True for card_pref in card_payload["prefectures"]):
        raise ValueError("not every prefecture ended up with education_profile.available == true")

    CARD_METADATA_PATH.write_text(
        json.dumps(card_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {CARD_METADATA_PATH} with education_profile data for {len(covered)} prefectures")


if __name__ == "__main__":
    main()
