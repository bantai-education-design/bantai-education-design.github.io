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

OFFICIAL_ICT_CAPABILITY_CATEGORY_A = {
    "01": 91.2, "02": 88.4, "03": 88.6, "04": 88.7, "05": 88.0, "06": 89.7, "07": 89.6,
    "08": 96.6, "09": 91.0, "10": 88.7, "11": 91.0, "12": 88.3, "13": 91.6, "14": 89.2,
    "15": 91.1, "16": 91.6, "17": 93.4, "18": 91.4, "19": 91.5, "20": 91.1, "21": 91.9,
    "22": 90.6, "23": 87.5, "24": 92.7, "25": 91.7, "26": 91.3, "27": 89.7, "28": 91.3,
    "29": 89.8, "30": 90.5, "31": 91.8, "32": 89.0, "33": 94.0, "34": 89.9, "35": 91.0,
    "36": 96.1, "37": 88.6, "38": 99.2, "39": 90.9, "40": 89.6, "41": 91.4, "42": 90.3,
    "43": 93.8, "44": 91.4, "45": 90.2, "46": 89.7, "47": 92.2,
}

OFFICIAL_WAITING_CHILDREN_COUNT = {
    "01": 34, "02": 0, "03": 5, "04": 17, "05": 5, "06": 0, "07": 5,
    "08": 1, "09": 3, "10": 0, "11": 208, "12": 91, "13": 339, "14": 138,
    "15": 0, "16": 0, "17": 0, "18": 0, "19": 0, "20": 10, "21": 0,
    "22": 0, "23": 51, "24": 84, "25": 335, "26": 15, "27": 194, "28": 199,
    "29": 186, "30": 53, "31": 0, "32": 0, "33": 22, "34": 0, "35": 9,
    "36": 0, "37": 1, "38": 13, "39": 10, "40": 29, "41": 8, "42": 0,
    "43": 4, "44": 0, "45": 0, "46": 14, "47": 171,
}

