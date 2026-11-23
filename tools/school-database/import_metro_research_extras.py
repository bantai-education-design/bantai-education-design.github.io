#!/usr/bin/env python3
"""Merge prefecture & designated-city official research-designated schools onto existing data
for Aichi (+Nagoya), Osaka (+Osaka City), and Fukuoka (+Fukuoka City / Kitakyushu City).

Preserves all existing MEXT/JST entries and deduplicates cleanly.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "school-database"
METRO_CACHE = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\metro_research"
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_kanto_research_designations import SchoolMatcher, clean, norm_chars
from enable_research_ui import update_html, update_js


def merge_and_save(slug: str, pref_name: str, schools: list[dict], additions: dict[int, list[dict]]) -> tuple[int, int, int]:
    auth_order = {"文部科学省": 0, pref_name: 1, "市町村": 2}
    added_entries = 0
    total_schools = 0
    total_entries = 0

    for idx, sc in enumerate(schools):
        existing = list(sc.get("research_designations") or [])
        new_items = additions.get(idx, [])
        combined = existing + new_items
        if not combined:
            continue

        deduped = []
        seen = set()
        for e in combined:
            key = (e["authority"], e["year"], norm_chars(e.get("subject", "")), norm_chars(e.get("designation", "")))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(e)

        added_entries += max(0, len(deduped) - len(existing))
        deduped.sort(key=lambda x: (auth_order.get(x["authority"], 9), x["designation"], x["subject"]))
        sc["research_designations"] = deduped
        total_schools += 1
        total_entries += len(deduped)

    out_path = DATA_DIR / f"{slug}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(schools, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return total_schools, total_entries, added_entries


# ---------------------------------------------------------------------------
# 1. AICHI (+ Nagoya City)
# ---------------------------------------------------------------------------
def enrich_aichi():
    schools = json.loads((DATA_DIR / "aichi.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "愛知県")
    additions: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    # Source A: 愛知県公式「令和8年度 愛知の研究校（園）一覧」(aichi_r8.pdf, 10 pages)
    with pdfplumber.open(METRO_CACHE / "aichi_r8.pdf") as pdf:
        for page in pdf.pages:
            for t in page.extract_tables():
                for row in t:
                    if not row or len(row) < 6:
                        continue
                    no = clean(row[0]).replace(" ", "")
                    if not no or no == "NO" or no == "ＮＯ":
                        continue
                    sname = clean(row[1]).replace(" ", "")
                    domain = clean(row[3]).replace(" ", "")
                    theme = clean(row[4])
                    pres = clean(row[5])
                    if not sname:
                        continue
                    idxs = matcher.match(sname)
                    if not idxs:
                        unmatched.append(("aichi_r8", sname))
                        continue
                    desig = theme[:65] + ("…" if len(theme) > 65 else "") if theme else "愛知の研究校（園）"
                    entry = {
                        "year": "令和8",
                        "subject": domain or "教育研究",
                        "designation": desig,
                        "authority": "愛知県",
                    }
                    if pres and pres not in ("なし", "無し", "未定", "-"):
                        entry["presentation"] = pres[:40]
                    for i in idxs:
                        additions[i].append(entry)

    # Source B: 名古屋市「NAGOYA School Innovation」研究開発学校 (令和7〜10年度)
    for sname in ["名古屋市立千石小学校", "名古屋市立相生小学校", "名古屋市立日比野中学校", "名古屋市立吉根中学校"]:
        idxs = matcher.match(sname)
        if not idxs:
            unmatched.append(("nagoya_rd", sname))
            continue
        for i in idxs:
            additions[i].append({
                "year": "令和7〜10",
                "subject": "子ども中心の学び・教育課程研究開発",
                "designation": "文部科学省研究開発学校（ナゴヤスクールイノベーション）",
                "authority": "文部科学省",
            })

    sc_cnt, ent_cnt, added = merge_and_save("aichi", "愛知県", schools, additions)
    note = (
        "研究指定校（年度・研究領域・研究主題等）は、愛知県教育委員会「令和8年度 愛知の研究校（園）一覧」、"
        "名古屋市教育委員会「ナゴヤスクールイノベーション（研究開発学校）」、および文部科学省・JSTの令和8年度全国公式一覧をもとに収録しています。"
    )
    update_html("aichi", "愛知県", "研究指定・研究校（令和8年度）", note, ["文部科学省", "愛知県"])
    update_js("aichi", "研究指定・研究校（令和8年度）")
    print(f"[aichi] total_schools={sc_cnt}, total_entries={ent_cnt}, newly_added={added}, unmatched={len(unmatched)}")
    if unmatched:
        print("  aichi unmatched sample:", unmatched[:8])


# ---------------------------------------------------------------------------
# 2. FUKUOKA (+ Fukuoka City & Kitakyushu City)
# ---------------------------------------------------------------------------
def enrich_fukuoka():
    schools = json.loads((DATA_DIR / "fukuoka.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "福岡県")
    additions: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    # Source: 福岡県教育庁義務教育課「令和8年度 教育研究発表校（園）一覧【全体】0916修正」(fukuoka_r8_all.pdf, 12 pages)
    with pdfplumber.open(METRO_CACHE / "fukuoka_r8_all.pdf") as pdf:
        for page in pdf.pages:
            for t in page.extract_tables():
                for row in t:
                    if not row or len(row) < 9:
                        continue
                    sname = clean(row[4]).replace(" ", "")
                    if not sname or "学校" in sname and "名" in sname:
                        continue
                    month = clean(row[0])
                    day = clean(row[2])
                    kubun = clean(row[6]).replace(" ", "")
                    theme = clean(row[8])
                    pres = f"{month}月{day}日" if (month.isdigit() and day.isdigit()) else ""

                    if "文" in kubun or "国" in kubun:
                        auth = "文部科学省"
                    elif "県" in kubun:
                        auth = "福岡県"
                    else:
                        auth = "市町村"

                    # Infer subject keyword from theme if obvious
                    subj = ""
                    for kw in ("国語", "算数", "数学", "理科", "社会", "外国語", "英語", "道徳", "体育", "音楽", "図画工作", "美術", "家庭", "技術", "生活", "総合的な学習", "特別活動", "学級活動", "人権", "特別支援", "書写", "キャリア", "ICT"):
                        if kw in theme:
                            subj = kw
                            break

                    # Handle multiple schools in one cell (split by 、 or ・ or space)
                    raw_names = [s.strip() for s in re.split(r"[、・\n]", sname) if s.strip()]
                    matched_any = False
                    for rn in raw_names:
                        idxs = matcher.match(rn)
                        if not idxs:
                            continue
                        matched_any = True
                        desig = theme[:65] + ("…" if len(theme) > 65 else "") if theme else "教育研究発表校"
                        entry = {
                            "year": "令和8",
                            "subject": subj or "教育研究発表",
                            "designation": desig,
                            "authority": auth,
                        }
                        if pres:
                            entry["presentation"] = pres
                        for i in idxs:
                            additions[i].append(entry)
                    if not matched_any:
                        unmatched.append(("fukuoka_r8", sname))

    sc_cnt, ent_cnt, added = merge_and_save("fukuoka", "福岡県", schools, additions)
    note = (
        "研究指定・発表校（年度・教科等・研究主題）は、福岡県教育庁義務教育課「令和8年度 福岡県教育研究発表校（園）一覧【全体】」"
        "（福岡市・北九州市含む全県集約版）および文部科学省・JSTの令和8年度全国公式一覧をもとに収録しています。"
    )
    update_html("fukuoka", "福岡県", "研究指定・研究発表校（令和8年度）", note, ["文部科学省", "福岡県", "市町村"])
    update_js("fukuoka", "研究指定・研究発表校（令和8年度）")
    print(f"[fukuoka] total_schools={sc_cnt}, total_entries={ent_cnt}, newly_added={added}, unmatched={len(unmatched)}")
    if unmatched:
        print("  fukuoka unmatched sample:", unmatched[:8])


# ---------------------------------------------------------------------------
# 3. OSAKA (+ Osaka City)
# ---------------------------------------------------------------------------
def enrich_osaka():
    schools = json.loads((DATA_DIR / "osaka.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "大阪府")
    additions: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    # Source A: 大阪府 グローバルリーダーズハイスクール（GLHS）全10校
    glhs = [
        "大阪府立北野高等学校", "大阪府立豊中高等学校", "大阪府立茨木高等学校",
        "大阪府立大手前高等学校", "大阪府立四條畷高等学校", "大阪府立高津高等学校",
        "大阪府立天王寺高等学校", "大阪府立三国丘高等学校", "大阪府立岸和田高等学校",
        "大阪府立生野高等学校",
    ]
    for sname in glhs:
        idxs = matcher.match(sname, type_hint="高等学校")
        if not idxs:
            unmatched.append(("osaka_glhs", sname))
            continue
        for i in idxs:
            additions[i].append({
                "year": "継続指定",
                "subject": "グローバル・文理学科探究",
                "designation": "グローバルリーダーズハイスクール（GLHS）",
                "authority": "大阪府",
            })

    # Source B: 大阪市総合教育センター 令和7年度 研究校・実践校
    osaka_city_research = [
        ("令和7", "ESD・グローバル・シティズンシップ", "大阪市総合教育センター 研究校", ["大阪市立中之島小中一貫校"]),
        ("令和7", "ESD・グローバル・シティズンシップ", "大阪市総合教育センター 実践校", ["大阪市立美津島中学校", "大阪市立海老江東小学校", "大阪市立墨江丘中学校", "大阪市立生魂小学校"]),
        ("令和7", "ICT活用・個別最適な学び", "大阪市総合教育センター 研究校", ["大阪市立生野未来学園"]),
        ("令和7", "ICT活用・個別最適な学び", "大阪市総合教育センター 実践校", ["大阪市立春日出小学校", "大阪市立大宮中学校", "大阪市立三軒家西小学校", "大阪市立桃陽小学校"]),
        ("令和7", "理科教育", "大阪市総合教育センター 研究校", ["大阪市立長居小学校"]),
        ("令和7", "理科教育", "大阪市総合教育センター 実践校", ["大阪市立市岡小学校", "大阪市立榎本小学校", "大阪市立加賀屋東小学校", "大阪市立今川小学校"]),
        ("令和7", "不登校の未然防止・解決", "大阪市総合教育センター 研究校", ["大阪市立北稜中学校"]),
        ("令和7", "不登校の未然防止・解決", "大阪市総合教育センター 実践校", ["大阪市立瑞光中学校"]),
        # Source C: 大阪市 生成AIパイロット校（令和7年度）
        ("令和7", "生成AI活用（校務・教育）", "大阪市 生成AIパイロット校", ["大阪市立田辺中学校", "大阪市立巽南小学校", "大阪市立長原小学校"]),
    ]
    for yr, subj, desig, names in osaka_city_research:
        for sname in names:
            idxs = matcher.match(sname)
            if not idxs:
                unmatched.append(("osaka_city", sname))
                continue
            for i in idxs:
                additions[i].append({
                    "year": yr,
                    "subject": subj,
                    "designation": desig,
                    "authority": "市町村",
                })

    # Source D: 大阪市 文部科学省 リーディングDXスクール事業（令和7年度）
    for sname in ["大阪市立西淀中学校", "大阪市立姫里小学校"]:
        idxs = matcher.match(sname)
        if not idxs:
            unmatched.append(("osaka_ldx", sname))
            continue
        for i in idxs:
            additions[i].append({
                "year": "令和7",
                "subject": "教育DX・ICT活用",
                "designation": "リーディングDXスクール事業指定校",
                "authority": "文部科学省",
            })

    sc_cnt, ent_cnt, added = merge_and_save("osaka", "大阪府", schools, additions)
    note = (
        "研究指定・推進校（年度・教科等・事業名）は、大阪府教育庁（GLHS）、大阪市教育委員会・総合教育センター"
        "（令和7年度研究校・実践校、生成AIパイロット校、リーディングDXスクール）、および文部科学省・JSTの令和8年度全国公式一覧をもとに収録しています。"
    )
    update_html("osaka", "大阪府", "研究指定・推進校（令和7〜8年度）", note, ["文部科学省", "大阪府", "市町村"])
    update_js("osaka", "研究指定・推進校（令和7〜8年度）")
    print(f"[osaka] total_schools={sc_cnt}, total_entries={ent_cnt}, newly_added={added}, unmatched={len(unmatched)}")
    if unmatched:
        print("  osaka unmatched sample:", unmatched[:8])


if __name__ == "__main__":
    enrich_aichi()
    enrich_fukuoka()
    enrich_osaka()
