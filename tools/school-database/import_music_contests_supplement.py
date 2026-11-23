#!/usr/bin/env python3
"""Supplement missing 2025 and 2026 official national music contest results into Nationwide School DB.

Sources merged:
  1. 全日本マーチングコンテスト 第38回(2025年) 中学生の部(32団体)・高等学校以上の部(36団体) (AJBA official)
  2. 全国高等学校軽音楽コンテスト 第12回(2025年) グランプリ・準グランプリ・奨励賞(7校) (zenkoku-keion.com official)
  3. 日本学校合奏コンクール（全国学校合奏コンクール） 第15回(2026年) グランドコンテスト全3部門(67団体) (jseccfks.jp official)
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from html import unescape
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "school-database"
PAST_DIR = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\music_contests_past"
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_kanto_research_designations import SchoolMatcher, clean
from mext_national_research import PREF_SLUGS
from import_music_contests import strip_club_suffix

# 1. 第38回全日本マーチングコンテスト（2025年11月22日・23日 大阪城ホール）AJBA公式結果
MARCHING_2025_JH = [
    ("大分県", "大分市立滝尾中学校", "銅賞"),
    ("大阪府", "大阪市立堀江中学校", "金賞"),
    ("広島県", "広島市立安佐中学校", "金賞"),
    ("大阪府", "大阪市立蒲生中学校", "金賞"),
    ("福島県", "田村市立船引中学校", "銅賞"),
    ("千葉県", "船橋市立法田中学校", "金賞"),
    ("愛知県", "愛西マーチングバンド BLOWING Jr.", "銅賞"),
    ("千葉県", "野田市立南部中学校", "銀賞"),
    ("長崎県", "雲仙市立小浜中学校", "金賞"),
    ("山口県", "山口市立小郡中学校", "銀賞"),
    ("富山県", "砺波市立庄西中学校", "金賞"),
    ("東京都", "足立区立第十四中学校", "金賞"),
    ("高知県", "高知学芸中学校", "銀賞"),
    ("埼玉県", "栗橋ジュニアマーチングバンド Scarlet", "銅賞"),
    ("北海道", "遠軽町立遠軽中学校", "銅賞"),
    ("京都府", "京都市立近衛中学校", "銀賞"),
    ("広島県", "広島市立翠町中学校", "銀賞"),
    ("福岡県", "北九州市立高須中学校", "金賞"),
    ("東京都", "板橋区立赤塚第三中学校", "金賞"),
    ("長野県", "佐久市立浅間中学校", "銅賞"),
    ("鹿児島県", "薩摩川内市立川内北中学校", "銀賞"),
    ("兵庫県", "西宮市立上甲子園中学校", "金賞"),
    ("大阪府", "豊中市立第十三中学校", "金賞"),
    ("愛知県", "名古屋市立大高中学校", "銀賞"),
    ("京都府", "宇治市立東宇治中学校", "金賞"),
    ("群馬県", "高崎市立塚沢中学校", "銀賞"),
    ("千葉県", "習志野市立第二中学校", "金賞"),
    ("宮城県", "仙台市立広瀬中学校", "銅賞"),
    ("千葉県", "習志野市立第四中学校", "金賞"),
    ("長崎県", "長崎市立戸町中学校", "銀賞"),
    ("高知県", "香美市立鏡野中学校", "銅賞"),
    ("群馬県", "高崎市立箕郷中学校", "銅賞"),
]

MARCHING_2025_HS = [
    ("熊本県", "熊本県立熊本工業高等学校", "金賞"),
    ("三重県", "三重県立白子高等学校", "銅賞"),
    ("島根県", "島根県立出雲商業高等学校", "銅賞"),
    ("長崎県", "活水高等学校", "金賞"),
    ("京都府", "京都両洋高等学校", "金賞"),
    ("東京都", "八王子学園八王子高等学校", "金賞"),
    ("宮城県", "聖ウルスラ学院英智高等学校", "銅賞"),
    ("高知県", "土佐女子高等学校", "銅賞"),
    ("埼玉県", "叡明高等学校", "銀賞"),
    ("千葉県", "船橋市立船橋高等学校", "銀賞"),
    ("静岡県", "浜松修学舎高等学校", "銅賞"),
    ("埼玉県", "埼玉県立伊奈学園総合高等学校", "金賞"),
    ("大阪府", "早稲田大阪高等学校", "銀賞"),
    ("千葉県", "千葉県立松戸六実高等学校", "銅賞"),
    ("愛知県", "豊川高等学校", "銅賞"),
    ("大阪府", "箕面自由学園高等学校", "金賞"),
    ("島根県", "出雲北陵高等学校", "銀賞"),
    ("鹿児島県", "神村学園高等部", "金賞"),
    ("福岡県", "精華女子高等学校", "金賞"),
    ("群馬県", "東京農業大学第二高等学校", "銀賞"),
    ("広島県", "広島翔洋高等学校", "銅賞"),
    ("石川県", "金沢学院大学附属高等学校", "銀賞"),
    ("高知県", "高知学芸高等学校", "銅賞"),
    ("熊本県", "玉名女子高等学校", "金賞"),
    ("香川県", "高松中央高等学校", "銅賞"),
    ("島根県", "島根県立松江商業高等学校", "銅賞"),
    ("千葉県", "柏市立柏高等学校", "金賞"),
    ("北海道", "北海道遠軽高等学校", "銅賞"),
    ("兵庫県", "滝川第二高等学校", "金賞"),
    ("京都府", "京都橘高等学校", "金賞"),
    ("愛知県", "安城学園高等学校", "銅賞"),
    ("愛知県", "愛知工業大学名電高等学校", "銀賞"),
    ("千葉県", "習志野市立習志野高等学校", "金賞"),
    ("福岡県", "九州産業大学付属九州産業高等学校", "銀賞"),
    ("東京都", "東海大学付属高輪台高等学校", "金賞"),
    ("宮城県", "宮城県多賀城高等学校", "銅賞"),
]

# 2. 第12回全国高等学校軽音楽コンテスト（2025年8月19日・20日）公式結果
KEION_2025 = [
    ("埼玉県", "埼玉県立所沢高等学校", "グランプリ", "YagiRi「脱兎」"),
    ("愛知県", "名古屋市立名東高等学校", "準グランプリ", "偶然のうたげ「わたしたちのつみとは」"),
    ("奈良県", "奈良育英高等学校", "準グランプリ", "Mädchen「鬼灯」"),
    ("北海道", "北海道札幌東商業高等学校", "奨励賞", "Berry Pickin'「余光」"),
    ("東京都", "東京都立桜町高等学校", "奨励賞", "MUSIQA「PIpE DREAM」"),
    ("神奈川県", "神奈川県立市ケ尾高等学校", "奨励賞", "404「それだけ」"),
    ("滋賀県", "比叡山高等学校", "奨励賞", "詠人不知「微熱」"),
]


def parse_jsecc_2026(html_path: Path) -> list[dict]:
    txt = html_path.read_text(encoding="utf-8", errors="ignore")
    tables = re.findall(r"<table[^>]*>(.*?)</table>", txt, re.S)
    divisions = ["高等学校の部", "小学校の部", "中学校の部"]
    recs: list[dict] = []

    for idx, tbl in enumerate(tables[:3]):
        div = divisions[idx]
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, re.S)
        for r in rows[1:]:
            cells = [
                clean(unescape(re.sub(r"<[^>]+>", "", c)))
                for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)
            ]
            if len(cells) < 3:
                continue
            org = cells[1]
            award = cells[2]
            special = cells[3] if len(cells) > 3 else ""
            if not org or not award:
                continue
            final_award = "文部科学大臣賞" if "文部科学大臣賞" in special else award
            detail = special if special and special != final_award else ""
            sname = strip_club_suffix(org)
            # Clean trailing ensemble labels
            sname = re.sub(
                r"(?:筝曲部|箏曲部|オーケストラ部|管弦楽団|管弦楽部|弦楽合奏部|弦楽部|ギター・マンドリン部|マンドリン部|合奏部|器楽部|音楽部|吹奏楽部|コーラス・ハンドベル部|ハンドベル部|日本音楽部)$",
                "",
                sname,
            ).strip()
            recs.append({
                "pref": "",
                "school_name": sname,
                "raw_org": org,
                "contest": "日本学校合奏コンクール（全国学校合奏コンクール）",
                "year": "2026年（第15回）",
                "division": div,
                "award": final_award,
                "detail": detail,
            })
    return recs


def collect_records() -> list[dict]:
    recs: list[dict] = []
    for pref, sname, award in MARCHING_2025_JH:
        recs.append({
            "pref": pref,
            "school_name": sname,
            "contest": "全日本マーチングコンテスト",
            "year": "2025年（第38回）",
            "division": "中学生の部",
            "award": award,
            "detail": "",
        })
    for pref, sname, award in MARCHING_2025_HS:
        recs.append({
            "pref": pref,
            "school_name": sname,
            "contest": "全日本マーチングコンテスト",
            "year": "2025年（第38回）",
            "division": "高等学校以上の部",
            "award": award,
            "detail": "",
        })
    for pref, sname, award, detail in KEION_2025:
        recs.append({
            "pref": pref,
            "school_name": sname,
            "contest": "全国高等学校軽音楽コンテスト",
            "year": "2025年（第12回）",
            "division": "全国大会",
            "award": award,
            "detail": detail,
        })
    jsecc_path = PAST_DIR / "jsecc_2026_gc.html"
    if jsecc_path.exists():
        recs.extend(parse_jsecc_2026(jsecc_path))
    return recs


def main() -> None:
    recs = collect_records()
    print(f"Collected {len(recs)} supplement records")

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

    NAME_ALIASES = {
        "大阪信愛学院中高等学校": ("大阪府", "大阪信愛学院高等学校"),
        "横浜創英中学・高等学校": ("神奈川県", "横浜創英高等学校"),
        "明治大学付属中野中学・高等学校": ("東京都", "明治大学付属中野高等学校"),
        "北海道遠軽高等学校": ("北海道", "遠軽高等学校"),
        "北海道札幌東商業高等学校": ("北海道", "札幌東商業高等学校"),
        "福島大学附属中学校": ("福島県", "福島大学人間発達文化学類附属中学校"),
    }

    for rec in recs:
        pref = rec.get("pref", "")
        sname = rec["school_name"]
        if sname in NAME_ALIASES:
            pref, sname = NAME_ALIASES[sname]
        entry = {
            "contest": rec["contest"],
            "year": rec["year"],
            "division": rec["division"],
            "award": rec["award"],
            **({"detail": rec["detail"]} if rec.get("detail") else {}),
        }

        if pref and pref in PREF_SLUGS:
            slug = PREF_SLUGS[pref]
            idxs = matchers[slug].match(sname)
            if idxs:
                additions[slug][idxs[0]].append(entry)
                matched_cnt += 1
            else:
                unmatched.append((rec["contest"], pref, sname))
        else:
            found = False
            # Try prefecture hint in school name first
            for pref_name, slug in PREF_SLUGS.items():
                if pref_name in sname or pref_name[:-1] in sname[:4]:
                    idxs = matchers[slug].match(sname)
                    if idxs:
                        additions[slug][idxs[0]].append(entry)
                        matched_cnt += 1
                        found = True
                        break
            if not found:
                for pref_name, slug in PREF_SLUGS.items():
                    idxs = matchers[slug].match(sname)
                    if idxs:
                        additions[slug][idxs[0]].append(entry)
                        matched_cnt += 1
                        found = True
                        break
            if not found:
                unmatched.append((rec["contest"], "?", sname))

    award_order = {
        "文部科学大臣賞": 0,
        "グランプリ": 0,
        "最優秀賞": 0,
        "金賞": 1,
        "準グランプリ": 2,
        "銀賞": 2,
        "優秀賞": 2,
        "銅賞": 3,
        "奨励賞": 3,
        "優良賞": 4,
        "全国大会出場": 5,
    }

    total_sc = 0
    total_ent = 0
    prefs_with_music = 0
    newly_added_ent = 0

    for pref_name, slug in PREF_SLUGS.items():
        schools = pref_schools[slug]
        sc_add = additions.get(slug, {})
        p_sc = 0
        changed = False
        for idx, sc in enumerate(schools):
            existing = list(sc.get("music_awards") or [])
            new_items = sc_add.get(idx, [])
            combined = existing + new_items
            if not combined:
                continue
            deduped = []
            seen = set()
            for e in combined:
                k = (e["contest"], e["year"], e["division"], e["award"])
                if k in seen:
                    continue
                seen.add(k)
                deduped.append(e)
            delta = max(0, len(deduped) - len(existing))
            if delta > 0:
                changed = True
                newly_added_ent += delta
            deduped.sort(
                key=lambda x: (
                    -int(re.search(r"20\d{2}", x["year"]).group(0)) if re.search(r"20\d{2}", x["year"]) else -2025,
                    award_order.get(x["award"], 9),
                    x["contest"],
                )
            )
            sc["music_awards"] = deduped
            p_sc += 1
            total_sc += 1
            total_ent += len(deduped)
        if p_sc > 0:
            prefs_with_music += 1
        if changed:
            out_path = DATA_DIR / f"{slug}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(schools, f, ensure_ascii=False, indent=2)
                f.write("\n")

    print(f"MATCHED supplement records: {matched_cnt}/{len(recs)} (unmatched={len(unmatched)})")
    print(
        f"TOTAL school DB (2024-2026): {prefs_with_music}/47 prefectures, "
        f"{total_sc} schools, {total_ent} entries (+{newly_added_ent} new)"
    )
    if unmatched:
        print("Unmatched:", unmatched)


if __name__ == "__main__":
    main()
