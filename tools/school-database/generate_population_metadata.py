#!/usr/bin/env python3
"""Generate the Tokyo-only population metadata pilot JSON."""

from __future__ import annotations

import argparse
import csv
import io
import json
import unicodedata
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_URL = "https://www.toukei.metro.tokyo.lg.jp/juukiy/2026/jy26qv0600.csv"
SOURCE_PAGE_URL = "https://www.toukei.metro.tokyo.lg.jp/juukiy/2026/jy26q10601.htm"
OUTPUT_PATH = ROOT / "data" / "school-database" / "prefecture-population-pilot.json"
TOKYO_SCHOOL_JSON = ROOT / "data" / "school-database" / "tokyo.json"

EXPECTED_HEADERS = [
    "地域階層",
    "地域コード",
    "地域",
    "年齢階層",
    "年齢",
    "総数(人)",
    "男(人)",
    "女(人)",
]

AGE_GROUPS = {
    "preschool_3_5": {
        "label": "幼稚園相当年齢",
        "school_type": "幼稚園",
        "age_range": [3, 5],
        "ages": range(3, 6),
    },
    "elementary_6_11": {
        "label": "小学校相当年齢",
        "school_type": "小学校",
        "age_range": [6, 11],
        "ages": range(6, 12),
    },
    "junior_high_12_14": {
        "label": "中学校相当年齢",
        "school_type": "中学校",
        "age_range": [12, 14],
        "ages": range(12, 15),
    },
    "high_school_15_17": {
        "label": "高等学校相当年齢",
        "school_type": "高等学校",
        "age_range": [15, 17],
        "ages": range(15, 18),
    },
}


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value or "").strip()


def parse_int(value: str) -> int:
    normalized = normalize_text(value).replace(",", "")
    if not normalized.isdecimal():
        raise ValueError(f"integer value expected: {value!r}")
    return int(normalized)


def decode_csv_bytes(data: bytes) -> list[dict[str, str]]:
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != EXPECTED_HEADERS:
        raise ValueError(f"unexpected CSV headers: {reader.fieldnames!r}")
    return list(reader)


def load_csv(source_url: str, source_file: Path | None) -> list[dict[str, str]]:
    if source_file:
        return decode_csv_bytes(source_file.read_bytes())

    with urllib.request.urlopen(source_url, timeout=30) as response:
        return decode_csv_bytes(response.read())


def tokyo_japanese_rows(rows: Iterable[dict[str, str]]) -> tuple[int, dict[int, int]]:
    japanese_population: int | None = None
    age_populations: dict[int, int] = {}

    for row in rows:
        if normalize_text(row["地域コード"]) != "13000":
            continue
        if normalize_text(row["地域"]) != "総数":
            continue

        age_label = normalize_text(row["年齢"]).replace(" ", "")
        if age_label == "総数":
            population = parse_int(row["総数(人)"])
            japanese_population = population
            continue
        if age_label.isdecimal():
            age = int(age_label)
            if age <= 17:
                age_populations[age] = parse_int(row["総数(人)"])

    if japanese_population is None:
        raise ValueError("Tokyo total row was not found")
    missing = [age for age in range(0, 18) if age not in age_populations]
    if missing:
        raise ValueError(f"Tokyo age rows are missing: {missing}")
    return japanese_population, age_populations


def share(population: int, japanese_population: int) -> float:
    return round((population / japanese_population) * 100, 6)


def load_school_counts() -> Counter[str]:
    schools = json.loads(TOKYO_SCHOOL_JSON.read_text(encoding="utf-8"))
    return Counter(normalize_text(school.get("school_type", "")) for school in schools)


def build_payload(rows: list[dict[str, str]], accessed_at: str) -> dict[str, object]:
    japanese_population, age_populations = tokyo_japanese_rows(rows)
    school_counts = load_school_counts()

    groups: dict[str, object] = {}
    japanese_age_3_17_population = 0
    population_per_school: dict[str, object] = {}

    for key, config in AGE_GROUPS.items():
        output_key = f"japanese_{key}"
        population = sum(age_populations[age] for age in config["ages"])
        japanese_age_3_17_population += population
        school_count = school_counts[config["school_type"]]
        groups[output_key] = {
            "label": config["label"],
            "school_type": config["school_type"],
            "age_range": config["age_range"],
            "population": population,
            "share_of_japanese_population_percent": share(population, japanese_population),
            "denominator": "japanese_population",
        }
        population_per_school[output_key] = {
            "school_type": config["school_type"],
            "school_count": school_count,
            "population": population,
            "population_per_school": round(population / school_count, 2) if school_count else None,
        }

    groups["japanese_age_3_17"] = {
        "label": "日本人の校種相当年齢人口",
        "school_type": "幼稚園・小学校・中学校・高等学校相当",
        "age_range": [3, 17],
        "population": japanese_age_3_17_population,
        "share_of_japanese_population_percent": share(japanese_age_3_17_population, japanese_population),
        "denominator": "japanese_population",
    }

    return {
        "generated_at": accessed_at,
        "pilot_scope": "tokyo-only",
        "prefectures": {
            "tokyo": {
                "prefecture_code": "13",
                "prefecture_name": "東京都",
                "reference_date": "2026-01-01",
                "population_definition": "住民基本台帳に記載された日本人人口",
                "population_scope": "Japanese residents",
                "denominator": "japanese_population",
                "japanese_population": japanese_population,
                "foreign_residents_included": False,
                "all_residents_age_3_17": None,
                "all_residents_age_3_17_status": "not_available_from_single-year-age official source",
                "age_groups": groups,
                "source": {
                    "publisher": "東京都総務局統計部",
                    "title": "住民基本台帳による東京都の世帯と人口 令和8年1月 第6表 区市町村、年齢（各歳）及び男女別日本人人口",
                    "page_url": SOURCE_PAGE_URL,
                    "csv_url": DEFAULT_SOURCE_URL,
                    "format": "CSV",
                    "accessed_at": accessed_at,
                },
                "additional_analysis": {
                    "population_per_school_simple_ratio": population_per_school,
                    "note": "校種相当年齢人口を同校種の収録校数で割った単純比率です。在学者数、定員、通学区域、国私立の越境通学は反映していません。",
                },
            }
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--source-file", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--accessed-at", default=date.today().isoformat())
    args = parser.parse_args()

    rows = load_csv(args.source_url, args.source_file)
    payload = build_payload(rows, args.accessed_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
