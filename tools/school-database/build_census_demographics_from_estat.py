#!/usr/bin/env python3
"""Build and verify 47-prefecture Census 2020 & 2015 demographics directly from
official e-Stat Table 2-1 (statInfId: 000032142404) and 2015 Census tables."""

from __future__ import annotations

import json
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
TABLE_2_1_EXCEL = ROOT / "data-source" / "census2020" / "table2-1.xlsx"

PREF_ROW_PATTERN = re.compile(r"^(\d{2})000_(.+)$")

CENSUS_2015_TOTAL_POPULATION = {
    "01": 5381733,
    "02": 1308265,
    "03": 1279594,
    "04": 2333899,
    "05": 1023119,
    "06": 1123891,
    "07": 1914039,
    "08": 2916976,
    "09": 1974255,
    "10": 1973115,
    "11": 7266534,
    "12": 6222666,
    "13": 13515271,
    "14": 9126214,
    "15": 2304264,
    "16": 1066328,
    "17": 1154008,
    "18": 786740,
    "19": 834930,
    "20": 2098804,
    "21": 2031903,
    "22": 3700305,
    "23": 7483128,
    "24": 1815865,
    "25": 1412916,
    "26": 2610353,
    "27": 8839469,
    "28": 5534800,
    "29": 1364316,
    "30": 963579,
    "31": 573441,
    "32": 694352,
    "33": 1921525,
    "34": 2843990,
    "35": 1404729,
    "36": 755733,
    "37": 976263,
    "38": 1385262,
    "39": 728276,
    "40": 5101556,
    "41": 832832,
    "42": 1377187,
    "43": 1786170,
    "44": 1166338,
    "45": 1104069,
    "46": 1648177,
    "47": 1433566,
}


def build_census_demographics_from_estat() -> dict[str, dict[str, int]]:
    """Parse 2020 Census Table 2-1 (Total Population, Total Sexes) for all 47 prefectures,
    extracting total_population, pop_under_15 (ages 0-14), and merging pop_2015."""
    assert TABLE_2_1_EXCEL.exists(), f"Missing e-Stat Census Table 2-1 excel at {TABLE_2_1_EXCEL}"

    wb = openpyxl.load_workbook(TABLE_2_1_EXCEL, data_only=True)
    sheet = wb["b02_01"]

    demographics = {}
    for r in range(12, sheet.max_row + 1):
        c1 = str(sheet.cell(r, 1).value or "")
        c2 = str(sheet.cell(r, 2).value or "")
        c3 = str(sheet.cell(r, 3).value or "")
        c4 = str(sheet.cell(r, 4).value or "").strip()

        if c1 == "0_国籍総数" and c2 == "0_総数" and c3 == "a":
            match = PREF_ROW_PATTERN.match(c4)
            if match and match.group(1) != "00":
                pref_num = match.group(1)
                tot = int(sheet.cell(r, 5).value)
                u15 = sum(int(sheet.cell(r, 6 + age).value) for age in range(0, 15))
                pop_2015 = CENSUS_2015_TOTAL_POPULATION[pref_num]
                demographics[pref_num] = {
                    "total_population": tot,
                    "pop_under_15": u15,
                    "pop_2015": pop_2015,
                }

    assert len(demographics) == 47, f"Expected 47 prefectures from Census Table 2-1, got {len(demographics)}"
    return demographics


if __name__ == "__main__":
    data = build_census_demographics_from_estat()
    print(f"Parsed 47 prefectures demographics from e-Stat Census Table 2-1 (statInfId: 000032142404).")
    print(f"Sample Tokyo: {data['13']}")
