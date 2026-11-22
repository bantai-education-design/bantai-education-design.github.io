#!/usr/bin/env python3
"""Import FY2026 official research-designated schools for Hokkaido & Tohoku (7 prefectures):
  hokkaido, aomori, iwate, miyagi, akita, yamagata, fukushima
Combines:
  - MEXT FY2026 national official lists (DX High School, Sakidori Research School, SSH R8)
  - Hokkaido BOE FY2026 designated school list (令和8年6月現在)
  - Akita BOE FY2026 designated school list (令和8年6月19日現在)
  - Iwate Morioka Education Office FY2026 designated school list (盛岡教育事務所管内)
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "school-database"
CACHE_DIR = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\national_and_tohoku"
)
MEXT_CACHE = CACHE_DIR / "mext_r8_national_parsed.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_kanto_research_designations import SchoolMatcher, clean, norm_chars, save_designations

TARGET_PREFS = [
    ("hokkaido", "北海道"),
    ("aomori", "青森県"),
    ("iwate", "岩手県"),
    ("miyagi", "宮城県"),
    ("akita", "秋田県"),
    ("yamagata", "山形県"),
    ("fukushima", "福島県"),
]


def add_hokkaido_extra(matcher: SchoolMatcher, per_school: dict[int, list[dict]], unmatched: list):
    # From hokkaido_r8.pdf (令和8年6月現在 北海道教育委員会研究指定校一覧)
    items = [
        ("令和8〜10", "医進・地域医療", "地域医療を支える人づくりプロジェクト事業（医進類型指定校）",
         ["岩見沢東", "小樽潮陵", "室蘭栄", "苫小牧東", "函館中部", "旭川東", "北見北斗", "帯広柏葉", "釧路湖陵"]),
        ("令和8", "キャリア・就職指導", "就職指導の改善に関する研究（実践研究校）",
         ["野幌", "松前", "富良野", "北見緑陵", "幕別清陵", "釧路湖陵"]),
        ("令和8", "地域連携・総合学科等", "小規模総合学科等による地域と連携・協働した高校魅力化推進事業",
         ["美唄尚栄", "余市紅志", "浦河", "森", "斜里", "清水", "池田", "標茶", "登別青嶺", "江差", "北見緑陵", "音更", "鵡川", "鹿追", "広尾"]),
        ("令和8", "定時制・通信制", "北海道高等学校定時制・通信制パワーアップ事業（研究推進校）",
         ["札幌琴似工業", "苫小牧工業", "有朋"]),
    ]
    for yr, subj, desig, names in items:
        for short in names:
            idxs = matcher.match(f"北海道{short}高等学校", type_hint="高等学校")
            if not idxs:
                idxs = matcher.match(f"{short}高等学校", type_hint="高等学校")
            if not idxs:
                unmatched.append(("hokkaido_boe", short))
                continue
            for i in idxs:
                per_school[i].append({
                    "year": yr,
                    "subject": subj,
                    "designation": desig,
                    "authority": "北海道",
                })


def add_akita_extra(matcher: SchoolMatcher, per_school: dict[int, list[dict]], unmatched: list):
    # From akita_r8.pdf p.1 (令和8年6月19日現在 研究指定校・研究委嘱校等一覧)
    items = [
        ("令和8", "道徳教育", "よりよい生き方を実践する力を育む道徳教育の推進事業", "文部科学省",
         [("由利本荘市", "由利小学校"), ("由利本荘市", "由利中学校"), ("", "由利工業高等学校")]),
        ("令和8", "中学校 数学", "教育課程実践検証協力校事業", "文部科学省",
         [("湯沢市", "湯沢南中学校")]),
        ("令和8", "ICT活用", "ICTを活用した授業力向上事業", "秋田県",
         [("三種町", "三種中学校")]),
        ("令和5〜9", "理数・科学技術", "スーパーサイエンスハイスクール（SSH）", "文部科学省",
         [("", "秋田中央高等学校")]),
        ("令和6〜10", "理数・科学技術", "スーパーサイエンスハイスクール（SSH）", "文部科学省",
         [("", "横手高等学校")]),
        ("令和8", "学校安全", "学校安全総合支援事業（地域連携安全・安心推進事業）", "文部科学省",
         [("五城目町", "五城目小学校"), ("五城目町", "五城目第一中学校"), ("", "五城目高等学校")]),
        ("令和8", "学校安全・通学路", "学校安全総合支援事業（通学路安全推進事業）", "文部科学省",
         [("にかほ市", "金浦小学校"), ("にかほ市", "金浦中学校"), ("", "仁賀保高等学校")]),
    ]
    for yr, subj, desig, auth, targets in items:
        for muni, sname in targets:
            idxs = matcher.match(sname, muni_hint=muni)
            if not idxs:
                unmatched.append(("akita_boe", sname))
                continue
            for i in idxs:
                per_school[i].append({
                    "year": yr,
                    "subject": subj,
                    "designation": desig,
                    "authority": auth,
                })


def add_iwate_morioka_extra(matcher: SchoolMatcher, per_school: dict[int, list[dict]], unmatched: list):
    # From iwate_morioka_shitei.pdf (盛岡教育事務所 小・中学校「研究指定校等」一覧)
    items = [
        ("盛岡市", "上田小学校", "市町村", "令和7〜9", "国語"),
        ("盛岡市", "向中野小学校", "市町村", "令和6〜8", "国語・算数"),
        ("盛岡市", "仙北中学校", "市町村", "令和8〜9", "教育課程一般（学力向上）"),
        ("盛岡市", "黒石野中学校", "市町村", "令和8", "教育課程一般（学力向上）"),
        ("盛岡市", "城東中学校", "市町村", "令和6〜8", "教育課程一般（学力向上）"),
        ("盛岡市", "見前小学校", "市町村", "令和7〜9", "小中一貫教育"),
        ("盛岡市", "津志田小学校", "市町村", "令和7〜9", "小中一貫教育"),
        ("盛岡市", "見前中学校", "市町村", "令和7〜9", "小中一貫教育"),
        ("盛岡市", "飯岡小学校", "市町村", "令和8〜10", "小中一貫教育"),
        ("盛岡市", "羽場小学校", "市町村", "令和8〜10", "小中一貫教育"),
        ("盛岡市", "飯岡中学校", "市町村", "令和8〜10", "小中一貫教育"),
        ("八幡平市", "西根中学校", "市町村", "令和7〜8", "教科等"),
        ("八幡平市", "田頭小学校", "市町村", "令和8〜9", "算数"),
        ("八幡平市", "平笠小学校", "市町村", "令和8〜9", "国語"),
        ("八幡平市", "安代中学校", "市町村", "令和8〜9", "道徳"),
        ("滝沢市", "篠木小学校", "市町村", "令和8〜10", "研究指定校"),
        ("滝沢市", "鵜飼小学校", "市町村", "令和8〜10", "研究指定校"),
        ("滝沢市", "滝沢南中学校", "市町村", "令和8〜10", "研究指定校"),
        ("雫石町", "七ツ森小学校", "市町村", "令和7〜8", "教科一般"),
        ("雫石町", "西山小学校", "市町村", "令和8〜9", "教科一般"),
        ("葛巻町", "江刈中学校", "市町村", "令和7〜9", "全教科・特別支援"),
        ("葛巻町", "五日市小学校", "市町村", "令和8〜10", "全教科・特別支援"),
        ("岩手町", "沼宮内中学校", "市町村", "令和7〜8", "全教科"),
        ("岩手町", "沼宮内小学校", "市町村", "令和8〜9", "全教科"),
        ("紫波町", "紫波第一中学校", "市町村", "令和7〜8", "全教科・特別支援"),
        ("紫波町", "古館小学校", "市町村", "令和8〜9", "サキドリ研究事業"),
        ("矢巾町", "不動小学校", "市町村", "令和8", "授業実践研修会実施校"),
        ("矢巾町", "矢巾北中学校", "市町村", "令和8", "授業実践研修会実施校"),
    ]
    for muni, sname, auth, yr, subj in items:
        idxs = matcher.match(sname, muni_hint=muni)
        if not idxs:
            unmatched.append(("iwate_morioka", f"{muni}:{sname}"))
            continue
        for i in idxs:
            per_school[i].append({
                "year": yr,
                "subject": subj,
                "designation": "研究指定校等（盛岡教育事務所管内）",
                "authority": auth,
            })


def main():
    mext_data = json.loads(MEXT_CACHE.read_text(encoding="utf-8"))

    for slug, pref_name in TARGET_PREFS:
        schools = json.loads((DATA_DIR / f"{slug}.json").read_text(encoding="utf-8"))
        matcher = SchoolMatcher(schools, pref_name)
        per_school: dict[int, list[dict]] = defaultdict(list)
        unmatched = []

        # 1. MEXT national FY2026
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

        # 2. Prefecture-specific official lists
        if slug == "hokkaido":
            add_hokkaido_extra(matcher, per_school, unmatched)
        elif slug == "akita":
            add_akita_extra(matcher, per_school, unmatched)
        elif slug == "iwate":
            add_iwate_morioka_extra(matcher, per_school, unmatched)

        sc_cnt, ent_cnt = save_designations(slug, schools, per_school, pref_name)
        print(f"[{slug}] schools={sc_cnt}, entries={ent_cnt}, unmatched={len(unmatched)}")
        if unmatched:
            print(f"  {slug} unmatched sample:", unmatched[:8])


if __name__ == "__main__":
    main()
