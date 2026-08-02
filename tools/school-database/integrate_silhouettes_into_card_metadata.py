#!/usr/bin/env python3
"""Add a `silhouette` (Ban.Tai独自の都道府県地域マーク) block to every
prefecture entry in data/school-database/prefecture-card-metadata.json.

This is NOT a prefectural crest/flag/official symbol — see
docs/school-database/prefecture-silhouettes-source-manifest.md. All 47
prefectures get `available: true` since the silhouettes are generated from
freely-licensed (CC BY 4.0 compatible) government administrative-boundary
data, unlike the abandoned official-crest approach (PR #95) where only 1 of
47 prefectures had a usable mark.

Any leftover `emblem` key (from the abandoned official-crest approach) is
explicitly removed if present, since that data must not ship to production.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CARD_METADATA_PATH = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
SILHOUETTES_DIR = ROOT / "assets" / "images" / "prefecture-silhouettes"

REFERENCE_DATE = "2026-01-01"
SOURCE_LABEL = "国土数値情報 行政区域データ"

PREFECTURE_CODE_NUMBER = {
    "hokkaido": "01", "aomori": "02", "iwate": "03", "miyagi": "04", "akita": "05",
    "yamagata": "06", "fukushima": "07", "ibaraki": "08", "tochigi": "09", "gunma": "10",
    "saitama": "11", "chiba": "12", "tokyo": "13", "kanagawa": "14", "niigata": "15",
    "toyama": "16", "ishikawa": "17", "fukui": "18", "yamanashi": "19", "nagano": "20",
    "gifu": "21", "shizuoka": "22", "aichi": "23", "mie": "24", "shiga": "25",
    "kyoto": "26", "osaka": "27", "hyogo": "28", "nara": "29", "wakayama": "30",
    "tottori": "31", "shimane": "32", "okayama": "33", "hiroshima": "34", "yamaguchi": "35",
    "tokushima": "36", "kagawa": "37", "ehime": "38", "kochi": "39", "fukuoka": "40",
    "saga": "41", "nagasaki": "42", "kumamoto": "43", "oita": "44", "miyazaki": "45",
    "kagoshima": "46", "okinawa": "47",
}


def main() -> None:
    payload = json.loads(CARD_METADATA_PATH.read_text(encoding="utf-8"))
    prefectures = payload["prefectures"]

    missing_files = []
    for pref in prefectures:
        code = pref["prefecture_code"]
        pref.pop("emblem", None)  # 公式章方式（見送り済み）の残骸を本番データへ残さない。

        number = PREFECTURE_CODE_NUMBER[code]
        svg_path = SILHOUETTES_DIR / f"{number}-{code}.svg"
        if not svg_path.is_file():
            missing_files.append(str(svg_path))
            continue

        pref["silhouette"] = {
            "available": True,
            "src": f"/assets/images/prefecture-silhouettes/{number}-{code}.svg",
            "alt": "",
            "source": SOURCE_LABEL,
            "reference_date": REFERENCE_DATE,
        }

    if missing_files:
        raise ValueError(f"silhouette SVG not found for: {missing_files}")

    available_count = sum(1 for p in prefectures if p["silhouette"]["available"])
    if available_count != 47:
        raise ValueError(f"expected 47 available silhouettes, got {available_count}")

    CARD_METADATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {CARD_METADATA_PATH} with silhouette data for {available_count}/47 prefectures")


if __name__ == "__main__":
    main()
