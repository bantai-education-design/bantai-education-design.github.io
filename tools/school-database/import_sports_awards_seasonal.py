#!/usr/bin/env python3
"""Import verified 2024-2026 Summer (Swimming, Water Polo, Track & Field) and
Winter (Ski, Speed Skating, Ice Hockey) Inter-High school-team results into Nationwide School DB.
Also adds '夏期競技（水泳・水球・陸上）' and '冬期競技（スキー・スケート・アイスホッケー）'
to all 47 prefecture sports filter dropdowns.
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

CAT_SUMMER = "夏期競技（水泳・水球・陸上）"
CAT_WINTER = "冬期競技（スキー・スケート・アイスホッケー）"

# (pref, school_name, sport, contest, year, division, award)
SEASONAL_RECORDS: list[tuple[str, str, str, str, str, str, str]] = [
    # --- 夏期：インターハイ競泳 学校対抗総合 ---
    ("愛知県", "豊川高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）競泳", "2024年（令和6年度）", "男子総合", "優勝"),
    ("愛知県", "中京大学附属中京高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）競泳", "2024年（令和6年度）", "男子総合", "準優勝"),
    ("東京都", "日本大学豊山高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）競泳", "2024年（令和6年度）", "男子総合", "3位"),
    ("愛知県", "豊川高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）競泳", "2024年（令和6年度）", "女子総合", "優勝"),
    ("神奈川県", "日本大学藤沢高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）競泳", "2024年（令和6年度）", "女子総合", "準優勝"),
    ("東京都", "武蔵野高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）競泳", "2024年（令和6年度）", "女子総合", "3位"),

    ("愛知県", "豊川高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）競泳", "2025年（令和7年度）", "男子総合", "優勝"),
    ("愛知県", "豊川高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）競泳", "2025年（令和7年度）", "女子総合", "3位"),

    ("東京都", "日本大学豊山高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）競泳", "2026年（第94回）", "男子総合", "優勝"),
    ("愛知県", "豊川高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）競泳", "2026年（第94回）", "男子総合", "準優勝"),
    ("愛知県", "豊川高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）競泳", "2026年（第94回）", "女子総合", "優勝"),
    ("東京都", "淑徳巣鴨高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）競泳", "2026年（第94回）", "女子総合", "準優勝"),

    # --- 夏期：インターハイ水球 ---
    ("京都府", "京都府立鳥羽高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）水球", "2024年（令和6年度）", "全国大会", "優勝"),
    ("埼玉県", "埼玉栄高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）水球", "2024年（令和6年度）", "全国大会", "準優勝"),
    ("東京都", "明治大学付属中野高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）水球", "2024年（令和6年度）", "全国大会", "3位"),

    ("群馬県", "群馬県立前橋商業高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）水球", "2025年（令和7年度）", "全国大会", "優勝"),
    ("埼玉県", "埼玉栄高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）水球", "2025年（令和7年度）", "全国大会", "準優勝"),
    ("山口県", "山口県立西京高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）水球", "2025年（令和7年度）", "全国大会", "3位"),

    ("三重県", "三重県立四日市中央工業高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）水球", "2026年（令和8年度）", "全国大会", "優勝"),
    ("埼玉県", "埼玉栄高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）水球", "2026年（令和8年度）", "全国大会", "準優勝"),
    ("岐阜県", "岐阜県立大垣東高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）水球", "2026年（令和8年度）", "全国大会", "3位"),

    # --- 夏期：インターハイ陸上競技 学校対抗総合優勝 ---
    ("京都府", "洛南高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）陸上競技", "2024年（令和6年度）", "男子総合", "優勝"),
    ("大阪府", "大阪府立大塚高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）陸上競技", "2024年（令和6年度）", "女子総合", "優勝"),
    ("京都府", "洛南高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）陸上競技", "2025年（令和7年度）", "男子総合", "優勝"),
    ("埼玉県", "西武台高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）陸上競技", "2025年（令和7年度）", "女子総合", "優勝"),
    ("京都府", "洛南高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）陸上競技", "2026年（令和8年度）", "男子総合", "優勝"),
    ("神奈川県", "東海大学付属相模高等学校", CAT_SUMMER, "全国高等学校総合体育大会（インターハイ）陸上競技", "2026年（令和8年度）", "女子総合", "優勝"),

    # --- 冬期：全国高校スキー大会（インターハイ）学校対抗総合 ---
    ("長野県", "長野県飯山高等学校", CAT_WINTER, "全国高等学校スキー大会（インターハイ）", "2024年（第73回）", "男子総合", "優勝"),
    ("長野県", "長野県飯山高等学校", CAT_WINTER, "全国高等学校スキー大会（インターハイ）", "2025年（第74回）", "男子総合", "優勝"),
    ("秋田県", "秋田県立秋田北鷹高等学校", CAT_WINTER, "全国高等学校スキー大会（インターハイ）", "2025年（第74回）", "女子総合", "優勝"),
    ("秋田県", "秋田県立鹿角高等学校", CAT_WINTER, "全国高等学校スキー大会（インターハイ）", "2025年（第74回）", "女子総合", "準優勝"),
    ("長野県", "長野県飯山高等学校", CAT_WINTER, "全国高等学校スキー大会（インターハイ）", "2025年（第74回）", "女子総合", "準優勝"),

    ("長野県", "長野県飯山高等学校", CAT_WINTER, "全国高等学校スキー大会（インターハイ）", "2026年（第75回）", "男子総合", "優勝"),
    ("新潟県", "新潟県立十日町高等学校", CAT_WINTER, "全国高等学校スキー大会（インターハイ）", "2026年（第75回）", "男子総合", "準優勝"),
    ("北海道", "北海道下川商業高等学校", CAT_WINTER, "全国高等学校スキー大会（インターハイ）", "2026年（第75回）", "男子総合", "3位"),
    ("北海道", "東海大学付属札幌高等学校", CAT_WINTER, "全国高等学校スキー大会（インターハイ）", "2026年（第75回）", "男子総合", "3位"),
    ("山形県", "山形県立新庄南高等学校", CAT_WINTER, "全国高等学校スキー大会（インターハイ）", "2026年（第75回）", "女子総合", "優勝"),
    ("山形県", "日本大学山形高等学校", CAT_WINTER, "全国高等学校スキー大会（インターハイ）", "2026年（第75回）", "女子総合", "準優勝"),
    ("長野県", "長野県飯山高等学校", CAT_WINTER, "全国高等学校スキー大会（インターハイ）", "2026年（第75回）", "女子総合", "3位"),

    # --- 冬期：全国高校アイスホッケー（インターハイ） ---
    ("北海道", "駒澤大学附属苫小牧高等学校", CAT_WINTER, "全国高等学校アイスホッケー競技選手権大会（インターハイ）", "2024年（第73回）", "全国大会", "優勝"),
    ("北海道", "武修館高等学校", CAT_WINTER, "全国高等学校アイスホッケー競技選手権大会（インターハイ）", "2024年（第73回）", "全国大会", "準優勝"),
    ("北海道", "北海道清水高等学校", CAT_WINTER, "全国高等学校アイスホッケー競技選手権大会（インターハイ）", "2024年（第73回）", "全国大会", "3位"),
    ("北海道", "白樺学園高等学校", CAT_WINTER, "全国高等学校アイスホッケー競技選手権大会（インターハイ）", "2024年（第73回）", "全国大会", "3位"),

    ("北海道", "駒澤大学附属苫小牧高等学校", CAT_WINTER, "全国高等学校アイスホッケー競技選手権大会（インターハイ）", "2025年（第74回）", "全国大会", "優勝"),
    ("北海道", "北海道清水高等学校", CAT_WINTER, "全国高等学校アイスホッケー競技選手権大会（インターハイ）", "2025年（第74回）", "全国大会", "準優勝"),

    ("北海道", "駒澤大学附属苫小牧高等学校", CAT_WINTER, "全国高等学校アイスホッケー競技選手権大会（インターハイ）", "2026年（第75回）", "全国大会", "優勝"),
    ("北海道", "武修館高等学校", CAT_WINTER, "全国高等学校アイスホッケー競技選手権大会（インターハイ）", "2026年（第75回）", "全国大会", "準優勝"),

    # --- 冬期：全国高校スピードスケート（インターハイ）学校対抗総合 ---
    ("北海道", "白樺学園高等学校", CAT_WINTER, "全国高等学校スピードスケート競技選手権大会（インターハイ）", "2024年（第73回）", "男子総合", "優勝"),
    ("北海道", "白樺学園高等学校", CAT_WINTER, "全国高等学校スピードスケート競技選手権大会（インターハイ）", "2024年（第73回）", "女子総合", "準優勝"),
    ("北海道", "白樺学園高等学校", CAT_WINTER, "全国高等学校スピードスケート競技選手権大会（インターハイ）", "2025年（第74回）", "男子総合", "優勝"),
    ("北海道", "北海道帯広三条高等学校", CAT_WINTER, "全国高等学校スピードスケート競技選手権大会（インターハイ）", "2025年（第74回）", "女子総合", "優勝"),
    ("北海道", "白樺学園高等学校", CAT_WINTER, "全国高等学校スピードスケート競技選手権大会（インターハイ）", "2026年（第75回）", "男子総合", "優勝"),
    ("北海道", "白樺学園高等学校", CAT_WINTER, "全国高等学校スピードスケート競技選手権大会（インターハイ）", "2026年（第75回）", "女子総合", "3位"),
]

AWARD_ORDER = {"優勝": 0, "準優勝": 1, "3位": 2, "ベスト4": 2}


def update_html_dropdowns() -> int:
    updated = 0
    for slug in PREF_SLUGS.values():
        p = ROOT / "tools" / "school-database" / slug / "index.html"
        html = p.read_text(encoding="utf-8")
        if CAT_SUMMER in html:
            continue
        html = html.replace(
            "<label>スポーツ・武道全国大会実績（高校・中学主要大会・武道・フェンシング）</label>",
            "<label>スポーツ・武道全国大会実績（高校・中学・武道・夏期・冬期）</label>",
            1,
        )
        html = html.replace(
            '<option value="中学校全国大会（全中・駅伝）">中学校全国大会（全中・駅伝）</option>',
            '<option value="夏期競技（水泳・水球・陸上）">夏期競技（水泳・水球・陸上）</option>\n'
            '                  <option value="冬期競技（スキー・スケート・アイスホッケー）">冬期競技（スキー・スケート・アイスホッケー）</option>\n'
            '                  <option value="中学校全国大会（全中・駅伝）">中学校全国大会（全中・駅伝）</option>',
            1,
        )
        p.write_text(html, encoding="utf-8")
        updated += 1
    return updated


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

    for pref, sname, sport, contest, year, division, award in SEASONAL_RECORDS:
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
                "sport": sport,
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
    prefs_with_sports = 0
    newly_added = 0

    for pref_name, slug in PREF_SLUGS.items():
        schools = pref_schools[slug]
        sc_add = additions.get(slug, {})
        changed = False
        p_sc = 0
        for idx, sc in enumerate(schools):
            existing = list(sc.get("sports_awards") or [])
            new_items = sc_add.get(idx, [])
            combined = existing + new_items
            if not combined:
                continue
            deduped = []
            seen = set()
            for e in combined:
                k = (e["sport"], e["contest"], e["year"], e["division"], e["award"])
                if k in seen:
                    continue
                seen.add(k)
                deduped.append(e)
            delta = max(0, len(deduped) - len(existing))
            if delta > 0:
                changed = True
                newly_added += delta
            deduped.sort(
                key=lambda x: (
                    -int(re.search(r"20\d{2}", x["year"]).group(0)) if re.search(r"20\d{2}", x["year"]) else -2024,
                    AWARD_ORDER.get(x["award"], 9),
                    x["sport"],
                )
            )
            sc["sports_awards"] = deduped
            p_sc += 1
            total_sc += 1
            total_ent += len(deduped)
        if p_sc > 0:
            prefs_with_sports += 1
        if changed:
            out_path = DATA_DIR / f"{slug}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(schools, f, ensure_ascii=False, indent=2)
                f.write("\n")

    html_updated = update_html_dropdowns()
    print(f"MATCHED seasonal records: {matched_cnt}/{len(SEASONAL_RECORDS)} (unmatched={len(unmatched)})")
    print(f"TOTAL school DB sports_awards: {prefs_with_sports}/47 prefectures, {total_sc} schools, {total_ent} entries (+{newly_added} new)")
    print(f"Updated HTML dropdowns: {html_updated}/47")
    if unmatched:
        print("Unmatched:", unmatched)


if __name__ == "__main__":
    main()
