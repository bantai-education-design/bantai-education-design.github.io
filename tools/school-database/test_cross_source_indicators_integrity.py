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
    "01": {
        "combined_rate": 42.2,
        "combined_count": 14252,
        "elem_rate": 22.4,
        "elem_count": 4881,
        "jhs_rate": 78.6,
        "jhs_count": 9371
    },
    "02": {
        "combined_rate": 36.3,
        "combined_count": 2869,
        "elem_rate": 19.2,
        "elem_count": 981,
        "jhs_rate": 67.7,
        "jhs_count": 1888
    },
    "03": {
        "combined_rate": 33.3,
        "combined_count": 2685,
        "elem_rate": 17.9,
        "elem_count": 931,
        "jhs_rate": 61.3,
        "jhs_count": 1754
    },
    "04": {
        "combined_rate": 47.0,
        "combined_count": 7725,
        "elem_rate": 27.9,
        "elem_count": 3002,
        "jhs_rate": 82.8,
        "jhs_count": 4723
    },
    "05": {
        "combined_rate": 36.4,
        "combined_count": 2027,
        "elem_rate": 19.8,
        "elem_count": 699,
        "jhs_rate": 65.5,
        "jhs_count": 1328
    },
    "06": {
        "combined_rate": 32.5,
        "combined_count": 2343,
        "elem_rate": 18.3,
        "elem_count": 849,
        "jhs_rate": 58.3,
        "jhs_count": 1494
    },
    "07": {
        "combined_rate": 34.5,
        "combined_count": 4365,
        "elem_rate": 18.0,
        "elem_count": 1496,
        "jhs_rate": 65.7,
        "jhs_count": 2869
    },
    "08": {
        "combined_rate": 38.0,
        "combined_count": 7935,
        "elem_rate": 21.5,
        "elem_count": 2904,
        "jhs_rate": 68.2,
        "jhs_count": 5031
    },
    "09": {
        "combined_rate": 43.2,
        "combined_count": 6032,
        "elem_rate": 24.2,
        "elem_count": 2192,
        "jhs_rate": 78.2,
        "jhs_count": 3840
    },
    "10": {
        "combined_rate": 34.9,
        "combined_count": 4788,
        "elem_rate": 20.3,
        "elem_count": 1791,
        "jhs_rate": 61.5,
        "jhs_count": 2997
    },
    "11": {
        "combined_rate": 32.4,
        "combined_count": 17356,
        "elem_rate": 18.1,
        "elem_count": 6360,
        "jhs_rate": 59.9,
        "jhs_count": 10996
    },
    "12": {
        "combined_rate": 32.9,
        "combined_count": 14883,
        "elem_rate": 20.7,
        "elem_count": 6143,
        "jhs_rate": 56.4,
        "jhs_count": 8740
    },
    "13": {
        "combined_rate": 35.7,
        "combined_count": 33831,
        "elem_rate": 21.6,
        "elem_count": 13548,
        "jhs_rate": 63.3,
        "jhs_count": 20283
    },
    "14": {
        "combined_rate": 38.2,
        "combined_count": 25231,
        "elem_rate": 23.6,
        "elem_count": 10275,
        "jhs_rate": 66.6,
        "jhs_count": 14956
    },
    "15": {
        "combined_rate": 38.8,
        "combined_count": 5829,
        "elem_rate": 21.9,
        "elem_count": 2119,
        "jhs_rate": 69.7,
        "jhs_count": 3710
    },
    "16": {
        "combined_rate": 37.4,
        "combined_count": 2624,
        "elem_rate": 24.3,
        "elem_count": 1106,
        "jhs_rate": 61.7,
        "jhs_count": 1518
    },
    "17": {
        "combined_rate": 38.7,
        "combined_count": 3210,
        "elem_rate": 22.9,
        "elem_count": 1237,
        "jhs_rate": 68.3,
        "jhs_count": 1973
    },
    "18": {
        "combined_rate": 28.9,
        "combined_count": 1661,
        "elem_rate": 15.8,
        "elem_count": 586,
        "jhs_rate": 52.6,
        "jhs_count": 1075
    },
    "19": {
        "combined_rate": 41.2,
        "combined_count": 2337,
        "elem_rate": 23.0,
        "elem_count": 844,
        "jhs_rate": 75.1,
        "jhs_count": 1493
    },
    "20": {
        "combined_rate": 48.6,
        "combined_count": 7248,
        "elem_rate": 31.5,
        "elem_count": 3051,
        "jhs_rate": 80.0,
        "jhs_count": 4197
    },
    "21": {
        "combined_rate": 39.8,
        "combined_count": 5897,
        "elem_rate": 24.3,
        "elem_count": 2326,
        "jhs_rate": 67.7,
        "jhs_count": 3571
    },
    "22": {
        "combined_rate": 45.6,
        "combined_count": 12118,
        "elem_rate": 30.0,
        "elem_count": 5133,
        "jhs_rate": 73.8,
        "jhs_count": 6985
    },
    "23": {
        "combined_rate": 41.8,
        "combined_count": 24927,
        "elem_rate": 25.7,
        "elem_count": 10028,
        "jhs_rate": 72.0,
        "jhs_count": 14899
    },
    "24": {
        "combined_rate": 37.5,
        "combined_count": 4891,
        "elem_rate": 23.2,
        "elem_count": 1954,
        "jhs_rate": 63.3,
        "jhs_count": 2937
    },
    "25": {
        "combined_rate": 36.7,
        "combined_count": 4305,
        "elem_rate": 22.2,
        "elem_count": 1702,
        "jhs_rate": 64.0,
        "jhs_count": 2603
    },
    "26": {
        "combined_rate": 35.8,
        "combined_count": 6490,
        "elem_rate": 22.2,
        "elem_count": 2593,
        "jhs_rate": 60.7,
        "jhs_count": 3897
    },
    "27": {
        "combined_rate": 37.9,
        "combined_count": 23749,
        "elem_rate": 21.3,
        "elem_count": 8718,
        "jhs_rate": 69.3,
        "jhs_count": 15031
    },
    "28": {
        "combined_rate": 38.8,
        "combined_count": 15868,
        "elem_rate": 21.9,
        "elem_count": 5874,
        "jhs_rate": 70.7,
        "jhs_count": 9994
    },
    "29": {
        "combined_rate": 39.7,
        "combined_count": 3870,
        "elem_rate": 22.6,
        "elem_count": 1417,
        "jhs_rate": 70.4,
        "jhs_count": 2453
    },
    "30": {
        "combined_rate": 38.9,
        "combined_count": 2511,
        "elem_rate": 23.2,
        "elem_count": 967,
        "jhs_rate": 67.6,
        "jhs_count": 1544
    },
    "31": {
        "combined_rate": 42.3,
        "combined_count": 1764,
        "elem_rate": 23.9,
        "elem_count": 653,
        "jhs_rate": 77.2,
        "jhs_count": 1111
    },
    "32": {
        "combined_rate": 48.8,
        "combined_count": 2445,
        "elem_rate": 32.1,
        "elem_count": 1056,
        "jhs_rate": 80.7,
        "jhs_count": 1389
    },
    "33": {
        "combined_rate": 29.6,
        "combined_count": 4241,
        "elem_rate": 19.4,
        "elem_count": 1807,
        "jhs_rate": 48.8,
        "jhs_count": 2434
    },
    "34": {
        "combined_rate": 40.5,
        "combined_count": 8738,
        "elem_rate": 25.4,
        "elem_count": 3559,
        "jhs_rate": 68.5,
        "jhs_count": 5179
    },
    "35": {
        "combined_rate": 38.3,
        "combined_count": 3573,
        "elem_rate": 23.4,
        "elem_count": 1412,
        "jhs_rate": 65.3,
        "jhs_count": 2161
    },
    "36": {
        "combined_rate": 36.5,
        "combined_count": 1814,
        "elem_rate": 17.7,
        "elem_count": 573,
        "jhs_rate": 71.7,
        "jhs_count": 1241
    },
    "37": {
        "combined_rate": 31.6,
        "combined_count": 2253,
        "elem_rate": 18.5,
        "elem_count": 858,
        "jhs_rate": 56.3,
        "jhs_count": 1395
    },
    "38": {
        "combined_rate": 41.1,
        "combined_count": 3950,
        "elem_rate": 25.6,
        "elem_count": 1578,
        "jhs_rate": 69.0,
        "jhs_count": 2372
    },
    "39": {
        "combined_rate": 34.9,
        "combined_count": 1595,
        "elem_rate": 20.2,
        "elem_count": 604,
        "jhs_rate": 62.4,
        "jhs_count": 991
    },
    "40": {
        "combined_rate": 47.2,
        "combined_count": 19602,
        "elem_rate": 29.3,
        "elem_count": 8008,
        "jhs_rate": 81.7,
        "jhs_count": 11594
    },
    "41": {
        "combined_rate": 33.2,
        "combined_count": 2228,
        "elem_rate": 19.7,
        "elem_count": 858,
        "jhs_rate": 57.7,
        "jhs_count": 1370
    },
    "42": {
        "combined_rate": 38.1,
        "combined_count": 3798,
        "elem_rate": 21.8,
        "elem_count": 1420,
        "jhs_rate": 68.7,
        "jhs_count": 2378
    },
    "43": {
        "combined_rate": 40.7,
        "combined_count": 5781,
        "elem_rate": 22.9,
        "elem_count": 2133,
        "jhs_rate": 74.7,
        "jhs_count": 3648
    },
    "44": {
        "combined_rate": 36.9,
        "combined_count": 3075,
        "elem_rate": 20.9,
        "elem_count": 1133,
        "jhs_rate": 66.6,
        "jhs_count": 1942
    },
    "45": {
        "combined_rate": 32.6,
        "combined_count": 2842,
        "elem_rate": 18.6,
        "elem_count": 1054,
        "jhs_rate": 58.3,
        "jhs_count": 1788
    },
    "46": {
        "combined_rate": 38.2,
        "combined_count": 4982,
        "elem_rate": 20.8,
        "elem_count": 1768,
        "jhs_rate": 70.4,
        "jhs_count": 3214
    },
    "47": {
        "combined_rate": 49.5,
        "combined_count": 7432,
        "elem_rate": 35.4,
        "elem_count": 3523,
        "jhs_rate": 77.5,
        "jhs_count": 3909
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
        assert pref["elem_absenteeism_count"] == gt_data["elem_count"], f"{code}: elem_absenteeism_count mismatch"
        assert pref["jhs_absenteeism_rate"] == gt_data["jhs_rate"], f"{code}: jhs_absenteeism_rate mismatch"
        assert pref["jhs_absenteeism_count"] == gt_data["jhs_count"], f"{code}: jhs_absenteeism_count mismatch"

        assert ext_entry["absenteeism_combined_rate"] == gt_data["combined_rate"], f"ext {code}: absenteeism_combined_rate mismatch"
        assert ext_entry["absenteeism_combined_count"] == gt_data["combined_count"], f"ext {code}: absenteeism_combined_count mismatch"
        assert ext_entry["elem_absenteeism_rate"] == gt_data["elem_rate"], f"ext {code}: elem_absenteeism_rate mismatch"
        assert ext_entry["elem_absenteeism_count"] == gt_data["elem_count"], f"ext {code}: elem_absenteeism_count mismatch"
        assert ext_entry["jhs_absenteeism_rate"] == gt_data["jhs_rate"], f"ext {code}: jhs_absenteeism_rate mismatch"
        assert ext_entry["jhs_absenteeism_count"] == gt_data["jhs_count"], f"ext {code}: jhs_absenteeism_count mismatch"


if __name__ == "__main__":
    test_census_demographics_estat_live_ground_truth()
    test_cross_source_indicators_integrity()
    test_external_stats_official_ground_truth()
    test_absenteeism_official_ground_truth()
    print("ALL CROSS-SOURCE INDICATOR INTEGRITY & CENSUS LIVE GROUND TRUTH TESTS PASSED SUCCESSFULLY!")


