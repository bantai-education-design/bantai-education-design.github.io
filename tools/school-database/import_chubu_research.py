#!/usr/bin/env python3
"""Import FY2026 official research-designated schools for Chubu (9 prefectures):
  niigata, toyama, ishikawa, fukui, yamanashi, nagano, gifu, shizuoka, aichi
Combines:
  - MEXT FY2026 national official lists (DX High School, Sakidori Research School, JST SSH all active)
  - Ishikawa BOE FY2026 特色ある学校・研究推進校等の紹介 (tokusyoku.pdf, 23 pages)
  - Nagano BOE FY2026 「学びの改革支援課研究校」支援事業 (kenkyu2026.html)
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
MEXT_CACHE = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\national_and_tohoku\mext_r8_national_parsed.json"
)
CHUBU_CACHE = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\chubu_research"
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_kanto_research_designations import SchoolMatcher, clean, save_designations

TARGET_PREFS = [
    ("niigata", "新潟県"),
    ("toyama", "富山県"),
    ("ishikawa", "石川県"),
    ("fukui", "福井県"),
    ("yamanashi", "山梨県"),
    ("nagano", "長野県"),
    ("gifu", "岐阜県"),
    ("shizuoka", "静岡県"),
    ("aichi", "愛知県"),
]


def add_ishikawa_extra(matcher: SchoolMatcher, per_school: dict[int, list[dict]], unmatched: list):
    pdf_path = CHUBU_CACHE / "ishikawa_r8.pdf"
    if not pdf_path.exists():
        return
    with pdfplumber.open(pdf_path) as pdf:
        cur_domain = ""
        for page in pdf.pages[2:]:
            for t in page.extract_tables():
                cur_theme = ""
                for row in t:
                    if not row or len(row) < 2:
                        continue
                    c0 = clean(row[0]).replace(" ", "")
                    c1 = clean(row[1])
                    c2 = clean(row[2]) if len(row) > 2 else ""
                    if c0 == "領域名" or "研究主題" in c1:
                        continue
                    if c0:
                        cur_domain = c0
                    # Check if c1 contains a school name
                    m_sc = re.search(
                        r"((?:石川県立|金沢大学人間社会学域学校教育学類附属|[^\s・]+(?:市立|町立))[^\s(（]+(?:小学校|中学校|義務教育学校|高等学校|特別支援学校|幼稚園|こども園))",
                        c1.replace(" ", ""),
                    )
                    if m_sc:
                        sname = m_sc.group(1)
                        auth = "文部科学省" if ("文部科学省" in c2 or "国指定" in c2 or "国委託" in c2) else ("市町村" if ("市指定" in c2 or "町指定" in c2) else "石川県")
                        m_yr = re.search(r"(R\d+(?:[～〜-]\d+)?|令和\d+(?:[～〜-]\d+)?)", c2)
                        yr = m_yr.group(1).replace("R", "令和").replace("~", "〜").replace("～", "〜") if m_yr else "令和8"
                        m_pres = re.search(r"発表日[:：]?\s*([^\s]+)", c2)
                        pres = m_pres.group(1) if m_pres else ""
                        desig = cur_theme[:60] + ("…" if len(cur_theme) > 60 else "") if cur_theme else "特色ある学校・研究推進校"
                        idxs = matcher.match(sname)
                        if not idxs:
                            unmatched.append(("ishikawa_boe", sname))
                            continue
                        entry = {
                            "year": yr,
                            "subject": cur_domain,
                            "designation": desig,
                            "authority": auth,
                        }
                        if pres and pres not in ("未定", "なし"):
                            entry["presentation"] = pres
                        for i in idxs:
                            per_school[i].append(entry)
                    elif c1:
                        cur_theme = c1


def add_nagano_extra(matcher: SchoolMatcher, per_school: dict[int, list[dict]], unmatched: list):
    # From nagano_r8.html (令和8年度 「学びの改革支援課研究校」支援事業)
    items = [
        ("青木村", ["青木中学校", "青木小学校"]),
        ("泰阜村", ["泰阜中学校", "泰阜小学校"]),
        ("天龍村", ["天龍中学校", "天龍小学校"]),
        ("上松町", ["上松中学校", "上松小学校"]),
        ("松本市", ["丸ノ内中学校", "開智小学校", "田川小学校"]),
        ("坂城町", ["坂城中学校"]),
        ("佐久市", ["臼田中学校"]),
        ("諏訪市", ["城南小学校"]),
        ("木曽町", ["福島小学校"]),
        ("池田町", ["池田小学校"]),
        ("白馬村", ["白馬南小学校"]),
        ("小布施町", ["栗ガ丘小学校", "小布施中学校"]),
        ("須坂市", ["仁礼小学校", "東中学校"]),
        ("上田市", ["浦里小学校", "川西小学校"]),
        ("山ノ内町", ["南小学校", "東小学校", "西小学校"]),
    ]
    for muni, names in items:
        for sname in names:
            idxs = matcher.match(sname, muni_hint=muni)
            if not idxs:
                unmatched.append(("nagano_boe", f"{muni}:{sname}"))
                continue
            for i in idxs:
                per_school[i].append({
                    "year": "令和8",
                    "subject": "授業改善・学びの改革",
                    "designation": "学びの改革支援課研究校",
                    "authority": "長野県",
                })


def main():
    mext_data = json.loads(MEXT_CACHE.read_text(encoding="utf-8"))
    total_sc = 0
    total_ent = 0
    for slug, pref_name in TARGET_PREFS:
        schools = json.loads((DATA_DIR / f"{slug}.json").read_text(encoding="utf-8"))
        matcher = SchoolMatcher(schools, pref_name)
        per_school: dict[int, list[dict]] = defaultdict(list)
        unmatched = []

        for rec in mext_data.get(slug, []):
            idxs = matcher.match(rec["school_name"], muni_hint=rec.get("muni_hint", ""))
            if not idxs:
                unmatched.append(("MEXT", rec["school_name"]))
                continue
            for i in idxs:
                per_school[i].append({
                    "year": rec["year"],
                    "subject": rec["subject"],
                    "designation": rec["designation"],
                    "authority": rec["authority"],
                })

        if slug == "ishikawa":
            add_ishikawa_extra(matcher, per_school, unmatched)
        elif slug == "nagano":
            add_nagano_extra(matcher, per_school, unmatched)

        sc_cnt, ent_cnt = save_designations(slug, schools, per_school, pref_name)
        total_sc += sc_cnt
        total_ent += ent_cnt
        print(f"[{slug}] schools={sc_cnt}, entries={ent_cnt}, unmatched={len(unmatched)}")
    print(f"CHUBU TOTAL: schools={total_sc}, entries={total_ent}")


if __name__ == "__main__":
    main()
