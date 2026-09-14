#!/usr/bin/env python3
"""Static integration checks for official statistics overlays used by analytics."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ABS = ROOT / "data" / "school-database" / "mext-absenteeism-r6-ground-truth.json"
MOV = ROOT / "data" / "school-database" / "population-movement-2025.json"
JS = ROOT / "assets" / "js" / "analytics-events.js"


def test_overlay() -> None:
    abs_data = json.loads(ABS.read_text(encoding="utf-8"))
    mov_data = json.loads(MOV.read_text(encoding="utf-8"))
    js = JS.read_text(encoding="utf-8")
    assert len(abs_data["prefectures"]) == 47
    assert len(mov_data["prefectures"]) == 47
    a = {p["prefecture_code"]: p for p in abs_data["prefectures"]}
    m = {p["prefecture_code"]: p for p in mov_data["prefectures"]}
    assert a["tokyo"]["absenteeism_combined_count"] == 33831
    assert a["hokkaido"]["absenteeism_combined_count"] == 14252
    assert a["okinawa"]["absenteeism_combined_rate"] == 49.5
    assert m["tokyo"]["net_migration_2025"] == 65219
    assert m["tokyo"]["net_migration_rate_2025"] == 0.47
    assert m["hiroshima"]["net_migration_2025"] == -9921
    assert m["shiga"]["net_migration_2025"] == 353
    for needle in (
        "mext-absenteeism-r6-ground-truth.json",
        "population-movement-2025.json",
        "mergeAbsenteeism",
        "mergeMovement",
        "net_migration_2025",
        "net_migration_rate_2025",
        "absenteeism_combined_rate",
    ):
        assert needle in js, f"analytics overlay missing {needle}"


if __name__ == "__main__":
    test_overlay()
    print("OFFICIAL ABSENTEEISM & POPULATION MOVEMENT DASHBOARD OVERLAY VALIDATION PASSED!")
