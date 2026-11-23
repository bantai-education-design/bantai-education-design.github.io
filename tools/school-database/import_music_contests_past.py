#!/usr/bin/env python3
"""Merge FY2024 and FY2025 official national music contest results onto existing FY2026 data
across all 47 prefectures in Nationwide School DB and University DB.

Sources merged:
  1. 全日本吹奏楽コンクール 第73回(2025)・第72回(2024) 中学・高校・大学 (AJBA official)
  2. 全日本マーチングコンテスト 第37回(2024) 中学・高校以上 (AJBA official)
  3. 全日本合唱コンクール 第78回(2025)・第77回(2024) 小・中・高・大学ユース (JCA official con78/con77)
  4. 日本学校合奏コンクール（全国学校合奏コンクール） 2024年(第13回)全国大会グランドコンテスト + 2025年最優秀(幕張総合)
  5. NHK全国学校音楽コンクール（Nコン） 第92回(2025)・第91回(2024) 小・中・高 金銀銅
  6. こども音楽コンクール 令和6年度(第72期・2025年1月全国大会) 全12部門文部科学大臣賞
  7. 全国高等学校軽音楽コンテスト 第11回(2024) グランプリ・準グランプリ・奨励賞
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "school-database"
PAST_DIR = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\music_contests_past"
)
UNIV_OUT = ROOT / "tools" / "university-database" / "music" / "data" / "university_music_contests.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_kanto_research_designations import SchoolMatcher, clean
from mext_national_research import PREF_SLUGS, norm_pref
from import_music_contests import extract_rows, norm_award, strip_club_suffix


def parse_jca_kako(html_path: Path, year_label: str) -> tuple[list[dict], list[dict]]:
    html = html_path.read_text(encoding="utf-8")
    txt = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.S | re.I)
    txt = re.sub(r"<style[^>]*>.*?</style>", "", txt, flags=re.S | re.I)
    txt = txt.replace("&nbsp;", " ")
    txt = re.sub(r"<[^>]+>", "\n", txt)

    school_recs: list[dict] = []
    univ_recs: list[dict] = []

    cur_div = ""
    cur_award = ""
    in_general = False  # Stop before 室内合唱/同声合唱/混声合唱 of 一般部門

    for raw_line in txt.splitlines():
        line = clean(raw_line)
        if not line:
            continue
        # Detect section headings
        if "高等学校部門" in line and ("Aグループ" in line or "Ａグループ" in line):
            cur_div = "高等学校部門Aグループ"
            cur_award = ""
            in_general = False
            continue
        if "高等学校部門" in line and ("Bグループ" in line or "Ｂグループ" in line):
            cur_div = "高等学校部門Bグループ"
            cur_award = ""
            in_general = False
            continue
        if ("中学校部門" in line or "中学生部門" in line) and "混声" in line:
            cur_div = "中学生部門（混声）"
            cur_award = ""
            in_general = False
            continue
        if ("中学校部門" in line or "中学生部門" in line) and "同声" in line:
            cur_div = "中学生部門（同声）"
            cur_award = ""
            in_general = False
            continue
        if "小学校部門" in line or "小学生部門" in line:
            if "＜" in line or "部門" in line:
                cur_div = "小学生部門"
                cur_award = ""
                in_general = False
                continue
        if "大学ユース" in line and ("＜" in line or "<" in line or "の部" in line) and "開演" not in line and "日程" not in line:
            cur_div = "大学ユース合唱の部"
            cur_award = ""
            in_general = False
            continue
        if any(k in line for k in ("室内合唱", "同声合唱の部", "混声合唱の部")) and "中学" not in line and "開演" not in line:
            in_general = True
            cur_award = ""
            continue

        if in_general or not cur_div:
            continue

        # Detect award prefix
        for aw in ("金賞", "銀賞", "銅賞"):
            if line.startswith(aw):
                cur_award = aw
                line = line[len(aw) :].strip()
                break

        if not cur_award or not line:
            continue

        # Match org(都道府県)
        m = re.search(r"(.+?)[（(]([^）)]+(?:都|道|府|県))[）)]", line)
        if not m:
            continue
        org = clean(m.group(1))
        pref = norm_pref(m.group(2))
        if not pref or not org:
            continue

        if cur_div == "大学ユース合唱の部":
            m_u = re.search(r"([一-龥ぁ-んァ-ヶ々ヶ]+(?:大学|学院))", org)
            univ_recs.append({
                "pref": pref,
                "branch": "",
                "university_name": m_u.group(1) if m_u else org,
                "org_name": org,
                "contest": "全日本合唱コンクール",
                "year": year_label,
                "division": "大学ユース合唱の部",
                "award": cur_award,
                "detail": "",
            })
        else:
            school_recs.append({
                "pref": pref,
                "school_name": strip_club_suffix(org),
                "raw_org": org,
                "contest": "全日本合唱コンクール",
                "year": year_label,
                "division": cur_div,
                "award": cur_award,
                "detail": "",
            })

    return school_recs, univ_recs


def collect_past_records() -> tuple[list[dict], list[dict]]:
    school_recs: list[dict] = []
    univ_recs: list[dict] = []

    # 1. AJBA 全日本吹奏楽コンクール 2025(第73回) 中・高 & 2024(第72回) 中・高・大学
    for fn, div, yr in [
        ("ajba_73_jh.html", "中学校の部", "2025年（第73回）"),
        ("ajba_73_hs.html", "高等学校の部", "2025年（第73回）"),
        ("ajba_72_jh.html", "中学校の部", "2024年（第72回）"),
        ("ajba_72_hs.html", "高等学校の部", "2024年（第72回）"),
    ]:
        for cells in extract_rows(PAST_DIR / fn):
            if len(cells) < 5 or "団体名" in cells:
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

    # 2024(第72回) 大学
    for cells in extract_rows(PAST_DIR / "ajba_72_univ.html"):
        if len(cells) < 4 or "団体名" in cells:
            continue
        if len(cells) >= 5 and cells[0].isdigit():
            award, branch, pref_raw, org = cells[1], cells[2], cells[3], cells[4]
        elif len(cells) >= 6 and cells[1].isdigit():
            award, branch, pref_raw, org = cells[2], cells[3], cells[4], cells[5]
        else:
            continue
        pref = norm_pref(pref_raw)
        if not pref:
            continue
        univ_recs.append({
            "pref": pref,
            "branch": branch,
            "university_name": re.sub(r"(吹奏楽部|吹奏楽団|交響吹奏楽団|ウインドアンサンブル|シンフォニックバンド|ウィンドオーケストラ|学友会吹奏楽部|体育会.*|文化会.*)$", "", org).strip(),
            "org_name": org,
            "contest": "全日本吹奏楽コンクール",
            "year": "2024年（第72回）",
            "division": "大学の部",
            "award": norm_award(award),
            "detail": "",
        })

    # 2. AJBA 全日本マーチングコンテスト 2024(第37回) 中・高以上
    for fn, div, yr in [
        ("ajba_37_mc_jh.html", "中学生の部", "2024年（第37回）"),
        ("ajba_37_mc_hs.html", "高等学校以上の部", "2024年（第37回）"),
    ]:
        for cells in extract_rows(PAST_DIR / fn):
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

    # 3. JCA 全日本合唱コンクール 第78回(2025) & 第77回(2024)
    for fn, yr in [
        ("jca_78_jhhs.html", "2025年（第78回）"),
        ("jca_77_jhhs.html", "2024年（第77回）"),
    ]:
        s_list, u_list = parse_jca_kako(PAST_DIR / fn, yr)
        school_recs.extend(s_list)
        univ_recs.extend(u_list)

    # 4. 日本学校合奏コンクール 2024(第13回) グランドコンテスト & 2025(第14回)文部科学大臣賞
    for cells in extract_rows(PAST_DIR / "jsecc_2024.html"):
        if len(cells) < 4 or not cells[0].isdigit():
            continue
        org = cells[2].replace(" ", "")
        aw_raw = cells[3].replace(" ", "")
        special = cells[4].replace(" ", "") if len(cells) > 4 else ""
        award = "最優秀賞" if "最優秀" in aw_raw else ("優秀賞" if "優秀" in aw_raw else norm_award(aw_raw))
        # Expand abbreviated 小/中/高 at end
        sname = org
        if sname.endswith("小"):
            sname = sname[:-1] + "小学校"
        elif sname.endswith("中"):
            sname = sname[:-1] + "中学校"
        elif sname.endswith("高"):
            sname = sname[:-1] + "高等学校"
        pref = ""
        for pname in PREF_SLUGS:
            if sname.startswith(pname):
                pref = pname
                sname = sname[len(pname) :]
                break
        div = "小学校の部" if "小学" in sname else ("中学校の部" if "中学" in sname and "高等" not in sname else "高等学校の部")
        school_recs.append({
            "pref": pref,
            "school_name": strip_club_suffix(sname),
            "raw_org": org,
            "contest": "日本学校合奏コンクール（全国学校合奏コンクール）",
            "year": "2024年（第13回）",
            "division": div,
            "award": award,
            "detail": special,
        })

    # 2025(第14回) 千葉県立幕張総合高等学校 (最優秀賞・文部科学大臣賞)
    school_recs.append({
        "pref": "千葉県",
        "school_name": "千葉県立幕張総合高等学校",
        "raw_org": "千葉県立幕張総合高等学校シンフォニックオーケストラ部",
        "contest": "日本学校合奏コンクール（全国学校合奏コンクール）",
        "year": "2025年（第14回）",
        "division": "高等学校の部",
        "award": "最優秀賞",
        "detail": "文部科学大臣賞",
    })

    # 5. NHK全国学校音楽コンクール（Nコン） 第92回(2025) & 第91回(2024)
    ncon_past = [
        # 第92回 (2025)
        ("東京都", "目黒区立東山小学校", "2025年（第92回）", "小学校の部", "金賞"),
        ("東京都", "日野市立平山小学校", "2025年（第92回）", "小学校の部", "銀賞"),
        ("東京都", "港区立白金小学校", "2025年（第92回）", "小学校の部", "銅賞"),
        ("岩手県", "北上市立黒沢尻北小学校", "2025年（第92回）", "小学校の部", "銅賞"),
        ("愛知県", "名古屋市立滝ノ水中学校", "2025年（第92回）", "中学校の部", "金賞"),
        ("東京都", "府中市立府中第四中学校", "2025年（第92回）", "中学校の部", "銀賞"),
        ("東京都", "豊島岡女子学園中学校", "2025年（第92回）", "中学校の部", "銅賞"),
        ("岩手県", "北上市立上野中学校", "2025年（第92回）", "中学校の部", "銅賞"),
        ("岩手県", "北上市立北上北中学校", "2025年（第92回）", "中学校の部", "銅賞"),
        ("岩手県", "北上市立北上中学校", "2025年（第92回）", "中学校の部", "銅賞"),
        ("千葉県", "専修大学松戸高等学校", "2025年（第92回）", "高等学校の部", "金賞"),
        ("福島県", "福島県立郡山高等学校", "2025年（第92回）", "高等学校の部", "銀賞"),
        ("東京都", "大妻中野高等学校", "2025年（第92回）", "高等学校の部", "銅賞"),
        ("東京都", "頌栄女子学院高等学校", "2025年（第92回）", "高等学校の部", "銅賞"),
        # 第91回 (2024)
        ("東京都", "日野市立平山小学校", "2024年（第91回）", "小学校の部", "金賞"),
        ("東京都", "港区立白金小学校", "2024年（第91回）", "小学校の部", "銀賞"),
        ("岩手県", "北上市立黒沢尻北小学校", "2024年（第91回）", "小学校の部", "銅賞"),
        ("山口県", "下関市立勝山小学校", "2024年（第91回）", "小学校の部", "銅賞"),
        ("岩手県", "北上市立上野中学校", "2024年（第91回）", "中学校の部", "金賞"),
        ("岩手県", "北上市立飯豊中学校", "2024年（第91回）", "中学校の部", "金賞"),
        ("岩手県", "北上市立南中学校", "2024年（第91回）", "中学校の部", "金賞"),
        ("岩手県", "北上市立東陵中学校", "2024年（第91回）", "中学校の部", "金賞"),
        ("岩手県", "北上市立北上北中学校", "2024年（第91回）", "中学校の部", "金賞"),
        ("岩手県", "北上市立北上中学校", "2024年（第91回）", "中学校の部", "金賞"),
        ("愛知県", "名古屋市立滝ノ水中学校", "2024年（第91回）", "中学校の部", "銀賞"),
        ("兵庫県", "武庫川女子大学附属中学校", "2024年（第91回）", "中学校の部", "銅賞"),
        ("東京都", "府中市立府中第四中学校", "2024年（第91回）", "中学校の部", "銅賞"),
        ("神奈川県", "清泉女学院高等学校", "2024年（第91回）", "高等学校の部", "金賞"),
        ("福島県", "福島県立会津高等学校", "2024年（第91回）", "高等学校の部", "銀賞"),
        ("千葉県", "専修大学松戸高等学校", "2024年（第91回）", "高等学校の部", "銅賞"),
        ("兵庫県", "武庫川女子大学附属高等学校", "2024年（第91回）", "高等学校の部", "銅賞"),
    ]
    for pref, sname, yr, div, aw in ncon_past:
        school_recs.append({
            "pref": pref,
            "school_name": sname,
            "raw_org": sname,
            "contest": "NHK全国学校音楽コンクール（Nコン）",
            "year": yr,
            "division": div,
            "award": aw,
            "detail": "",
        })

    # 6. こども音楽コンクール 令和6年度(第72期・2025年1月全国大会) 全12部門文部科学大臣賞
    kodomo_r6 = [
        ("北海道", "中標津町立中標津小学校", "小学校・重唱部門"),
        ("北海道", "中標津町立丸山小学校", "小学校・重唱部門"),
        ("山口県", "山口市立大殿小学校", "小学校・合唱部門"),
        ("奈良県", "天理小学校", "小学校・重奏部門"),
        ("千葉県", "船橋市立海神小学校", "小学校・合奏第1部門"),
        ("千葉県", "習志野市立谷津小学校", "小学校・合奏第2部門"),
        ("千葉県", "船橋市立西海神小学校", "小学校・管楽合奏部門"),
        ("大阪府", "清教学園中学校", "中学校・重唱部門"),
        ("北海道", "札幌市立札苗北中学校", "中学校・合唱部門"),
        ("千葉県", "習志野市立第一中学校", "中学校・重奏部門"),
        ("奈良県", "天理中学校", "中学校・合奏第1部門"),
        ("千葉県", "船橋市立葛飾中学校", "中学校・合奏第2部門"),
        ("千葉県", "船橋市立行田中学校", "中学校・合奏第2部門"),
        ("北海道", "旭川市立旭川中学校", "中学校・管楽合奏部門"),
    ]
    for pref, sname, div in kodomo_r6:
        school_recs.append({
            "pref": pref,
            "school_name": sname,
            "raw_org": sname,
            "contest": "こども音楽コンクール",
            "year": "令和6年度（第72期）",
            "division": div,
            "award": "文部科学大臣賞",
            "detail": "",
        })

    # 7. 全国高等学校軽音楽コンテスト 第11回(2024)
    keion_11 = [
        ("東京都", "桜美林高等学校", "グランプリ"),
        ("神奈川県", "神奈川県立上鶴間高等学校", "準グランプリ"),
        ("東京都", "東京都立練馬高等学校", "準グランプリ"),
        ("京都府", "大谷高等学校", "奨励賞"),
        ("千葉県", "千葉英和高等学校", "奨励賞"),
        ("奈良県", "奈良育英高等学校", "奨励賞"),
        ("神奈川県", "神奈川県立市ケ尾高等学校", "奨励賞"),
    ]
    for pref, sname, aw in keion_11:
        school_recs.append({
            "pref": pref,
            "school_name": sname,
            "raw_org": sname,
            "contest": "全国高等学校軽音楽コンテスト",
            "year": "2024年（第11回）",
            "division": "全国大会",
            "award": aw,
            "detail": "",
        })

    return school_recs, univ_recs


def main():
    school_recs, univ_recs = collect_past_records()
    print(f"Collected 2024-2025 past records: schools={len(school_recs)}, universities={len(univ_recs)}")
    print("By contest (schools):", dict(Counter(r["contest"] for r in school_recs)))

    # Load all 47 prefectures
    pref_schools: dict[str, list[dict]] = {}
    pref_matchers: dict[str, SchoolMatcher] = {}
    for pref_name, slug in PREF_SLUGS.items():
        schools = json.loads((DATA_DIR / f"{slug}.json").read_text(encoding="utf-8"))
        pref_schools[slug] = schools
        pref_matchers[slug] = SchoolMatcher(schools, pref_name)

    additions: dict[str, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))
    matched_cnt = 0
    unmatched = []

    for rec in school_recs:
        sname = rec["school_name"]
        div = rec["division"]
        thint = "小学校" if "小学" in div else ("中学校" if "中学" in div else ("高等学校" if "高等" in div or "高校" in div else ""))

        if rec["pref"] and rec["pref"] in PREF_SLUGS:
            slug = PREF_SLUGS[rec["pref"]]
            idxs = pref_matchers[slug].match(sname, type_hint=thint)
            if not idxs and "・" in sname:
                idxs = []
                for part in sname.split("・"):
                    idxs.extend(pref_matchers[slug].match(part.strip(), type_hint=thint))
            if idxs:
                for i in set(idxs):
                    additions[slug][i].append({
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
            found = False
            for sl in PREF_SLUGS.values():
                idxs = pref_matchers[sl].match(sname, type_hint=thint)
                if len(idxs) == 1:
                    additions[sl][idxs[0]].append({
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

    # Merge with existing music_awards and save
    award_order = {"文部科学大臣賞": 0, "グランプリ": 0, "最優秀賞": 0, "金賞": 1, "準グランプリ": 2, "銀賞": 2, "優秀賞": 2, "銅賞": 3, "奨励賞": 3, "優良賞": 4, "全国大会出場": 5}
    total_sc = 0
    total_ent = 0
    prefs_with_music = 0
    newly_added_ent = 0

    for pref_name, slug in PREF_SLUGS.items():
        schools = pref_schools[slug]
        sc_add = additions.get(slug, {})
        p_sc = 0
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
            newly_added_ent += max(0, len(deduped) - len(existing))
            # Sort newest year first, then award order
            deduped.sort(key=lambda x: (-int(re.search(r"20\d{2}", x["year"]).group(0)) if re.search(r"20\d{2}", x["year"]) else -2025, award_order.get(x["award"], 9), x["contest"]))
            sc["music_awards"] = deduped
            p_sc += 1
            total_sc += 1
            total_ent += len(deduped)
        if p_sc > 0:
            prefs_with_music += 1
        out_path = DATA_DIR / f"{slug}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(schools, f, ensure_ascii=False, indent=2)
            f.write("\n")

    # Merge university music contests
    univ_data = json.loads(UNIV_OUT.read_text(encoding="utf-8"))
    existing_u = univ_data.get("records") or []
    # Link university IDs
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

    combined_u = existing_u + univ_recs
    deduped_u = []
    seen_u = set()
    for urec in combined_u:
        k = (urec["contest"], urec["year"], urec["org_name"], urec["award"])
        if k in seen_u:
            continue
        seen_u.add(k)
        uid = univ_id_map.get(urec["university_name"].replace(" ", ""), "")
        if uid:
            urec["university_id"] = uid
        deduped_u.append(urec)

    deduped_u.sort(key=lambda x: (-int(re.search(r"20\d{2}", x["year"]).group(0)) if re.search(r"20\d{2}", x["year"]) else 0, award_order.get(x["award"], 9), x["contest"], x["pref"]))

    univ_data["sources"] = [
        "一般社団法人 全日本吹奏楽連盟 第74回（2026年）・第73回（2025年）・第72回（2024年）全日本吹奏楽コンクール大学の部",
        "一般社団法人 全日本合唱連盟 第79回（2026年）・第78回（2025年）・第77回（2024年）全日本合唱コンクール全国大会 大学ユース合唱の部",
    ]
    univ_data["records"] = deduped_u
    UNIV_OUT.write_text(json.dumps(univ_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"MATCHED past school records: {matched_cnt}/{len(school_recs)} (unmatched={len(unmatched)})")
    print(f"MERGED school DB totals (2024-2026): {prefs_with_music}/47 prefectures, {total_sc} schools, {total_ent} entries (+{newly_added_ent} new)")
    print(f"MERGED university DB totals (2024-2026): {len(deduped_u)} entries (was {len(existing_u)})")
    if unmatched:
        print("Unmatched sample:", unmatched[:10])


if __name__ == "__main__":
    main()
