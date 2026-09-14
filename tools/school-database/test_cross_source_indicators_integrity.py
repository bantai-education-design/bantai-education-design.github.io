#!/usr/bin/env python3
"""Mechanical CI audit verifying 47-prefecture formulas, denominators, national
aggregates, and live e-Stat 2020 Census Table 2-1 Ground Truth (PR #317)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

ANALYTICS_PATH = ROOT / "data" / "school-database" / "national-analytics-dataset.json"
POPULATION_PATH = ROOT / "data" / "school-database" / "prefecture-population.json"
EXT_STATS_PATH = ROOT / "data" / "school-database" / "prefecture-education-external-stats.json"

from build_census_demographics_from_estat import build_census_demographics_from_estat

OFFICIAL_DEMOGRAPHICS_CENSUS = {
    "01": {"pop_under_15": 555804, "pop_2015": 5381733},
    "02": {"pop_under_15": 129112, "pop_2015": 1308265},
    "03": {"pop_under_15": 132447, "pop_2015": 1279594},
    "04": {"pop_under_15": 268428, "pop_2015": 2333899},
    "05": {"pop_under_15": 92673, "pop_2015": 1023119},
    "06": {"pop_under_15": 120086, "pop_2015": 1123891},
    "07": {"pop_under_15": 206152, "pop_2015": 1914039},
    "08": {"pop_under_15": 333741, "pop_2015": 2916976},
    "09": {"pop_under_15": 227553, "pop_2015": 1974255},
    "10": {"pop_under_15": 224304, "pop_2015": 1973115},
    "11": {"pop_under_15": 858384, "pop_2015": 7266534},
    "12": {"pop_under_15": 734496, "pop_2015": 6222666},
    "13": {"pop_under_15": 1566840, "pop_2015": 13515271},
    "14": {"pop_under_15": 1085763, "pop_2015": 9126214},
    "15": {"pop_under_15": 247480, "pop_2015": 2304264},
    "16": {"pop_under_15": 115177, "pop_2015": 1066328},
    "17": {"pop_under_15": 137096, "pop_2015": 1154008},
    "18": {"pop_under_15": 95544, "pop_2015": 786740},
    "19": {"pop_under_15": 91629, "pop_2015": 834930},
    "20": {"pop_under_15": 242873, "pop_2015": 2098804},
    "21": {"pop_under_15": 240520, "pop_2015": 2031903},
    "22": {"pop_under_15": 438723, "pop_2015": 3700305},
    "23": {"pop_under_15": 973642, "pop_2015": 7483128},
    "24": {"pop_under_15": 211090, "pop_2015": 1815865},
    "25": {"pop_under_15": 191369, "pop_2015": 1412916},
    "26": {"pop_under_15": 293465, "pop_2015": 2610353},
    "27": {"pop_under_15": 1029499, "pop_2015": 8839469},
    "28": {"pop_under_15": 660205, "pop_2015": 5534800},
    "29": {"pop_under_15": 154271, "pop_2015": 1364316},
    "30": {"pop_under_15": 105360, "pop_2015": 963579},
    "31": {"pop_under_15": 68330, "pop_2015": 573441},
    "32": {"pop_under_15": 81641, "pop_2015": 694352},
    "33": {"pop_under_15": 229352, "pop_2015": 1921525},
    "34": {"pop_under_15": 352678, "pop_2015": 2843990},
    "35": {"pop_under_15": 153608, "pop_2015": 1404729},
    "36": {"pop_under_15": 77129, "pop_2015": 755733},
    "37": {"pop_under_15": 113757, "pop_2015": 976263},
    "38": {"pop_under_15": 153764, "pop_2015": 1385262},
    "39": {"pop_under_15": 74946, "pop_2015": 728276},
    "40": {"pop_under_15": 662179, "pop_2015": 5101556},
    "41": {"pop_under_15": 108241, "pop_2015": 832832},
    "42": {"pop_under_15": 164303, "pop_2015": 1377187},
    "43": {"pop_under_15": 228366, "pop_2015": 1786170},
    "44": {"pop_under_15": 135272, "pop_2015": 1166338},
    "45": {"pop_under_15": 139773, "pop_2015": 1104069},
    "46": {"pop_under_15": 205381, "pop_2015": 1648177},
    "47": {"pop_under_15": 243246, "pop_2015": 1433566},
}


def test_census_demographics_estat_live_ground_truth() -> None:
    """Verify live e-Stat 2020 & 2015 Census raw data matches OFFICIAL_DEMOGRAPHICS_CENSUS 100% across all 47 prefectures without fallback."""
    live_demographics = build_census_demographics_from_estat(strict_live=True)
    assert len(live_demographics) == 47, f"Expected 47 prefectures, got {len(live_demographics)}"

    for pref_num, live_data in live_demographics.items():
        dict_data = OFFICIAL_DEMOGRAPHICS_CENSUS[pref_num]
        assert live_data["pop_under_15"] == dict_data["pop_under_15"], (
            f"Prefecture {pref_num} pop_under_15 mismatch: live={live_data['pop_under_15']} vs dict={dict_data['pop_under_15']}"
        )
        assert live_data["pop_2015"] == dict_data["pop_2015"], (
            f"Prefecture {pref_num} pop_2015 mismatch: live={live_data['pop_2015']} vs dict={dict_data['pop_2015']}"
        )


def test_cross_source_indicators_integrity() -> None:
    """Mechanical CI audit verifying 47-prefecture formulas, denominators, and national
    aggregates across all cross-source indicators."""
    assert ANALYTICS_PATH.exists(), f"{ANALYTICS_PATH} missing"
    assert POPULATION_PATH.exists(), f"{POPULATION_PATH} missing"
    assert EXT_STATS_PATH.exists(), f"{EXT_STATS_PATH} missing"

    analytics = json.loads(ANALYTICS_PATH.read_text(encoding="utf-8"))
    pop_data = json.loads(POPULATION_PATH.read_text(encoding="utf-8"))
    ext_stats = json.loads(EXT_STATS_PATH.read_text(encoding="utf-8"))

    prefectures = analytics["prefectures"]
    nat_summary = analytics["national_summary"]
    definitions = analytics["indicators_definition"]

    pop_by_code = {p["prefecture_code"]: p for p in pop_data["prefectures"]}
    ext_by_code = {p["prefecture_code"]: p for p in ext_stats["prefectures"]}

    assert len(prefectures) == 47, f"Expected 47 prefectures, got {len(prefectures)}"

    # 1. Total Population Check
    assert nat_summary["total_population"] == 126146099, "National total population must be exact Census 2020 (126,146,099)"

    # 2. Aging Rate Check (65+ / total_pop * 100 for all 47 prefectures)
    for p in prefectures:
        expected_aging_rate = round(p["elderly_65_plus"] / p["total_population"] * 100, 1)
        assert p["aging_rate"] == expected_aging_rate, f"{p['code']}: aging_rate mismatch (actual {p['aging_rate']} vs expected {expected_aging_rate})"
    expected_nat_aging = round(nat_summary["elderly_65_plus"] / nat_summary["total_population"] * 100, 1)
    assert nat_summary["aging_rate"] == expected_nat_aging, "National aging_rate mismatch"

    # 3. Child Under 15 Ratio Check (pop_under_15 / total_pop * 100 for all 47 prefectures)
    assert "child_under_15_ratio" in definitions
    assert definitions["child_under_15_ratio"]["source"] == "総務省統計局「令和2年国勢調査 確定値」"
    for p in prefectures:
        demo = OFFICIAL_DEMOGRAPHICS_CENSUS[p["pref_number"]]
        expected_u15_ratio = round(demo["pop_under_15"] / p["total_population"] * 100, 1)
        assert p["child_under_15_ratio"] == expected_u15_ratio, f"{p['code']}: child_under_15_ratio mismatch (actual {p['child_under_15_ratio']} vs expected {expected_u15_ratio})"
    expected_nat_under_15 = round(14955692 / 126146099 * 100, 1)  # 11.9%
    assert nat_summary["child_under_15_ratio"] == expected_nat_under_15

    # 4. Population Change Rate Check (2015 -> 2020 for all 47 prefectures)
    for p in prefectures:
        demo = OFFICIAL_DEMOGRAPHICS_CENSUS[p["pref_number"]]
        expected_pop_change = round((p["total_population"] - demo["pop_2015"]) / demo["pop_2015"] * 100, 1)
        assert p["pop_change_rate"] == expected_pop_change, f"{p['code']}: pop_change_rate mismatch (actual {p['pop_change_rate']} vs expected {expected_pop_change})"
    expected_nat_pop_change = round((126146099 - 127094745) / 127094745 * 100, 1)  # -0.7%
    assert nat_summary["pop_change_rate"] == expected_nat_pop_change

    # 5. School Age Pop Ratios (6-11 per Elem School, 12-14 per JHS School for all 47 prefectures)
    for p in prefectures:
        expected_elem_pop_per_sch = round(p["elem_age_6_11"] / p["elem_school_count"], 1)
        assert p["elem_pop_per_school"] == expected_elem_pop_per_sch, f"{p['code']}: elem_pop_per_school mismatch"

        expected_jhs_pop_per_sch = round(p["jhs_age_12_14"] / p["jhs_school_count"], 1)
        assert p["jhs_pop_per_school"] == expected_jhs_pop_per_sch, f"{p['code']}: jhs_pop_per_school mismatch"

    expected_nat_elem_pop_per_sch = round(sum(p["elem_age_6_11"] for p in prefectures) / nat_summary["elem_school_count"], 1)
    assert nat_summary["elem_pop_per_school"] == expected_nat_elem_pop_per_sch  # 333.8人/校

    expected_nat_jhs_pop_per_sch = round(sum(p["jhs_age_12_14"] for p in prefectures) / nat_summary["jhs_school_count"], 1)
    assert nat_summary["jhs_pop_per_school"] == expected_nat_jhs_pop_per_sch  # 328.6人/校

    # 6. Special Needs Schools per 100k (age 6-17 Total Pop for all 47 prefectures)
    for p in prefectures:
        sch_age_pop = p["elem_age_6_11"] + p["jhs_age_12_14"] + p["hs_age_15_17"]
        expected_sn_per_100k = round(p["special_needs_schools"] / sch_age_pop * 100000, 1)
        assert p["special_needs_schools_per_100k_age_6_17"] == expected_sn_per_100k, f"{p['code']}: SN per 100k mismatch"

    nat_sch_age_pop = sum(p["elem_age_6_11"] + p["jhs_age_12_14"] + p["hs_age_15_17"] for p in prefectures)
    expected_nat_sn = round(sum(p["special_needs_schools"] for p in prefectures) / nat_sch_age_pop * 100000, 1)
    assert nat_summary["special_needs_schools_per_100k_age_6_17"] == expected_nat_sn  # 9.4校/10万人

    # 7. ICT Teaching Capability Check (Major Category A & Official National 90.7%)
    for p in prefectures:
        assert p["ict_teaching_capability"] == ext_by_code[p["code"]]["ict_teaching_capability"], f"{p['code']}: ICT capability mismatch"
    assert nat_summary["ict_teaching_capability"] == 90.7, "National ICT capability must be official MEXT figure 90.7%"
    assert "大項目A" in definitions["ict_teaching_capability"]["label"]
    assert "教材研究" in definitions["ict_teaching_capability"]["label"] or "教材研究" in definitions["ict_teaching_capability"]["description"]

    # 8. Waiting Children per 10k Preschool (3-5 Total Pop formula for all 47 prefectures)
    for p in prefectures:
        code = p["code"]
        wc_count = ext_by_code[code]["waiting_children_count"]
        pref_pop = pop_by_code[code]
        preschool_pop = [ag["population"] for ag in pref_pop["age_groups"] if ag["key"] == "census_preschool_3_5"][0]
        expected_wc_per_10k = round(wc_count / preschool_pop * 10000, 1)
        assert p["waiting_children_per_10k_preschool"] == expected_wc_per_10k, f"{code}: waiting_children_per_10k_preschool mismatch (actual {p['waiting_children_per_10k_preschool']} vs expected {expected_wc_per_10k})"

    assert definitions["waiting_children_per_10k_preschool"]["unit"] == "人/1万人"
    assert definitions["waiting_children_per_10k_preschool"]["base_date"] == "2025年4月1日／2020年10月1日時点"


if __name__ == "__main__":
    test_census_demographics_estat_live_ground_truth()
    test_cross_source_indicators_integrity()
    print("ALL CROSS-SOURCE INDICATOR INTEGRITY & CENSUS LIVE GROUND TRUTH TESTS PASSED SUCCESSFULLY!")
