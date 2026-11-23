#!/usr/bin/env python3
"""Import verified 2024-2026 national high school cultural club tournament results
into Nationwide School DB (data/school-database/*.json) as `culture_awards`.

Covered domains:
  1. 演劇: 全国高等学校演劇大会 2024(第70回)・2025(第71回)・2026(第72回) 最優秀賞・優秀賞
  2. 書道: 書道パフォーマンス甲子園 2024(第17回)・2025(第18回)・2026(第19回) 優勝・準優勝・3位
  3. 将棋: 全国高等学校将棋選手権大会（団体戦）2024・2025・2026 男女優勝
  4. 囲碁: 全国高等学校囲碁選手権大会（団体戦）2024・2025・2026 男女優勝
  5. 箏曲・日本音楽: 全国高等学校総合文化祭 日本音楽部門 2025・2026 最優秀賞（文部科学大臣賞）
  6. 華道: 全国高校生花いけバトル 2024・2025 優勝
  7. 絵画・漫画: まんが甲子園 2024(第33回)・2026(第35回) 最優秀賞・第2位
  8. ロボット: 全国高等学校ロボット競技大会 2024・2025・2026 優勝・準優勝
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "school-database"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_kanto_research_designations import SchoolMatcher
from mext_national_research import PREF_SLUGS

# (pref, school_name, category, contest, year, division, award)
CULTURE_RECORDS: list[tuple[str, str, str, str, str, str, str]] = [
    # --- 1. 演劇 ---
    ("徳島県", "徳島県立城東高等学校", "演劇", "全国高等学校演劇大会", "2024年（第70回）", "全国大会", "最優秀賞"),
    ("岐阜県", "岐阜県立長良高等学校", "演劇", "全国高等学校演劇大会", "2024年（第70回）", "全国大会", "優秀賞"),
    ("宮崎県", "宮崎県立宮崎南高等学校", "演劇", "全国高等学校演劇大会", "2024年（第70回）", "全国大会", "優秀賞"),
    ("青森県", "青森県立青森中央高等学校", "演劇", "全国高等学校演劇大会", "2024年（第70回）", "全国大会", "優秀賞"),

    ("長野県", "長野県松本美須々ヶ丘高等学校", "演劇", "全国高等学校演劇大会", "2025年（第71回）", "全国大会", "最優秀賞"),
    ("兵庫県", "神戸常盤女子高等学校", "演劇", "全国高等学校演劇大会", "2025年（第71回）", "全国大会", "優秀賞"),
    ("北海道", "北海道網走南ケ丘高等学校", "演劇", "全国高等学校演劇大会", "2025年（第71回）", "全国大会", "優秀賞"),
    ("青森県", "青森県立青森中央高等学校", "演劇", "全国高等学校演劇大会", "2025年（第71回）", "全国大会", "優秀賞"),

    ("徳島県", "徳島県立城南高等学校", "演劇", "全国高等学校演劇大会", "2026年（第72回）", "全国大会", "最優秀賞"),
    ("山口県", "山口県立光高等学校", "演劇", "全国高等学校演劇大会", "2026年（第72回）", "全国大会", "優秀賞"),
    ("鹿児島県", "鹿児島県立伊集院高等学校", "演劇", "全国高等学校演劇大会", "2026年（第72回）", "全国大会", "優秀賞"),
    ("埼玉県", "細田学園高等学校", "演劇", "全国高等学校演劇大会", "2026年（第72回）", "全国大会", "優秀賞"),

    # --- 2. 書道 ---
    ("鳥取県", "鳥取城北高等学校", "書道", "書道パフォーマンス甲子園", "2024年（第17回）", "全国大会", "優勝"),
    ("茨城県", "水戸葵陵高等学校", "書道", "書道パフォーマンス甲子園", "2024年（第17回）", "全国大会", "準優勝"),
    ("長野県", "長野県松本蟻ヶ崎高等学校", "書道", "書道パフォーマンス甲子園", "2024年（第17回）", "全国大会", "3位"),

    ("茨城県", "水戸葵陵高等学校", "書道", "書道パフォーマンス甲子園", "2025年（第18回）", "全国大会", "優勝"),
    ("長野県", "長野県松本蟻ヶ崎高等学校", "書道", "書道パフォーマンス甲子園", "2025年（第18回）", "全国大会", "準優勝"),
    ("福岡県", "福岡県立八幡中央高等学校", "書道", "書道パフォーマンス甲子園", "2025年（第18回）", "全国大会", "3位"),

    ("茨城県", "水戸葵陵高等学校", "書道", "書道パフォーマンス甲子園", "2026年（第19回）", "全国大会", "優勝"),
    ("長野県", "長野県松本蟻ヶ崎高等学校", "書道", "書道パフォーマンス甲子園", "2026年（第19回）", "全国大会", "準優勝"),
    ("鳥取県", "鳥取城北高等学校", "書道", "書道パフォーマンス甲子園", "2026年（第19回）", "全国大会", "3位"),

    # --- 3. 将棋 ---
    ("埼玉県", "埼玉県立浦和高等学校", "将棋", "全国高等学校将棋選手権大会", "2024年（第60回）", "男子団体", "優勝"),
    ("山梨県", "駿台甲府高等学校", "将棋", "全国高等学校将棋選手権大会", "2024年（第60回）", "女子団体", "優勝"),
    ("東京都", "海城高等学校", "将棋", "全国高等学校将棋選手権大会", "2025年（第61回）", "男子団体", "優勝"),
    ("石川県", "金沢大学人間社会学域学校教育学類附属高等学校", "将棋", "全国高等学校将棋選手権大会", "2025年（第61回）", "女子団体", "優勝"),
    ("東京都", "攻玉社高等学校", "将棋", "全国高等学校将棋選手権大会", "2026年（第62回）", "男子団体", "優勝"),
    ("大阪府", "近畿大学附属高等学校", "将棋", "全国高等学校将棋選手権大会", "2026年（第62回）", "女子団体", "優勝"),

    # --- 4. 囲碁 ---
    ("宮城県", "宮城県仙台第二高等学校", "囲碁", "全国高等学校囲碁選手権大会", "2024年（第48回）", "男子団体", "優勝"),
    ("東京都", "白百合学園高等学校", "囲碁", "全国高等学校囲碁選手権大会", "2024年（第48回）", "女子団体", "優勝"),
    ("東京都", "駒場東邦高等学校", "囲碁", "全国高等学校囲碁選手権大会", "2025年（第49回）", "男子団体", "優勝"),
    ("愛知県", "南山高等学校", "囲碁", "全国高等学校囲碁選手権大会", "2025年（第49回）", "女子団体", "優勝"),
    ("兵庫県", "灘高等学校", "囲碁", "全国高等学校囲碁選手権大会", "2026年（第50回）", "男子団体", "優勝"),
    ("愛知県", "南山高等学校", "囲碁", "全国高等学校囲碁選手権大会", "2026年（第50回）", "女子団体", "優勝"),

    # --- 5. 箏曲・日本音楽 ---
    ("大阪府", "関西創価高等学校", "箏曲・日本音楽", "全国高等学校総合文化祭 日本音楽部門（箏曲）", "2025年（第49回）", "全国大会", "最優秀賞"),
    ("東京都", "創価高等学校", "箏曲・日本音楽", "全国高等学校総合文化祭 日本音楽部門（箏曲）", "2026年（第50回）", "全国大会", "最優秀賞"),

    # --- 6. 華道 ---
    ("香川県", "香川県立飯山高等学校", "華道", "全国高校生花いけバトル", "2024年（第8回）", "全国大会", "優勝"),
    ("東京都", "正則学園高等学校", "華道", "全国高校生花いけバトル", "2024年（第4回全国選抜）", "全国選抜", "優勝"),
    ("東京都", "正則学園高等学校", "華道", "全国高校生花いけバトル", "2025年（第9回）", "全国大会", "優勝"),

    # --- 7. 絵画・漫画 ---
    ("富山県", "高岡龍谷高等学校", "絵画・漫画", "全国高等学校漫画選手権大会（まんが甲子園）", "2024年（第33回）", "全国大会", "最優秀賞"),
    ("高知県", "土佐高等学校", "絵画・漫画", "全国高等学校漫画選手権大会（まんが甲子園）", "2024年（第33回）", "全国大会", "準優勝"),
    ("富山県", "富山県立高岡高等学校", "絵画・漫画", "全国高等学校漫画選手権大会（まんが甲子園）", "2026年（第35回）", "全国大会", "最優秀賞"),

    # --- 8. ロボット ---
    ("長野県", "長野県駒ヶ根工業高等学校", "ロボット", "全国高等学校ロボット競技大会", "2024年（第32回）", "全国大会", "優勝"),
    ("新潟県", "新潟県立長岡工業高等学校", "ロボット", "全国高等学校ロボット競技大会", "2025年（第33回）", "全国大会", "優勝"),
    ("大分県", "大分県立大分工業高等学校", "ロボット", "全国高等学校ロボット競技大会", "2025年（第33回）", "全国大会", "準優勝"),
    ("新潟県", "新潟県立長岡工業高等学校", "ロボット", "全国高等学校ロボット競技大会", "2026年（第34回）", "全国大会", "優勝"),
]

AWARD_ORDER = {"最優秀賞": 0, "優勝": 0, "準優勝": 1, "優秀賞": 1, "3位": 2}


def main() -> None:
    pref_schools: dict[str, list[dict]] = {}
    matchers: dict[str, SchoolMatcher] = {}
    for pref_name, slug in PREF_SLUGS.items():
        path = DATA_DIR / f"{slug}.json"
        schools = json.loads(path.read_text(encoding="utf-8"))
        pref_schools[slug] = schools
        matchers[slug] = SchoolMatcher(schools, pref_name)

    additions: dict[str, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))
    matched_cnt = 0
    unmatched: list[tuple[str, str, str]] = []

    for pref, sname, cat, contest, year, division, award in CULTURE_RECORDS:
        slug = PREF_SLUGS[pref]
        idxs = matchers[slug].match(sname)
        if not idxs:
            alt = re.sub(r"^(?:北海道|東京都|(?:大阪|京都)府|.+?県)立?", "", sname)
            idxs = matchers[slug].match(alt)
        if not idxs:
            base = re.sub(r"(?:高等学校|高校)$", "", sname)
            for i, sc in enumerate(pref_schools[slug]):
                t = str(sc.get("type") or sc.get("school_type") or "")
                if sc.get("name") == base and ("高" in t or "中等" in t):
                    idxs = [i]
                    break
        if idxs:
            additions[slug][idxs[0]].append({
                "category": cat,
                "contest": contest,
                "year": year,
                "division": division,
                "award": award,
            })
            matched_cnt += 1
        else:
            unmatched.append((pref, sname, contest))

    total_sc = 0
    total_ent = 0
    prefs_with_culture = 0

    for pref_name, slug in PREF_SLUGS.items():
        schools = pref_schools[slug]
        sc_add = additions.get(slug, {})
        changed = False
        p_sc = 0
        for idx, sc in enumerate(schools):
            existing = list(sc.get("culture_awards") or [])
            new_items = sc_add.get(idx, [])
            combined = existing + new_items
            if not combined:
                continue
            deduped = []
            seen = set()
            for e in combined:
                k = (e["category"], e["contest"], e["year"], e["division"], e["award"])
                if k in seen:
                    continue
                seen.add(k)
                deduped.append(e)
            if len(deduped) != len(existing):
                changed = True
            deduped.sort(
                key=lambda x: (
                    -int(re.search(r"20\d{2}", x["year"]).group(0)) if re.search(r"20\d{2}", x["year"]) else -2024,
                    AWARD_ORDER.get(x["award"], 9),
                    x["category"],
                )
            )
            sc["culture_awards"] = deduped
            p_sc += 1
            total_sc += 1
            total_ent += len(deduped)
        if p_sc > 0:
            prefs_with_culture += 1
        if changed:
            out_path = DATA_DIR / f"{slug}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(schools, f, ensure_ascii=False, indent=2)
                f.write("\n")

    print(f"MATCHED culture records: {matched_cnt}/{len(CULTURE_RECORDS)} (unmatched={len(unmatched)})")
    print(f"TOTAL school DB culture_awards: {prefs_with_culture}/47 prefectures, {total_sc} schools, {total_ent} entries")
    if unmatched:
        print("Unmatched:", unmatched)


if __name__ == "__main__":
    main()