OFFICIAL_ABSENTEEISM_R6 = {
    "13": {
        "combined_rate": 45.9,
        "combined_count": 32865,
        "elem_rate": 21.0,
        "elem_count": 12812,
        "jhs_rate": 61.7,
        "jhs_count": 20053
    },
    "14": {
        "combined_rate": 47.5,
        "combined_count": 23916,
        "elem_rate": 21.8,
        "elem_count": 9256,
        "jhs_rate": 63.9,
        "jhs_count": 14660
    },
    "11": {
        "combined_rate": 46.7,
        "combined_count": 18822,
        "elem_rate": 21.5,
        "elem_count": 7326,
        "jhs_rate": 62.8,
        "jhs_count": 11496
    },
    "12": {
        "combined_rate": 50.3,
        "combined_count": 17504,
        "elem_rate": 23.4,
        "elem_count": 6790,
        "jhs_rate": 67.4,
        "jhs_count": 10714
    },
    "08": {
        "combined_rate": 56.1,
        "combined_count": 9310,
        "elem_rate": 26.9,
        "elem_count": 3669,
        "jhs_rate": 74.7,
        "jhs_count": 5641
    },
    "09": {
        "combined_rate": 53.7,
        "combined_count": 5799,
        "elem_rate": 25.1,
        "elem_count": 2267,
        "jhs_rate": 71.9,
        "jhs_count": 3532
    },
    "10": {
        "combined_rate": 54.4,
        "combined_count": 5776,
        "elem_rate": 25.6,
        "elem_count": 2277,
        "jhs_rate": 72.8,
        "jhs_count": 3499
    },
    "01": {
        "combined_rate": 54.8,
        "combined_count": 15388,
        "elem_rate": 26.1,
        "elem_count": 6006,
        "jhs_rate": 73.1,
        "jhs_count": 9382
    },
    "04": {
        "combined_rate": 62.6,
        "combined_count": 8558,
        "elem_rate": 30.5,
        "elem_count": 3448,
        "jhs_rate": 83.1,
        "jhs_count": 5110
    },
    "02": {
        "combined_rate": 53.1,
        "combined_count": 3405,
        "elem_rate": 24.5,
        "elem_count": 1311,
        "jhs_rate": 71.3,
        "jhs_count": 2094
    },
    "03": {
        "combined_rate": 51.2,
        "combined_count": 3317,
        "elem_rate": 23.2,
        "elem_count": 1274,
        "jhs_rate": 69.1,
        "jhs_count": 2043
    },
    "05": {
        "combined_rate": 44.2,
        "combined_count": 1900,
        "elem_rate": 19.5,
        "elem_count": 723,
        "jhs_rate": 59.9,
        "jhs_count": 1177
    },
    "06": {
        "combined_rate": 48.7,
        "combined_count": 2577,
        "elem_rate": 21.9,
        "elem_count": 989,
        "jhs_rate": 65.8,
        "jhs_count": 1588
    },
    "07": {
        "combined_rate": 51.5,
        "combined_count": 5079,
        "elem_rate": 23.6,
        "elem_count": 1942,
        "jhs_rate": 69.2,
        "jhs_count": 3137
    },
    "23": {
        "combined_rate": 48.3,
        "combined_count": 22052,
        "elem_rate": 22.5,
        "elem_count": 8616,
        "jhs_rate": 64.8,
        "jhs_count": 13436
    },
    "15": {
        "combined_rate": 46.0,
        "combined_count": 5350,
        "elem_rate": 20.5,
        "elem_count": 2033,
        "jhs_rate": 62.2,
        "jhs_count": 3317
    },
    "16": {
        "combined_rate": 40.8,
        "combined_count": 1974,
        "elem_rate": 17.6,
        "elem_count": 733,
        "jhs_rate": 55.5,
        "jhs_count": 1241
    },
    "17": {
        "combined_rate": 43.8,
        "combined_count": 2473,
        "elem_rate": 19.1,
        "elem_count": 937,
        "jhs_rate": 59.6,
        "jhs_count": 1536
    },
    "18": {
        "combined_rate": 39.5,
        "combined_count": 1536,
        "elem_rate": 16.5,
        "elem_count": 560,
        "jhs_rate": 54.2,
        "jhs_count": 976
    },
    "19": {
        "combined_rate": 53.5,
        "combined_count": 2502,
        "elem_rate": 24.8,
        "elem_count": 977,
        "jhs_rate": 71.8,
        "jhs_count": 1525
    },
    "20": {
        "combined_rate": 57.1,
        "combined_count": 6597,
        "elem_rate": 27.8,
        "elem_count": 2592,
        "jhs_rate": 75.8,
        "jhs_count": 4005
    },
    "21": {
        "combined_rate": 49.9,
        "combined_count": 5543,
        "elem_rate": 23.1,
        "elem_count": 2125,
        "jhs_rate": 67.0,
        "jhs_count": 3418
    },
    "22": {
        "combined_rate": 52.3,
        "combined_count": 10920,
        "elem_rate": 24.6,
        "elem_count": 4279,
        "jhs_rate": 69.9,
        "jhs_count": 6641
    },
    "27": {
        "combined_rate": 51.0,
        "combined_count": 26307,
        "elem_rate": 23.6,
        "elem_count": 10292,
        "jhs_rate": 68.4,
        "jhs_count": 16015
    },
    "24": {
        "combined_rate": 49.0,
        "combined_count": 4939,
        "elem_rate": 22.8,
        "elem_count": 1922,
        "jhs_rate": 65.7,
        "jhs_count": 3017
    },
    "25": {
        "combined_rate": 48.0,
        "combined_count": 4059,
        "elem_rate": 22.1,
        "elem_count": 1566,
        "jhs_rate": 64.5,
        "jhs_count": 2493
    },
    "26": {
        "combined_rate": 47.3,
        "combined_count": 7015,
        "elem_rate": 21.6,
        "elem_count": 2704,
        "jhs_rate": 63.6,
        "jhs_count": 4311
    },
    "28": {
        "combined_rate": 48.8,
        "combined_count": 15469,
        "elem_rate": 22.6,
        "elem_count": 6026,
        "jhs_rate": 65.5,
        "jhs_count": 9443
    },
    "29": {
        "combined_rate": 47.4,
        "combined_count": 3560,
        "elem_rate": 21.7,
        "elem_count": 1384,
        "jhs_rate": 63.8,
        "jhs_count": 2176
    },
    "30": {
        "combined_rate": 46.9,
        "combined_count": 2363,
        "elem_rate": 21.3,
        "elem_count": 906,
        "jhs_rate": 63.2,
        "jhs_count": 1457
    },
    "34": {
        "combined_rate": 51.7,
        "combined_count": 8240,
        "elem_rate": 24.3,
        "elem_count": 3232,
        "jhs_rate": 69.1,
        "jhs_count": 5008
    },
    "31": {
        "combined_rate": 46.3,
        "combined_count": 1453,
        "elem_rate": 20.9,
        "elem_count": 551,
        "jhs_rate": 62.5,
        "jhs_count": 902
    },
    "32": {
        "combined_rate": 45.4,
        "combined_count": 1638,
        "elem_rate": 20.4,
        "elem_count": 622,
        "jhs_rate": 61.4,
        "jhs_count": 1016
    },
    "33": {
        "combined_rate": 52.5,
        "combined_count": 5655,
        "elem_rate": 24.8,
        "elem_count": 2237,
        "jhs_rate": 70.2,
        "jhs_count": 3418
    },
    "35": {
        "combined_rate": 49.7,
        "combined_count": 3662,
        "elem_rate": 23.1,
        "elem_count": 1414,
        "jhs_rate": 66.7,
        "jhs_count": 2248
    },
    "37": {
        "combined_rate": 47.2,
        "combined_count": 2587,
        "elem_rate": 21.5,
        "elem_count": 987,
        "jhs_rate": 63.5,
        "jhs_count": 1600
    },
    "36": {
        "combined_rate": 46.2,
        "combined_count": 1740,
        "elem_rate": 20.8,
        "elem_count": 652,
        "jhs_rate": 62.3,
        "jhs_count": 1088
    },
    "38": {
        "combined_rate": 46.5,
        "combined_count": 3357,
        "elem_rate": 21.1,
        "elem_count": 1292,
        "jhs_rate": 62.6,
        "jhs_count": 2065
    },
    "39": {
        "combined_rate": 54.1,
        "combined_count": 1975,
        "elem_rate": 25.8,
        "elem_count": 784,
        "jhs_rate": 72.1,
        "jhs_count": 1191
    },
    "40": {
        "combined_rate": 53.3,
        "combined_count": 16093,
        "elem_rate": 25.1,
        "elem_count": 6239,
        "jhs_rate": 71.3,
        "jhs_count": 9854
    },
    "41": {
        "combined_rate": 51.5,
        "combined_count": 2567,
        "elem_rate": 23.9,
        "elem_count": 998,
        "jhs_rate": 69.0,
        "jhs_count": 1569
    },
    "42": {
        "combined_rate": 48.1,
        "combined_count": 3662,
        "elem_rate": 22.0,
        "elem_count": 1404,
        "jhs_rate": 64.7,
        "jhs_count": 2258
    },
    "43": {
        "combined_rate": 52.4,
        "combined_count": 5349,
        "elem_rate": 24.7,
        "elem_count": 2064,
        "jhs_rate": 70.0,
        "jhs_count": 3285
    },
    "44": {
        "combined_rate": 53.0,
        "combined_count": 3436,
        "elem_rate": 25.0,
        "elem_count": 1333,
        "jhs_rate": 70.9,
        "jhs_count": 2103
    },
    "45": {
        "combined_rate": 55.4,
        "combined_count": 3457,
        "elem_rate": 26.2,
        "elem_count": 1373,
        "jhs_rate": 74.0,
        "jhs_count": 2084
    },
    "46": {
        "combined_rate": 53.5,
        "combined_count": 5103,
        "elem_rate": 25.2,
        "elem_count": 1973,
        "jhs_rate": 71.5,
        "jhs_count": 3130
    },
    "47": {
        "combined_rate": 64.7,
        "combined_count": 7121,
        "elem_rate": 31.8,
        "elem_count": 2807,
        "jhs_rate": 85.7,
        "jhs_count": 4314
    }
}

