#!/usr/bin/env python3
"""Merge prefecture & municipal official research-designated schools onto existing data
for Hiroshima (+Hiroshima City), Hyogo (Awaji BOE), Kyoto (+Kyoto City), and Miyagi (+Sendai City).
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "school-database"
CACHE_DIR = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\metro2_research"
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_kanto_research_designations import SchoolMatcher, clean, norm_chars
from import_metro_research_extras import merge_and_save
from enable_research_ui import update_html, update_js


# ---------------------------------------------------------------------------
# 1. HIROSHIMA (+ Hiroshima City)
# ---------------------------------------------------------------------------
def enrich_hiroshima():
    schools = json.loads((DATA_DIR / "hiroshima.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "広島県")
    additions: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    # A. 広島県教育委員会「令和8年度 研究公開校一覧」(4 PDFs)
    pref_pdfs = [
        ("hiro_pref_el.pdf", "小学校"),
        ("hiro_pref_jh.pdf", "中学校"),
        ("hiro_pref_gi.pdf", "義務教育学校"),
        ("hiro_pref_kg.pdf", "幼稚園"),
    ]
    for fn, stype in pref_pdfs:
        p = CACHE_DIR / fn
        if not p.exists():
            continue
        with pdfplumber.open(p) as pdf:
            for page in pdf.pages:
                for t in page.extract_tables():
                    for row in t:
                        if not row or len(row) < 6:
                            continue
                        if stype == "幼稚園":
                            pres = clean(row[0])
                            raw_sc = clean(row[1])
                            subj = "幼児教育"
                            kai = clean(row[2])
                            theme = clean(row[3])
                            shitei = clean(row[4])
                        else:
                            pres = clean(row[0])
                            raw_sc = clean(row[2])
                            subj = clean(row[3])
                            kai = clean(row[4])
                            theme = clean(row[5])
                            shitei = clean(row[7]) if len(row) > 7 else ""

                        if not raw_sc or "学校名" in raw_sc.replace(" ", "") or "幼稚園名" in raw_sc.replace(" ", ""):
                            continue
                        sname = re.sub(r"[（(][0-9\-]+[)）]", "", raw_sc).replace(" ", "")
                        if not sname:
                            continue
                        auth = "文部科学省" if ("文部" in shitei or "国" in shitei) else ("広島県" if ("県" in shitei or "新しい学び" in kai) else "市町村")
                        desig_text = f"{kai}：{theme}" if (kai and theme and kai != "自主公開") else (theme or kai or "研究公開校")
                        desig = desig_text[:65] + ("…" if len(desig_text) > 65 else "")
                        idxs = matcher.match(sname, type_hint=stype)
                        if not idxs:
                            unmatched.append((fn, sname))
                            continue
                        entry = {
                            "year": "令和8",
                            "subject": subj or "教育研究",
                            "designation": desig,
                            "authority": auth,
                        }
                        if pres and pres.startswith("R"):
                            entry["presentation"] = pres
                        for i in idxs:
                            additions[i].append(entry)

    # B. 広島市教育委員会「令和8年度 研究公開授業等実施一覧」(5 PDFs)
    city_pdfs = [
        ("hiro_city_kg.pdf", "幼稚園", False),
        ("hiro_city_el.pdf", "小学校", True),
        ("hiro_city_jh.pdf", "中学校", True),
        ("hiro_city_hs.pdf", "高等学校", True),
        ("hiro_city_sp.pdf", "特別支援学校", True),
    ]
    for fn, stype, has_subj_col in city_pdfs:
        p = CACHE_DIR / fn
        if not p.exists():
            continue
        with pdfplumber.open(p) as pdf:
            cur_sname = ""
            for page in pdf.pages:
                for t in page.extract_tables():
                    for row in t:
                        if not row or len(row) < 4:
                            continue
                        pres = clean(row[0])
                        raw_sc = clean(row[1]).replace(" ", "")
                        kai = clean(row[2])
                        theme = clean(row[3])
                        subj = clean(row[4]) if (has_subj_col and len(row) > 4) else ("幼児教育" if stype == "幼稚園" else "")
                        if pres == "公開日" or raw_sc == "校名":
                            continue
                        if raw_sc:
                            cur_sname = raw_sc
                        if not cur_sname or not (kai or theme):
                            continue
                        idxs = matcher.match(cur_sname, muni_hint="広島市")
                        if not idxs:
                            unmatched.append((fn, cur_sname))
                            continue
                        desig_text = f"{kai}（{theme}）" if (kai and theme) else (kai or theme)
                        desig = desig_text[:65] + ("…" if len(desig_text) > 65 else "")
                        entry = {
                            "year": "令和8",
                            "subject": subj or "教育研究",
                            "designation": desig,
                            "authority": "市町村",
                        }
                        if pres and pres.startswith("R"):
                            entry["presentation"] = pres
                        for i in idxs:
                            additions[i].append(entry)

    # C. 広島県東部教育事務所「令和8年度 文部科学省・県指定事業 指定校一覧」
    tobu_items = [
        ("文部科学省", "令和7〜10", "研究開発学校", "研究開発学校", [("尾道市", "因北小学校"), ("尾道市", "因北中学校")]),
        ("文部科学省", "令和8", "教育課程実践検証", "教育課程実践検証協力校事業", [("府中市", "府中学園")]),
        ("広島県", "令和8", "学びの変革", "市町の「学びの変革」チャレンジ加配", [("三原市", "糸崎小学校"), ("尾道市", "向東小学校"), ("世羅町", "甲山小学校")]),
        ("広島県", "令和8", "学習指導・生徒指導", "学習指導と生徒指導の一体的推進プロジェクト", [("三原市", "本郷中学校"), ("世羅町", "世羅中学校")]),
        ("広島県", "令和8", "小学校教科担任制", "小学校教科担任制推進事業", [
            ("三原市", "三原小学校"), ("三原市", "南小学校"), ("三原市", "本郷小学校"), ("三原市", "本郷西小学校"),
            ("尾道市", "尾道みなと小学校"), ("尾道市", "山波小学校"), ("尾道市", "日比崎小学校"), ("尾道市", "因北小学校"),
            ("府中市", "国府小学校"), ("府中市", "府中学園"),
        ]),
        ("広島県", "令和8", "英語・AI活用", "AIの活用による英語教育強化事業", [("府中市", "府中明郷学園")]),
        ("広島県", "令和8", "外国語教育", "小学校外国語教育推進研修", [("尾道市", "高須小学校"), ("府中市", "国府小学校")]),
        ("広島県", "令和8", "指導方法工夫改善", "指導方法工夫改善指定校", [("三原市", "中之町小学校"), ("三原市", "西小学校")]),
        ("広島県", "令和8", "ICT活用", "デジタル学習基盤活用研修サポート", [("三原市", "幸崎小学校"), ("神石高原町", "三和中学校"), ("神石高原町", "神石高原中学校")]),
        ("広島県", "令和8", "生徒指導", "生徒指導サポート実践校", [
            ("三原市", "中之町小学校"), ("三原市", "西小学校"), ("三原市", "南小学校"),
            ("尾道市", "尾道みなと小学校"), ("尾道市", "栗原小学校"), ("尾道市", "吉和小学校"), ("尾道市", "高須小学校"), ("尾道市", "栗原北小学校"),
            ("尾道市", "栗原中学校"), ("尾道市", "吉和中学校"), ("尾道市", "向島中学校"), ("尾道市", "因島南中学校"),
            ("府中市", "府中学園"),
        ]),
        ("広島県", "令和8", "不登校支援", "不登校SSR推進校", [
            ("三原市", "沼田東小学校"), ("三原市", "大和小学校"), ("三原市", "第三中学校"), ("三原市", "宮浦中学校"), ("三原市", "久井中学校"),
            ("尾道市", "向東小学校"), ("尾道市", "因北小学校"), ("尾道市", "尾道みなと中学校"), ("尾道市", "美木中学校"), ("尾道市", "高西中学校"), ("尾道市", "因北中学校"),
            ("府中市", "第一中学校"),
            ("世羅町", "世羅小学校"), ("世羅町", "甲山中学校"), ("世羅町", "世羅中学校"),
        ]),
    ]
    for auth, yr, subj, desig, targets in tobu_items:
        for muni, sname in targets:
            idxs = matcher.match(sname, muni_hint=muni)
            if not idxs:
                unmatched.append(("hiro_tobu", f"{muni}:{sname}"))
                continue
            for i in idxs:
                additions[i].append({"year": yr, "subject": subj, "designation": desig, "authority": auth})

    sc_cnt, ent_cnt, added = merge_and_save("hiroshima", "広島県", schools, additions)
    note = (
        "研究指定・公開校（年度・教科等・研究主題）は、広島県教育委員会「令和8年度研究公開校一覧」「令和8年度文部科学省・県指定事業指定校一覧」、"
        "広島市教育委員会「令和8年度研究公開授業等実施一覧」、および文部科学省・JSTの令和8年度全国公式一覧をもとに収録しています。"
    )
    update_html("hiroshima", "広島県", "研究指定・公開校（令和8年度）", note, ["文部科学省", "広島県", "市町村"])
    update_js("hiroshima", "研究指定・公開校（令和8年度）")
    print(f"[hiroshima] total_schools={sc_cnt}, total_entries={ent_cnt}, newly_added={added}, unmatched={len(unmatched)}")
    if unmatched:
        print("  hiroshima unmatched sample:", unmatched[:10])


# ---------------------------------------------------------------------------
# 2. HYOGO (Awaji Education Office R8 designated schools)
# ---------------------------------------------------------------------------
def enrich_hyogo():
    schools = json.loads((DATA_DIR / "hyogo.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "兵庫県")
    additions: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    raw = (CACHE_DIR / "hyogo_list.html").read_bytes()
    hhtml = ""
    for enc in ("utf-8", "cp932", "shift_jis"):
        try:
            dec = raw.decode(enc)
            if "淡路" in dec:
                hhtml = dec
                break
        except Exception:
            pass

    munis = ["洲本市", "南あわじ市", "淡路市"]
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", hhtml, re.S | re.I):
        cells = [clean(re.sub(r"<[^>]+>", " ", c)) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S | re.I)]
        if len(cells) < 4 or "事" in cells[0] and "業" in cells[0]:
            continue
        proj = cells[0].replace(" ", "")
        for ci, muni in enumerate(munis, 1):
            val = cells[ci].replace(" ", "")
            if not val:
                continue
            # Split concatenated short names ending in 小 / 中 / 幼
            for m in re.finditer(r"([一-龥ぁ-んァ-ヶ々ヶ]+?)([小中幼])", val):
                base, st = m.group(1), m.group(2)
                suf = {"小": "小学校", "中": "中学校", "幼": "幼稚園"}[st]
                sname = base + suf
                idxs = matcher.match(sname, muni_hint=muni, type_hint=suf)
                if not idxs:
                    unmatched.append(("hyogo_awaji", f"{muni}:{sname}"))
                    continue
                for i in idxs:
                    additions[i].append({
                        "year": "令和8",
                        "subject": proj,
                        "designation": "兵庫県淡路教育事務所 研究指定校",
                        "authority": "兵庫県",
                    })

    sc_cnt, ent_cnt, added = merge_and_save("hyogo", "兵庫県", schools, additions)
    note = (
        "研究指定校（年度・教科等・事業名）は、文部科学省・JSTの令和8年度全国公式一覧および"
        "兵庫県教育委員会淡路教育事務所「令和8年度研究指定校一覧」をもとに収録しています。"
    )
    update_html("hyogo", "兵庫県", "研究指定校（令和8年度）", note, ["文部科学省", "兵庫県"])
    update_js("hyogo", "研究指定校（令和8年度）")
    print(f"[hyogo] total_schools={sc_cnt}, total_entries={ent_cnt}, newly_added={added}, unmatched={len(unmatched)}")
    if unmatched:
        print("  hyogo unmatched sample:", unmatched[:8])


# ---------------------------------------------------------------------------
# 3. KYOTO (+ Kyoto City)
# ---------------------------------------------------------------------------
def enrich_kyoto():
    schools = json.loads((DATA_DIR / "kyoto.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "京都府")
    additions: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    items = [
        ("京都市立御所南小学校", "文部科学省", "令和7〜10", "研究開発学校", "文部科学省研究開発学校"),
        ("京都府立清明高等学校", "文部科学省", "令和8〜10", "研究開発学校", "文部科学省研究開発学校"),
        ("京都市立朱雀第一小学校", "市町村", "令和7〜8", "人権教育", "京都市 人権教育研究指定校"),
    ]
    for sname, auth, yr, subj, desig in items:
        idxs = matcher.match(sname)
        if not idxs:
            unmatched.append(("kyoto", sname))
            continue
        for i in idxs:
            additions[i].append({"year": yr, "subject": subj, "designation": desig, "authority": auth})

    sc_cnt, ent_cnt, added = merge_and_save("kyoto", "京都府", schools, additions)
    note = (
        "研究指定校（年度・教科等・事業名）は、文部科学省・JSTの令和8年度全国公式一覧（DXハイスクール・サキドリ研究校・SSH・研究開発学校）"
        "および京都市教育委員会（人権教育研究指定校）をもとに収録しています。"
    )
    update_html("kyoto", "京都府", "研究指定校（令和7〜8年度）", note, ["文部科学省", "市町村"])
    update_js("kyoto", "研究指定校（令和7〜8年度）")
    print(f"[kyoto] total_schools={sc_cnt}, total_entries={ent_cnt}, newly_added={added}, unmatched={len(unmatched)}")


# ---------------------------------------------------------------------------
# 4. MIYAGI (+ Sendai City)
# ---------------------------------------------------------------------------
def enrich_miyagi():
    schools = json.loads((DATA_DIR / "miyagi.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "宮城県")
    additions: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    # Sendai City: 令和8年度 新教科「（仮称）国際探究科」実践研究協力校
    for sname in ["仙台市立向山小学校", "仙台市立愛宕中学校", "仙台市立南吉成小学校", "仙台市立南吉成中学校"]:
        idxs = matcher.match(sname, muni_hint="仙台市")
        if not idxs:
            unmatched.append(("sendai_intl", sname))
            continue
        for i in idxs:
            additions[i].append({
                "year": "令和8",
                "subject": "（仮称）国際探究科",
                "designation": "仙台市 新教科「（仮称）国際探究科」実践研究協力校",
                "authority": "市町村",
            })

    sc_cnt, ent_cnt, added = merge_and_save("miyagi", "宮城県", schools, additions)
    note = (
        "研究指定・協力校（年度・教科等・事業名）は、文部科学省・JSTの令和8年度全国公式一覧および"
        "仙台市教育委員会「新教科（仮称）国際探究科 実践研究協力校（令和8年度）」をもとに収録しています。"
    )
    update_html("miyagi", "宮城県", "研究指定・協力校（令和8年度）", note, ["文部科学省", "市町村"])
    update_js("miyagi", "研究指定・協力校（令和8年度）")
    print(f"[miyagi] total_schools={sc_cnt}, total_entries={ent_cnt}, newly_added={added}, unmatched={len(unmatched)}")


if __name__ == "__main__":
    enrich_hiroshima()
    enrich_hyogo()
    enrich_kyoto()
    enrich_miyagi()
