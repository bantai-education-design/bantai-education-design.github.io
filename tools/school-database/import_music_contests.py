#!/usr/bin/env python3
"""Parse official national music contest results (8 contests) and import into:
  1. Nationwide School Database (data/school-database/{slug}.json -> music_awards)
  2. University Database (tools/university-database/music/data/university_music_contests.json)

Contests covered:
  1. NHK全国学校音楽コンクール（Nコン） 第93回（2026年）
  2. 全日本合唱コンクール 第79回（2026年）小・中・高・大学ユース
  3. 全日本吹奏楽コンクール 第74回（2026年）中・高・大学 & 第73回（2025年）大学
  4. 全日本マーチングコンテスト 第39回（2026年出場）& 第38回（2025年金銀銅）中・高以上
  5. こども音楽コンクール 令和7年度（第73期・2026年1月全国大会）全12部門文部科学大臣賞
  6. 日本学校合奏コンクール（全国学校合奏コンクール） 2026年全国大会グランドコンテスト
  7. 全国高等学校軽音楽コンテスト 第13回（2026年）& 第12回（2025年）
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "school-database"
CACHE_DIR = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\music_contests"
)
UNIV_OUT = ROOT / "tools" / "university-database" / "music" / "data" / "university_music_contests.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_kanto_research_designations import SchoolMatcher, clean, norm_chars
from mext_national_research import PREF_SLUGS, norm_pref


def norm_award(raw: str) -> str:
    s = clean(raw).replace(" ", "")
    if s in ("金", "金賞"):
        return "金賞"
    if s in ("銀", "銀賞"):
        return "銀賞"
    if s in ("銅", "銅賞"):
        return "銅賞"
    if not s:
        return "全国大会出場"
    return s


def strip_club_suffix(name: str) -> str:
    s = clean(name).replace(" ", "")
    # Prefer full school suffixes over 学園 (so 安城学園高等学校 stays 安城学園高等学校)
    m = re.match(
        r"^(.+?(?:中学高等学校|中・高等学校|高等学校・中学校|義務教育学校|中等教育学校|特別支援学校|高等学校|高校|小学校|中学校))",
        s,
    )
    if m:
        res = m.group(1)
        res = res.replace("中学高等学校", "高等学校").replace("中・高等学校", "高等学校")
        return res
    m2 = re.match(r"^(.+?学園)", s)
    if m2:
        return m2.group(1)
    return s


def extract_rows(html_path: Path) -> list[list[str]]:
    html = html_path.read_text(encoding="utf-8")
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        cells = [
            clean(re.sub(r"<[^>]+>", "", c).replace("&nbsp;", " "))
            for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S | re.I)
        ]
        if cells:
            rows.append(cells)
    return rows


def collect_all_records() -> tuple[list[dict], list[dict]]:
    """Return (school_records, university_records)."""
    school_recs: list[dict] = []
    univ_recs: list[dict] = []

    # -----------------------------------------------------------------------
    # 1. 全日本吹奏楽コンクール (AJBA) 第74回(2026) 中・高・大学 & 第73回(2025) 大学
    # -----------------------------------------------------------------------
    for fn, div, yr in [
        ("ajba_74_jh.html", "中学校の部", "2026年（第74回）"),
        ("ajba_74_hs.html", "高等学校の部", "2026年（第74回）"),
    ]:
        for cells in extract_rows(CACHE_DIR / fn):
            if len(cells) < 6:
                continue
            # [ブロック, 出演順, 賞, 支部, 都道府県, 団体名, 時刻] or [出演順, 賞, 支部, 都道府県, 団体名, 時刻]
            if cells[0] in ("ブロック", "出演順") or "団体名" in cells:
                continue
            if len(cells) >= 6 and cells[1].isdigit():
                award, pref_raw, org = cells[2], cells[4], cells[5]
            elif cells[0].isdigit():
                award, pref_raw, org = cells[1], cells[3], cells[4]
            else:
                continue
            pref = norm_pref(pref_raw)
            if not pref:
                continue
            school_recs.append({
                "pref": pref,
                "school_name": strip_club_suffix(org),
                "raw_org": org,
                "contest": "全日本吹奏楽コンクール",
                "year": yr,
                "division": div,
                "award": norm_award(award),
                "detail": "",
            })

    for fn, yr in [
        ("ajba_74_univ.html", "2026年（第74回）"),
        ("ajba_73_univ.html", "2025年（第73回）"),
    ]:
        for cells in extract_rows(CACHE_DIR / fn):
            if len(cells) < 5 or not cells[0].isdigit():
                continue
            award, branch, pref_raw, org = cells[1], cells[2], cells[3], cells[4]
            pref = norm_pref(pref_raw)
            if not pref:
                continue
            univ_recs.append({
                "pref": pref,
                "branch": branch,
                "university_name": re.sub(r"(吹奏楽部|吹奏楽団|交響吹奏楽団|ウインドアンサンブル|シンフォニックバンド|ウィンドオーケストラ|学友会吹奏楽部|体育会.*|文化会.*)$", "", org).strip(),
                "org_name": org,
                "contest": "全日本吹奏楽コンクール",
                "year": yr,
                "division": "大学の部",
                "award": norm_award(award),
                "detail": "",
            })

    # -----------------------------------------------------------------------
    # 2. 全日本マーチングコンテスト (AJBA) 第39回(2026出場) & 第38回(2025金銀銅)
    # -----------------------------------------------------------------------
    for fn, div, yr in [
        ("ajba_39_mc_jh.html", "中学生の部", "2026年（第39回）"),
        ("ajba_39_mc_hs.html", "高等学校以上の部", "2026年（第39回）"),
        ("ajba_38_mc_jh.html", "中学生の部", "2025年（第38回）"),
        ("ajba_38_mc_hs.html", "高等学校以上の部", "2025年（第38回）"),
    ]:
        for cells in extract_rows(CACHE_DIR / fn):
            if len(cells) < 5 or not cells[0].isdigit():
                continue
            award, branch, pref_raw, org = cells[1], cells[2], cells[3], cells[4]
            pref = norm_pref(pref_raw) or norm_pref(branch)
            if not pref:
                continue
            school_recs.append({
                "pref": pref,
                "school_name": strip_club_suffix(org),
                "raw_org": org,
                "contest": "全日本マーチングコンテスト",
                "year": yr,
                "division": div,
                "award": norm_award(award),
                "detail": "",
            })

    # -----------------------------------------------------------------------
    # 3. 全日本合唱コンクール (JCA) 第79回(2026) 小・中・高・大学ユース
    # -----------------------------------------------------------------------
    for cells in extract_rows(CACHE_DIR / "jca_el.html"):
        if len(cells) < 5 or not cells[0].isdigit():
            continue
        pref = norm_pref(cells[2])
        org = cells[3]
        award = norm_award(cells[4])
        special = cells[5] if len(cells) > 5 else ""
        if not pref:
            continue
        school_recs.append({
            "pref": pref,
            "school_name": strip_club_suffix(org),
            "raw_org": org,
            "contest": "全日本合唱コンクール",
            "year": "2026年（第79回）",
            "division": "小学生部門",
            "award": award,
            "detail": special,
        })

    # jca_jhhs.html has 4 sections: 高校A, 高校B, 中学混声, 中学同声
    jca_jhhs_html = (CACHE_DIR / "jca_jhhs.html").read_text(encoding="utf-8")
    # Split by heading markers or track section
    cur_div = "高等学校部門"
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", jca_jhhs_html, re.S | re.I):
        cells = [clean(re.sub(r"<[^>]+>", "", c).replace("&nbsp;", " ")) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S | re.I)]
        if not cells:
            continue
        joined = " ".join(cells)
        if "高等学校" in joined and ("Ａグループ" in joined or "Aグループ" in joined):
            cur_div = "高等学校部門Aグループ"
            continue
        if "高等学校" in joined and ("Ｂグループ" in joined or "Bグループ" in joined):
            cur_div = "高等学校部門Bグループ"
            continue
        if "中学生" in joined and "混声" in joined:
            cur_div = "中学生部門（混声）"
            continue
        if "中学生" in joined and "同声" in joined:
            cur_div = "中学生部門（同声）"
            continue
        if len(cells) >= 5 and cells[0].isdigit():
            pref = norm_pref(cells[2])
            org = cells[3]
            award = norm_award(cells[4])
            special = cells[5] if len(cells) > 5 else ""
            if not pref:
                continue
            # Refine division from org name if generic
            div_use = cur_div
            if "中学" in org and "高等" not in org and "高等学校" in div_use:
                div_use = "中学生部門"
            elif "高等" in org and "中学" not in org and "中学生" in div_use:
                div_use = "高等学校部門"
            school_recs.append({
                "pref": pref,
                "school_name": strip_club_suffix(org),
                "raw_org": org,
                "contest": "全日本合唱コンクール",
                "year": "2026年（第79回）",
                "division": div_use,
                "award": award,
                "detail": special,
            })

    # jca_univ.html: 大学ユース合唱の部 (only university choirs)
    in_univ_sec = False
    for cells in extract_rows(CACHE_DIR / "jca_univ.html"):
        joined = " ".join(cells)
        if "大学ユース" in joined:
            in_univ_sec = True
            continue
        if in_univ_sec and ("室内合唱" in joined or "同声合唱" in joined or "混声合唱" in joined):
            in_univ_sec = False
            continue
        if in_univ_sec and len(cells) >= 4 and cells[0].isdigit():
            branch, pref_raw, org = cells[1], cells[2], cells[3]
            pref = norm_pref(pref_raw) or norm_pref(branch)
            if not pref:
                continue
            m_u = re.search(r"([一-龥ぁ-んァ-ヶ々ヶ]+大学)", org)
            univ_recs.append({
                "pref": pref,
                "branch": branch,
                "university_name": m_u.group(1) if m_u else org,
                "org_name": org,
                "contest": "全日本合唱コンクール",
                "year": "2026年（第79回）",
                "division": "大学ユース合唱の部",
                "award": "全国大会出場",
                "detail": "",
            })

    # -----------------------------------------------------------------------
    # 4. 日本学校合奏コンクール（全国学校合奏コンクール）2026年グランドコンテスト
    # -----------------------------------------------------------------------
    for cells in extract_rows(CACHE_DIR / "jsecc_2026.html"):
        if len(cells) < 3 or not cells[0].isdigit():
            continue
        org = cells[1]
        award = norm_award(cells[2])
        special = cells[3] if len(cells) > 3 else ""
        # Determine division from school name
        if "小学" in org:
            div = "小学校の部"
        elif "中学" in org and "高等" not in org:
            div = "中学校の部"
        else:
            div = "高等学校の部"
        school_recs.append({
            "pref": "",  # Will be matched across all 47 prefectures
            "school_name": strip_club_suffix(org),
            "raw_org": org,
            "contest": "日本学校合奏コンクール（全国学校合奏コンクール）",
            "year": "2026年（第15回）",
            "division": div,
            "award": award,
            "detail": special,
        })

    # -----------------------------------------------------------------------
    # 5. NHK全国学校音楽コンクール（Nコン）第93回（2026年）全国コンクール
    # -----------------------------------------------------------------------
    ncon_93 = [
        # 高等学校の部 (11校)
        ("福島県", "福島県立会津高等学校", "高等学校の部", "金賞"),
        ("千葉県", "専修大学松戸高等学校", "高等学校の部", "銀賞"),
        ("東京都", "大妻中野高等学校", "高等学校の部", "銅賞"),
        ("愛知県", "愛知県立岡崎高等学校", "高等学校の部", "銅賞"),
        ("北海道", "札幌山の手高等学校", "高等学校の部", "優良賞"),
        ("福島県", "福島県立橘高等学校", "高等学校の部", "優良賞"),
        ("神奈川県", "清泉女学院高等学校", "高等学校の部", "優良賞"),
        ("兵庫県", "兵庫県立長田高等学校", "高等学校の部", "優良賞"),
        ("岡山県", "岡山県立岡山城東高等学校", "高等学校の部", "優良賞"),
        ("香川県", "高松第一高等学校", "高等学校の部", "優良賞"),
        ("熊本県", "熊本県立第一高等学校", "高等学校の部", "優良賞"),
        # 小学校の部 (11組)
        ("東京都", "日野市立平山小学校", "小学校の部", "金賞"),
        ("東京都", "港区立白金小学校", "小学校の部", "銀賞"),
        ("岩手県", "北上市立黒沢尻北小学校", "小学校の部", "銅賞"),
        ("愛媛県", "新居浜市立角野小学校", "小学校の部", "銅賞"),
        ("北海道", "札幌市立平岡中央小学校", "小学校の部", "優良賞"),
        ("北海道", "札幌市立月寒東小学校", "小学校の部", "優良賞"),
        ("北海道", "札幌市立月寒小学校", "小学校の部", "優良賞"),
        ("岩手県", "岩手大学教育学部附属小学校", "小学校の部", "優良賞"),
        ("埼玉県", "富士見市立鶴瀬小学校", "小学校の部", "優良賞"),
        ("大阪府", "吹田市立吹田東小学校", "小学校の部", "優良賞"),
        ("広島県", "広島市立牛田小学校", "小学校の部", "優良賞"),
        ("宮崎県", "日南市立吾田小学校", "小学校の部", "優良賞"),
        # 中学校の部
        ("愛知県", "名古屋市立滝ノ水中学校", "中学校の部", "金賞"),
        ("神奈川県", "清泉女学院中学校", "中学校の部", "銀賞"),
        ("東京都", "豊島岡女子学園中学校", "中学校の部", "銅賞"),
        ("大阪府", "大阪市立文の里中学校", "中学校の部", "銅賞"),
        ("高知県", "高知学芸中学校", "中学校の部", "優良賞"),
        ("愛知県", "名古屋市立志賀中学校", "中学校の部", "優良賞"),
        ("岩手県", "北上市立上野中学校", "中学校の部", "優良賞"),
        ("岩手県", "北上市立北上中学校", "中学校の部", "優良賞"),
        ("岩手県", "北上市立北上北中学校", "中学校の部", "優良賞"),
    ]
    for pref, sname, div, award in ncon_93:
        school_recs.append({
            "pref": pref,
            "school_name": sname,
            "raw_org": sname,
            "contest": "NHK全国学校音楽コンクール（Nコン）",
            "year": "2026年（第93回）",
            "division": div,
            "award": award,
            "detail": "",
        })

    # -----------------------------------------------------------------------
    # 6. こども音楽コンクール 令和7年度（第73期・2026年1月全国大会）全12部門文部科学大臣賞
    # -----------------------------------------------------------------------
    kodomo_r7 = [
        ("長野県", "長野市立南部小学校", "小学校・重唱部門", "文部科学大臣賞"),
        ("北海道", "札幌市立幌西小学校", "小学校・合唱部門", "文部科学大臣賞"),
        ("千葉県", "習志野市立谷津小学校", "小学校・重奏部門", "文部科学大臣賞"),
        ("石川県", "金沢大学人間社会学域学校教育学類附属小学校", "小学校・合奏第1部門", "文部科学大臣賞"),
        ("千葉県", "習志野市立谷津小学校", "小学校・合奏第2部門", "文部科学大臣賞"),
        ("奈良県", "生駒市立桜ヶ丘小学校", "小学校・管楽合奏部門", "文部科学大臣賞"),
        ("千葉県", "専修大学松戸中学校", "中学校・重唱部門", "文部科学大臣賞"),
        ("東京都", "府中市立府中第四中学校", "中学校・合唱部門", "文部科学大臣賞"),
        ("千葉県", "船橋市立前原中学校", "中学校・重奏部門", "文部科学大臣賞"),
        ("大阪府", "関西創価中学校", "中学校・合奏第1部門", "文部科学大臣賞"),
        ("千葉県", "習志野市立第一中学校", "中学校・合奏第2部門", "文部科学大臣賞"),
        ("三重県", "菰野町立菰野中学校", "中学校・管楽合奏部門", "文部科学大臣賞"),
    ]
    for pref, sname, div, award in kodomo_r7:
        school_recs.append({
            "pref": pref,
            "school_name": sname,
            "raw_org": sname,
            "contest": "こども音楽コンクール",
            "year": "令和7年度（第73期）",
            "division": div,
            "award": award,
            "detail": "",
        })

    # -----------------------------------------------------------------------
    # 7. 全国高等学校軽音楽コンテスト 第13回（2026年）& 第12回（2025年）
    # -----------------------------------------------------------------------
    keion_items = [
        # 第13回 (2026) from official keion_13.html
        ("大阪府", "大阪府立北千里高等学校", "2026年（第13回）", "グランプリ"),
        ("京都府", "大谷高等学校", "2026年（第13回）", "準グランプリ"),
        ("東京都", "法政大学高等学校", "2026年（第13回）", "準グランプリ"),
        ("愛知県", "名古屋市立名東高等学校", "2026年（第13回）", "奨励賞"),
        ("兵庫県", "兵庫県立武庫荘総合高等学校", "2026年（第13回）", "奨励賞"),
        ("北海道", "北星学園大学附属高等学校", "2026年（第13回）", "奨励賞"),
        ("埼玉県", "埼玉県立所沢高等学校", "2026年（第13回）", "奨励賞"),
        # 第12回 (2025) from official zenkoku-keion.com
        ("埼玉県", "埼玉県立所沢高等学校", "2025年（第12回）", "グランプリ"),
        ("愛知県", "名古屋市立名東高等学校", "2025年（第12回）", "準グランプリ"),
        ("奈良県", "奈良育英高等学校", "2025年（第12回）", "準グランプリ"),
        ("北海道", "北海道札幌東商業高等学校", "2025年（第12回）", "奨励賞"),
        ("東京都", "東京都立桜町高等学校", "2025年（第12回）", "奨励賞"),
        ("神奈川県", "神奈川県立市ケ尾高等学校", "2025年（第12回）", "奨励賞"),
        ("滋賀県", "比叡山高等学校", "2025年（第12回）", "奨励賞"),
    ]
    for pref, sname, yr, award in keion_items:
        school_recs.append({
            "pref": pref,
            "school_name": sname,
            "raw_org": sname,
            "contest": "全国高等学校軽音楽コンテスト",
            "year": yr,
            "division": "全国大会",
            "award": award,
            "detail": "",
        })

    return school_recs, univ_recs


def main():
    school_recs, univ_recs = collect_all_records()
    print(f"Collected raw records: schools={len(school_recs)}, universities={len(univ_recs)}")
    contest_counts = Counter(r["contest"] for r in school_recs)
    print("By contest (schools):", dict(contest_counts))

    # Load all 47 prefectures
    pref_schools: dict[str, list[dict]] = {}
    pref_matchers: dict[str, SchoolMatcher] = {}
    for pref_name, slug in PREF_SLUGS.items():
        schools = json.loads((DATA_DIR / f"{slug}.json").read_text(encoding="utf-8"))
        pref_schools[slug] = schools
        pref_matchers[slug] = SchoolMatcher(schools, pref_name)

    # Match school records
    per_pref_school: dict[str, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))
    matched_cnt = 0
    unmatched = []

    for rec in school_recs:
        sname = rec["school_name"]
        div = rec["division"]
        thint = "小学校" if "小学" in div else ("中学校" if "中学" in div else ("高等学校" if "高等" in div or "高校" in div else ""))

        if rec["pref"] and rec["pref"] in PREF_SLUGS:
            slug = PREF_SLUGS[rec["pref"]]
            idxs = pref_matchers[slug].match(sname, type_hint=thint)
            # If joint school name with ・, try splitting
            if not idxs and "・" in sname:
                idxs = []
                for part in sname.split("・"):
                    idxs.extend(pref_matchers[slug].match(part.strip(), type_hint=thint))
            if idxs:
                for i in set(idxs):
                    per_pref_school[slug][i].append({
                        "contest": rec["contest"],
                        "year": rec["year"],
                        "division": rec["division"],
                        "award": rec["award"],
                        **({"detail": rec["detail"]} if rec.get("detail") else {}),
                    })
                matched_cnt += 1
            else:
                unmatched.append((rec["contest"], rec["pref"], sname))
        else:
            # Cross-prefecture match (for JSECC where prefecture is embedded in school name or unique)
            found = False
            # First check if a prefecture name is in sname
            target_slugs = []
            for pname, sl in PREF_SLUGS.items():
                if pname in sname or pname.rstrip("都府県") in sname[:4]:
                    target_slugs.append(sl)
            if not target_slugs:
                target_slugs = list(PREF_SLUGS.values())
            for sl in target_slugs:
                idxs = pref_matchers[sl].match(sname, type_hint=thint)
                if len(idxs) == 1:
                    per_pref_school[sl][idxs[0]].append({
                        "contest": rec["contest"],
                        "year": rec["year"],
                        "division": rec["division"],
                        "award": rec["award"],
                        **({"detail": rec["detail"]} if rec.get("detail") else {}),
                    })
                    found = True
                    matched_cnt += 1
                    break
            if not found:
                unmatched.append((rec["contest"], "?", sname))

    # Save updated school JSONs across all 47 prefectures
    award_order = {"文部科学大臣賞": 0, "グランプリ": 0, "最優秀賞": 0, "金賞": 1, "準グランプリ": 2, "銀賞": 2, "優秀賞": 2, "銅賞": 3, "奨励賞": 3, "優良賞": 4, "全国大会出場": 5}
    total_sc_with_music = 0
    total_music_entries = 0
    prefs_with_music = 0

    for pref_name, slug in PREF_SLUGS.items():
        schools = pref_schools[slug]
        sc_map = per_pref_school.get(slug, {})
        p_sc = 0
        p_ent = 0
        for idx, sc in enumerate(schools):
            entries = sc_map.get(idx, [])
            if not entries:
                sc.pop("music_awards", None)
                continue
            deduped = []
            seen = set()
            for e in entries:
                k = (e["contest"], e["year"], e["division"], e["award"])
                if k in seen:
                    continue
                seen.add(k)
                deduped.append(e)
            deduped.sort(key=lambda x: (award_order.get(x["award"], 9), x["contest"], x["year"]))
            sc["music_awards"] = deduped
            p_sc += 1
            p_ent += len(deduped)
        if p_sc > 0:
            prefs_with_music += 1
        total_sc_with_music += p_sc
        total_music_entries += p_ent
        out_path = DATA_DIR / f"{slug}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(schools, f, ensure_ascii=False, indent=2)
            f.write("\n")

    # Save University Music Contests JSON
    UNIV_OUT.parent.mkdir(parents=True, exist_ok=True)
    # Try linking to university-database IDs for Tokyo/Saitama/Kanagawa/Chiba
    univ_id_map = {}
    for rel in [
        "tools/university-database/tokyo/data/universities_tokyo_all.generated.json",
        "tools/university-database/saitama/data/saitama_core_01.json",
        "tools/university-database/kanagawa/data/kanagawa_core_01.json",
        "tools/university-database/chiba/data/chiba_core_01.json",
    ]:
        p = ROOT / rel
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            arr = d if isinstance(d, list) else (d.get("records") or d.get("universities") or [])
            for u in arr:
                uname = u.get("name") or u.get("university_name") or ""
                if uname and u.get("id"):
                    univ_id_map[uname.replace(" ", "")] = u["id"]

    for urec in univ_recs:
        uid = univ_id_map.get(urec["university_name"].replace(" ", ""), "")
        if uid:
            urec["university_id"] = uid

    UNIV_OUT.write_text(
        json.dumps(
            {
                "updated_at": "2026-11-23",
                "sources": [
                    "一般社団法人 全日本吹奏楽連盟 第74回（2026年）・第73回（2025年）全日本吹奏楽コンクール大学の部",
                    "一般社団法人 全日本合唱連盟 第79回（2026年）全日本合唱コンクール全国大会 大学ユース合唱の部",
                ],
                "records": univ_recs,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"MATCHED school records: {matched_cnt}/{len(school_recs)} (unmatched={len(unmatched)})")
    print(f"SAVED to 47 prefectures: {prefs_with_music}/47 prefectures, {total_sc_with_music} schools, {total_music_entries} entries")
    print(f"SAVED university music contests: {len(univ_recs)} entries -> {UNIV_OUT}")
    if unmatched:
        print("Unmatched sample (first 15):", unmatched[:15])


if __name__ == "__main__":
    main()