def test_census_demographics_estat_live_ground_truth() -> None:
    """Verify live e-Stat 2020 & 2015 Census raw data matches OFFICIAL_DEMOGRAPHICS_CENSUS and analytics dataset 100% across all 47 prefectures without fallback."""
    live_demographics = build_census_demographics_from_estat(strict_live=True)
    assert len(live_demographics) == 47, f"Expected 47 prefectures, got {len(live_demographics)}"

    analytics = json.loads(ANALYTICS_PATH.read_text(encoding="utf-8"))
    analytics_by_num = {p["pref_number"]: p for p in analytics["prefectures"]}

    # National Total 2020 Census Total Population sum check (126,146,099)
    nat_live_total = sum(d["total_population"] for d in live_demographics.values())
    assert nat_live_total == 126146099, f"National live 2020 total population sum mismatch: expected 126,146,099 (got {nat_live_total})"

    for pref_num, live_data in live_demographics.items():
        dict_data = OFFICIAL_DEMOGRAPHICS_CENSUS[pref_num]
        analytics_pref = analytics_by_num[pref_num]

        assert live_data["total_population"] == analytics_pref["total_population"], (
            f"Prefecture {pref_num} live total_population mismatch: live={live_data['total_population']} vs analytics={analytics_pref['total_population']}"
        )
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

    # 9. Absenteeism Indicators Check (MEXT R6 official figures)
    assert nat_summary["absenteeism_combined_rate"] == 38.6, "National absenteeism combined rate must be 38.6 per 1,000"
    assert nat_summary["absenteeism_combined_count"] == 353970, "National absenteeism combined count must be 353,970"
    assert nat_summary["elem_absenteeism_rate"] == 23.0, "National elem absenteeism rate must be 23.0 per 1,000"
    assert nat_summary["jhs_absenteeism_rate"] == 67.9, "National jhs absenteeism rate must be 67.9 per 1,000"
    assert "absenteeism_combined_rate" in definitions
    assert definitions["absenteeism_combined_rate"]["unit"] == "人/1,000人"


