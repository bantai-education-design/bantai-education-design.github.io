#!/usr/bin/env python3
"""Generic regional importer for FY2026 MEXT/JST national official research-designated schools
(DX High School, Sakidori Research School, JST SSH all active schools) with optional prefecture extras.

Usage:
  python tools/school-database/import_region_research.py kinki
  python tools/school-database/import_region_research.py chugoku
  python tools/school-database/import_region_research.py shikoku
  python tools/school-database/import_region_research.py kyushu
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "school-database"
MEXT_CACHE = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\national_and_tohoku\mext_r8_national_parsed.json"
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_kanto_research_designations import SchoolMatcher, save_designations
from enable_research_ui import update_html, update_js

REGIONS: dict[str, list[tuple[str, str]]] = {
    "kinki": [
        ("mie", "三重県"),
        ("shiga", "滋賀県"),
        ("kyoto", "京都府"),
        ("osaka", "大阪府"),
        ("hyogo", "兵庫県"),
        ("nara", "奈良県"),
        ("wakayama", "和歌山県"),
    ],
    "chugoku": [
        ("tottori", "鳥取県"),
        ("shimane", "島根県"),
        ("okayama", "岡山県"),
        ("hiroshima", "広島県"),
        ("yamaguchi", "山口県"),
    ],
    "shikoku": [
        ("tokushima", "徳島県"),
        ("kagawa", "香川県"),
        ("ehime", "愛媛県"),
        ("kochi", "高知県"),
    ],
    "kyushu": [
        ("fukuoka", "福岡県"),
        ("saga", "佐賀県"),
        ("nagasaki", "長崎県"),
        ("kumamoto", "熊本県"),
        ("oita", "大分県"),
        ("miyazaki", "宮崎県"),
        ("kagoshima", "鹿児島県"),
        ("okinawa", "沖縄県"),
    ],
}

MEXT_NOTE = (
    "研究指定校（年度・教科等・事業名）は、文部科学省「令和8年度高等学校DX加速化推進事業（DXハイスクール）採択校一覧」"
    "「教育課程柔軟化サキドリ研究校指定一覧」およびJST「スーパーサイエンスハイスクール（SSH）指定校一覧」をもとに収録しています。"
)


def run_region(region_key: str) -> None:
    if region_key not in REGIONS:
        raise SystemExit(f"Unknown region: {region_key}")
    mext_data = json.loads(MEXT_CACHE.read_text(encoding="utf-8"))
    total_sc = 0
    total_ent = 0
    for slug, pref_name in REGIONS[region_key]:
        schools = json.loads((DATA_DIR / f"{slug}.json").read_text(encoding="utf-8"))
        matcher = SchoolMatcher(schools, pref_name)
        per_school: dict[int, list[dict]] = defaultdict(list)
        unmatched = []
        for rec in mext_data.get(slug, []):
            idxs = matcher.match(rec["school_name"], muni_hint=rec.get("muni_hint", ""))
            if not idxs:
                unmatched.append(rec["school_name"])
                continue
            for i in idxs:
                per_school[i].append({
                    "year": rec["year"],
                    "subject": rec["subject"],
                    "designation": rec["designation"],
                    "authority": rec["authority"],
                })
        sc_cnt, ent_cnt = save_designations(slug, schools, per_school, pref_name)
        update_html(slug, pref_name, "研究指定校（令和8年度）", MEXT_NOTE, ["文部科学省"])
        update_js(slug, "研究指定校（令和8年度）")
        total_sc += sc_cnt
        total_ent += ent_cnt
        print(f"[{slug}] schools={sc_cnt}, entries={ent_cnt}, unmatched={len(unmatched)}")
    print(f"{region_key.upper()} TOTAL: schools={total_sc}, entries={total_ent}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: import_region_research.py <kinki|chugoku|shikoku|kyushu>")
    run_region(sys.argv[1])
