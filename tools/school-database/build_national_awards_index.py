#!/usr/bin/env python3
"""Build lightweight nationwide index of schools with sports, culture/kanken, or music awards
from all 47 data/school-database/{slug}.json files into data/school-database/national-awards-index.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "school-database"
OUT_PATH = DATA_DIR / "national-awards-index.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mext_national_research import PREF_SLUGS


def main() -> None:
    records = []
    stats = {
        "total_schools": 0,
        "sports_schools": 0,
        "sports_entries": 0,
        "culture_schools": 0,
        "culture_entries": 0,
        "music_schools": 0,
        "music_entries": 0,
    }
    pref_list = []

    for pref_name, slug in PREF_SLUGS.items():
        pref_list.append({"slug": slug, "name": pref_name})
        path = DATA_DIR / f"{slug}.json"
        schools = json.loads(path.read_text(encoding="utf-8"))
        for sc in schools:
            sports = sc.get("sports_awards") or []
            culture = sc.get("culture_awards") or []
            music = sc.get("music_awards") or []
            if not (sports or culture or music):
                continue
            stats["total_schools"] += 1
            if sports:
                stats["sports_schools"] += 1
                stats["sports_entries"] += len(sports)
            if culture:
                stats["culture_schools"] += 1
                stats["culture_entries"] += len(culture)
            if music:
                stats["music_schools"] += 1
                stats["music_entries"] += len(music)

            records.append({
                "pref": pref_name,
                "pref_slug": slug,
                "name": sc.get("name", ""),
                "type": sc.get("type") or sc.get("school_type") or "",
                "establishment": sc.get("establishment") or sc.get("founder") or "",
                "city": sc.get("city") or "",
                "address": sc.get("address") or "",
                "sports_awards": sports,
                "culture_awards": culture,
                "music_awards": music,
            })

    payload = {
        "stats": stats,
        "prefectures": pref_list,
        "schools": records,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"Built {OUT_PATH.name}: {stats['total_schools']} schools ({size_kb:.1f} KB) | stats={stats}")


if __name__ == "__main__":
    main()