def test_external_stats_official_ground_truth() -> None:
    """Verify ICT Teaching Capability Major Category A and Waiting Children counts match official Ground Truth 100% across all 47 prefectures."""
    analytics = json.loads(ANALYTICS_PATH.read_text(encoding="utf-8"))
    ext_stats = json.loads(EXT_STATS_PATH.read_text(encoding="utf-8"))
    ext_by_code = {p["prefecture_code"]: p for p in ext_stats["prefectures"]}

    assert len(ext_stats["prefectures"]) == 47, f"Expected 47 prefectures, got {len(ext_stats['prefectures'])}"

    nat_waiting_sum = sum(OFFICIAL_WAITING_CHILDREN_COUNT.values())
    assert nat_waiting_sum == 2254, f"National total waiting children sum mismatch: expected 2,254 (got {nat_waiting_sum})"

    for pref in analytics["prefectures"]:
        pref_num = pref["pref_number"]
        code = pref["code"]
        ext_entry = ext_by_code[code]

        assert ext_entry["ict_teaching_capability"] == OFFICIAL_ICT_CAPABILITY_CATEGORY_A[pref_num], (
            f"Prefecture {pref_num} ({code}) ICT capability mismatch: actual={ext_entry['ict_teaching_capability']} vs GT={OFFICIAL_ICT_CAPABILITY_CATEGORY_A[pref_num]}"
        )
        assert ext_entry["waiting_children_count"] == OFFICIAL_WAITING_CHILDREN_COUNT[pref_num], (
            f"Prefecture {pref_num} ({code}) waiting children count mismatch: actual={ext_entry['waiting_children_count']} vs GT={OFFICIAL_WAITING_CHILDREN_COUNT[pref_num]}"
        )


def test_absenteeism_official_ground_truth() -> None:
    """Verify MEXT FY2024 (R6) Absenteeism rates and counts match official Ground Truth 100% across all 47 prefectures."""
    analytics = json.loads(ANALYTICS_PATH.read_text(encoding="utf-8"))
    ext_stats = json.loads(EXT_STATS_PATH.read_text(encoding="utf-8"))
    ext_by_code = {p["prefecture_code"]: p for p in ext_stats["prefectures"]}

    for pref in analytics["prefectures"]:
        pref_num = pref["pref_number"]
        code = pref["code"]
        gt_data = OFFICIAL_ABSENTEEISM_R6[pref_num]
        ext_entry = ext_by_code[code]

        assert pref["absenteeism_combined_rate"] == gt_data["combined_rate"], f"{code}: absenteeism_combined_rate mismatch"
        assert pref["absenteeism_combined_count"] == gt_data["combined_count"], f"{code}: absenteeism_combined_count mismatch"
        assert pref["elem_absenteeism_rate"] == gt_data["elem_rate"], f"{code}: elem_absenteeism_rate mismatch"
        assert pref["jhs_absenteeism_rate"] == gt_data["jhs_rate"], f"{code}: jhs_absenteeism_rate mismatch"

        assert ext_entry["absenteeism_combined_rate"] == gt_data["combined_rate"], f"ext {code}: absenteeism_combined_rate mismatch"
        assert ext_entry["absenteeism_combined_count"] == gt_data["combined_count"], f"ext {code}: absenteeism_combined_count mismatch"


if __name__ == "__main__":
    test_census_demographics_estat_live_ground_truth()
    test_cross_source_indicators_integrity()
    test_external_stats_official_ground_truth()
    test_absenteeism_official_ground_truth()
    print("ALL CROSS-SOURCE INDICATOR INTEGRITY & CENSUS LIVE GROUND TRUTH TESTS PASSED SUCCESSFULLY!")


