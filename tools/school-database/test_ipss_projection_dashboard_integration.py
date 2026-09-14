#!/usr/bin/env python3
"""Validate the committed IPSS projection master and dashboard wiring."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECTION_PATH = ROOT / "data" / "school-database" / "ipss-child-population-projection-2023.json"
ANALYTICS_PATH = ROOT / "data" / "school-database" / "national-analytics-dataset.json"
DASHBOARD_JS_PATH = ROOT / "assets" / "js" / "school-database" / "analytics.js"


def test_ipss_projection_dashboard_integration() -> None:
    projection = json.loads(PROJECTION_PATH.read_text(encoding="utf-8"))
    analytics = json.loads(ANALYTICS_PATH.read_text(encoding="utf-8"))
    js = DASHBOARD_JS_PATH.read_text(encoding="utf-8")

    assert projection["source"]["base_year"] == 2020
    assert projection["national"] == {
        "child_population_index_2035": 77.8,
        "child_population_index_2050": 69.2,
    }
    assert len(projection["prefectures"]) == 47

    projection_codes = {item["prefecture_code"] for item in projection["prefectures"]}
    analytics_codes = {item["code"] for item in analytics["prefectures"]}
    assert projection_codes == analytics_codes, "IPSS projection slugs must exactly match analytics prefecture slugs"

    tokyo = next(item for item in projection["prefectures"] if item["prefecture_code"] == "tokyo")
    akita = next(item for item in projection["prefectures"] if item["prefecture_code"] == "akita")
    okinawa = next(item for item in projection["prefectures"] if item["prefecture_code"] == "okinawa")

    assert (tokyo["child_population_index_2035"], tokyo["child_population_index_2050"]) == (93.5, 91.8)
    assert (akita["child_population_index_2035"], akita["child_population_index_2050"]) == (58.1, 41.5)
    assert (okinawa["child_population_index_2035"], okinawa["child_population_index_2050"]) == (83.7, 78.5)

    assert "/data/school-database/ipss-child-population-projection-2023.json" in js
    assert "child_population_index_2035" in js
    assert "child_population_index_2050" in js
    assert "全国指数（2020年=100）" in js
    assert "国立社会保障・人口問題研究所" in js

    # PR #324 must not expose the currently disputed absenteeism values in the dashboard.
    assert "absenteeism_combined_rate" not in js
    assert "elem_absenteeism_rate" not in js
    assert "jhs_absenteeism_rate" not in js


if __name__ == "__main__":
    test_ipss_projection_dashboard_integration()
    print("IPSS FUTURE CHILD POPULATION DASHBOARD INTEGRATION VALIDATION PASSED!")
