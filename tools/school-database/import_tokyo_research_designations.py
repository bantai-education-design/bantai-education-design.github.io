#!/usr/bin/env python3
"""Import Tokyo FY2026 (令和8年度) research-designated schools into data/school-database/tokyo.json.

Primary official source:
  東京都教育委員会「令和８年度 研究協力校等一覧」(更新日: 2026年9月9日)
  https://www.kyoiku.metro.tokyo.lg.jp/school/designated_and_promotional_school/other/schools_r8
    1. 区市町村教育委員会 研究協力・奨励・推進・指定校・創意工夫ある学校等一覧
    2. 東京都教育委員会 研究指定校等一覧
    3. 文部科学省 関係事業及び研究指定校等一覧
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
TOKYO_JSON = ROOT / "data" / "school-database" / "tokyo.json"
DEFAULT_PDF_DIR = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\tokyo_research_pdfs"
)


def clean(val: object) -> str:
    if val is None:
        return ""
    s = unicodedata.normalize("NFKC", str(val))
    s = re.sub(r"\s+", " ", s).strip()
    return s


def norm_year(val: str) -> str:
    s = clean(val)
    s = s.replace("~", "〜").replace("～", "〜").replace("－", "〜").replace("-", "〜")
    s = re.sub(r"\s*〜\s*", "〜", s)
    s = re.sub(r"\s+", "", s)
    return s


def norm_subject(val: str) -> str:
    s = clean(val)
    s = s.replace(" ", "")
    if s in ("", "ー", "-", "―", "－", "なし", "無し"):
        return ""
    return s


def norm_chars(s: str) -> str:
    s = clean(s)
    s = re.sub(r"\([^)]*\)", "", s)
    s = s.replace(" ", "")
    for old, new in (
        ("ケ", "ヶ"),
        ("鷗", "鴎"),
        ("澤", "沢"),
        ("櫻", "桜"),
        ("廣", "広"),
        ("邊", "辺"),
        ("邉", "辺"),
        ("髙", "高"),
    ):
        s = s.replace(old, new)
    return s


def build_index(schools: list[dict]):
    muni_set = set(clean(sc.get("municipality", "")) for sc in schools)
    by_muni_short: dict[tuple[str, str], list[int]] = defaultdict(list)
    by_full: dict[str, list[int]] = defaultdict(list)
    by_short: dict[str, list[int]] = defaultdict(list)

    def strip_prefix(name: str, muni: str) -> str:
        s = norm_chars(name)
        if muni and muni in muni_set and s.startswith(muni + "立"):
            return s[len(muni) + 1 :]
        for p in ("東京都立", "都立"):
            if s.startswith(p):
                return s[len(p) :]
        return s

    for idx, sc in enumerate(schools):
        muni = clean(sc.get("municipality", ""))
        full = norm_chars(sc["school_name"])
        short = strip_prefix(full, muni)
        by_muni_short[(muni, short)].append(idx)
        by_full[full].append(idx)
        by_short[short].append(idx)

    return muni_set, by_muni_short, by_full, by_short, strip_prefix


# Explicit verified mappings for multi-school cells, PDF overlap artifacts, and exact name aliases
EXPLICIT_SCHOOL_MAP: dict[tuple[str, str], list[tuple[str, str]]] = {
    # (normalized_area, normalized_raw_name) -> list of (municipality_or_empty, exact_school_name_in_tokyo_json)
    ("港区", "白金の丘学園白金の丘小中学校"): [
        ("港区", "港区立白金の丘小学校"),
        ("港区", "港区立白金の丘中学校"),
    ],
    ("新宿区", "市谷幼稚園市ヶ谷小学校"): [
        ("新宿区", "新宿区立市谷幼稚園"),
        ("新宿区", "新宿区立市谷小学校"),
    ],
    ("新宿区", "花園幼稚園花園小学校"): [
        ("新宿区", "新宿区立花園幼稚園"),
        ("新宿区", "新宿区立花園小学校"),
    ],
    ("世田谷区", "認定こども園多聞幼稚園"): [
        ("世田谷区", "世田谷区立認定こども園世田谷区立多聞幼稚園"),
    ],
    ("世田谷区", "北沢学園中学校"): [
        ("世田谷区", "世田谷区立北沢中学校"),
    ],
    ("渋谷区", "渋谷本町学園小学校"): [
        ("渋谷区", "渋谷区立渋谷本町学園"),
    ],
    ("渋谷区", "渋谷本町学園中学校"): [
        ("渋谷区", "渋谷区立渋谷本町学園"),
    ],
    ("杉並区", "高円寺北子供園"): [
        ("杉並区", "杉並区立高円寺北子供園幼稚園"),
    ],
    ("杉並区", "堀ノ内子供園"): [
        ("杉並区", "杉並区立堀ノ内子供園幼稚園"),
    ],
    ("豊島区", "池袋第一小学校池袋本町小学校池袋中学校"): [
        ("豊島区", "豊島区立池袋第一小学校"),
        ("豊島区", "豊島区立池袋本町小学校"),
        ("豊島区", "豊島区立池袋中学校"),
    ],
    ("豊島区", "池袋小学校西池袋中学校"): [
        ("豊島区", "豊島区立池袋小学校"),
        ("豊島区", "豊島区立西池袋中学校"),
    ],
    ("豊島区", "池袋小学校・西池袋中学校"): [
        ("豊島区", "豊島区立池袋小学校"),
        ("豊島区", "豊島区立西池袋中学校"),
    ],
    ("練馬区", "豊玉第二中学校豊玉第二小学校豊玉東小学校"): [
        ("練馬区", "練馬区立豊玉第二中学校"),
        ("練馬区", "練馬区立豊玉第二小学校"),
        ("練馬区", "練馬区立豊玉東小学校"),
    ],
    ("練馬区", "大泉学園桜小学校大泉学園桜中学校"): [
        ("練馬区", "練馬区立大泉学園桜小学校"),
        ("練馬区", "練馬区立大泉学園桜中学校"),
    ],
    ("足立区", "千寿桜堤"): [
        ("足立区", "足立区立千寿桜堤中学校"),
    ],
    ("足立区", "新田学園"): [
        ("足立区", "足立区立新田小学校"),
        ("足立区", "足立区立新田中学校"),
    ],
    ("足立区", "新田小学校・新田中学校"): [
        ("足立区", "足立区立新田小学校"),
        ("足立区", "足立区立新田中学校"),
    ],
    ("江戸川区", "葛西小・中学校"): [
        ("江戸川区", "江戸川区立葛西小学校"),
        ("江戸川区", "江戸川区立葛西中学校"),
    ],
    ("八王子市", "館小中学校"): [
        ("八王子市", "八王子市立館小学校"),
        ("八王子市", "八王子市立館中学校"),
    ],
    ("八王子市", "いずみの森義務教育学"): [
        ("八王子市", "八王子市立いずみの森義務教育学校"),
    ],
    ("八王子市", "みなみ野小中学校"): [
        ("八王子市", "八王子市立みなみ野小学校"),
        ("八王子市", "八王子市立みなみ野中学校"),
    ],
    ("調布市", "飛会田科給、生小活学科校"): [
        ("調布市", "調布市立飛田給小学校"),
    ],
    ("日野市", "間日野第四小学校"): [
        ("日野市", "日野市立日野第四小学校"),
    ],
    ("東村山市", "東村山第三中学校萩山"): [
        ("東村山市", "東村山市立東村山第三萩山分校中学校"),
    ],
    ("東村山市", "東村山第三中学校萩山分校"): [
        ("東村山市", "東村山市立東村山第三萩山分校中学校"),
    ],
    ("国分寺市", "第習七の時小間学校"): [
        ("国分寺市", "国分寺市立第七小学校"),
    ],
    ("東久留米市", "指東導中学校"): [
        ("東久留米市", "東久留米市立東中学校"),
    ],
    ("東久留米市", "指西導中学校"): [
        ("東久留米市", "東久留米市立西中学校"),
    ],
    ("稲城市", "稲習城の時第間三小学校"): [
        ("稲城市", "稲城市立稲城第三小学校"),
    ],
    ("瑞穂町", "瑞習穂の時第間三小学校"): [
        ("瑞穂町", "瑞穂町立瑞穂第三小学校"),
    ],
    ("都立", "新宿山吹高校学校"): [
        ("新宿区", "東京都立新宿山吹高等学校"),
    ],
    ("都立", "富士高等学校・附属中学校"): [
        ("中野区", "東京都立富士高等学校"),
        ("中野区", "東京都立富士高等学校附属中学校"),
    ],
}


def main() -> None:
    pdf_dir = Path(os.environ.get("TOKYO_RESEARCH_PDF_DIR", str(DEFAULT_PDF_DIR)))
    with TOKYO_JSON.open("r", encoding="utf-8") as f:
        schools = json.load(f)

    muni_set, by_muni_short, by_full, by_short, strip_prefix = build_index(schools)

    def normalize_area(area: str) -> str:
        a = clean(area).replace(" ", "")
        if a in muni_set:
            return a
        if a in ("都立", "国立", "私立", "都立学校", "都立高校"):
            return a
        for suffix in ("区", "市", "町", "村"):
            if (a + suffix) in muni_set:
                return a + suffix
        return a

    def resolve_indices(area: str, raw_name: str, stype_hint: str | None = None) -> list[int]:
        area_n = normalize_area(area)
        name_n = norm_chars(raw_name)

        # Special bulk case: 大田区 中学校 全28校
        if area_n == "大田区" and name_n == "中学校全28校":
            return [
                i
                for i, sc in enumerate(schools)
                if sc.get("municipality") == "大田区"
                and sc.get("establishment_type") == "公立"
                and sc.get("school_type") == "中学校"
            ]

        # Explicit map
        if (area_n, name_n) in EXPLICIT_SCHOOL_MAP:
            targets = EXPLICIT_SCHOOL_MAP[(area_n, name_n)]
            res: list[int] = []
            for t_muni, t_name in targets:
                t_full = norm_chars(t_name)
                hits = [
                    i
                    for i in by_full.get(t_full, [])
                    if not t_muni or clean(schools[i].get("municipality", "")) == t_muni
                ]
                # Disambiguate 渋谷区立渋谷本町学園 by school_type hint if provided
                if len(hits) > 1 and stype_hint:
                    tmap = {"小": "小学校", "中": "中学校"}
                    if stype_hint in tmap:
                        hits = [i for i in hits if schools[i]["school_type"] == tmap[stype_hint]]
                res.extend(hits)
            return res

        short_n = strip_prefix(name_n, area_n)
        cands: list[int] = []
        if area_n in muni_set:
            cands = by_muni_short.get((area_n, short_n), [])
        if not cands and area_n in ("都立", ""):
            cands = by_full.get("東京都立" + short_n, [])
        if not cands:
            cands = by_full.get(name_n, [])
        if not cands:
            cands = by_short.get(short_n, [])
            if area_n in muni_set:
                cands = [i for i in cands if clean(schools[i].get("municipality", "")) == area_n]
        if len(cands) > 1 and stype_hint:
            tmap = {
                "幼": "幼稚園",
                "小": "小学校",
                "中": "中学校",
                "義": "義務教育学校",
                "高": "高等学校",
                "特": "特別支援学校",
            }
            if stype_hint in tmap:
                filtered = [i for i in cands if schools[i]["school_type"] == tmap[stype_hint]]
                if filtered:
                    cands = filtered
        return cands

    # Collect entries per school index
    per_school: dict[int, list[dict]] = defaultdict(list)
    skipped: list[tuple[str, str, str, str]] = []
    source_counts = Counter()

    # 1. PDF 1: 区市町村立学校における研究指定校等一覧
    cat_map = {"A": "区市町村", "B": "東京都", "C": "文部科学省"}
    with pdfplumber.open(pdf_dir / "pdf1_2026-09-07.pdf") as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for t in page.extract_tables():
                for row in t:
                    cells = [clean(c) for c in row if c is not None]
                    if len(cells) < 8:
                        continue
                    m = re.match(r"^\d{2}(.+)$", cells[0])
                    if not m:
                        continue
                    muni = m.group(1).strip()
                    if len(cells) == 10:
                        _, cat, stype, subj, sname, _cls, content, _kind, year, pres = cells
                    elif len(cells) == 9:
                        # p.9 江東区 第五砂町幼稚園 (missing cat col -> A)
                        _, stype, subj, sname, _cls, content, _kind, year, pres = cells
                        cat = "A"
                    else:
                        continue

                    # Fix known PDF column-overlap artifacts in subject text
                    subj_clean = norm_subject(subj)
                    if sname.startswith("飛会田科給"):
                        subj_clean = "社会科、生活科"
                    elif "習" in sname and "時" in sname and "間" in sname:
                        subj_clean = "総合的な学習の時間"
                    elif sname in ("指東導中学校", "指西導中学校"):
                        subj_clean = "生活指導"
                    elif sname == "間日野第四小学校":
                        subj_clean = "総合的な学習の時間"

                    indices = resolve_indices(muni, sname, stype)
                    if not indices:
                        skipped.append(("PDF1", muni, sname, content))
                        continue
                    authority = cat_map.get(cat, "区市町村")
                    entry = {
                        "year": norm_year(year),
                        "subject": subj_clean,
                        "designation": clean(content).replace(" ", ""),
                        "authority": authority,
                    }
                    pres_clean = clean(pres)
                    if pres_clean and pres_clean not in ("無し", "なし", "未定", "ー", "-"):
                        entry["presentation"] = pres_clean
                    for idx in indices:
                        per_school[idx].append(entry)
                    source_counts["PDF1"] += len(indices)

    # 2. PDF 2: 東京都教育委員会 研究指定校等一覧
    with pdfplumber.open(pdf_dir / "pdf2_2026-09-08.pdf") as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for t in page.extract_tables():
                for row in t:
                    if not row or len(row) < 4:
                        continue
                    proj, area, sname, year = clean(row[0]), clean(row[1]), clean(row[2]), clean(row[3])
                    if not sname or sname == "学校名" or proj.startswith("事業名"):
                        continue
                    # Fix known PDF2 page 6 overlapping row: 足立工科高等学校 (オンライン等での学びの評価研究校)
                    if pno == 6 and "オ教ン育ラ課イ程ン" in proj:
                        proj = "オンライン等での学びの評価研究校(令和7年度 新たな教育のスタイル研究校)"
                        area = "都立"
                        sname = "足立工科高等学校"
                        year = "令和7〜8"

                    indices = resolve_indices(area, sname)
                    if not indices:
                        skipped.append(("PDF2", area, sname, proj))
                        continue
                    entry = {
                        "year": norm_year(year),
                        "subject": "",
                        "designation": proj,
                        "authority": "東京都",
                    }
                    for idx in indices:
                        per_school[idx].append(entry)
                    source_counts["PDF2"] += len(indices)

    # 3. PDF 3: 文部科学省 関係事業及び研究指定校等一覧
    with pdfplumber.open(pdf_dir / "pdf3_2026-07-28.pdf") as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for t in page.extract_tables():
                for row in t:
                    if not row or len(row) < 4:
                        continue
                    proj, area, sname, year = clean(row[0]), clean(row[1]), clean(row[2]), clean(row[3])
                    if not sname or sname == "学校名" or proj.startswith("事業名"):
                        continue
                    indices = resolve_indices(area, sname)
                    if not indices:
                        skipped.append(("PDF3", area, sname, proj))
                        continue
                    entry = {
                        "year": norm_year(year),
                        "subject": "",
                        "designation": proj,
                        "authority": "文部科学省",
                    }
                    for idx in indices:
                        per_school[idx].append(entry)
                    source_counts["PDF3"] += len(indices)

    # Deduplicate entries per school (prefer entry with subject/presentation when authority+designation match)
    total_entries = 0
    schools_with_designations = 0
    for idx, sc in enumerate(schools):
        entries = per_school.get(idx, [])
        if not entries:
            sc.pop("research_designations", None)
            continue

        deduped: list[dict] = []
        for e in entries:
            merged = False
            for existing in deduped:
                if (
                    existing["authority"] == e["authority"]
                    and norm_chars(existing["designation"]) == norm_chars(e["designation"])
                ):
                    # Merge if same year or if one lacks subject (PDF1 vs PDF2/3 overlap)
                    if existing["year"] == e["year"] or (bool(existing["subject"]) != bool(e["subject"])):
                        if not existing["subject"] and e["subject"]:
                            existing["subject"] = e["subject"]
                        if "presentation" not in existing and "presentation" in e:
                            existing["presentation"] = e["presentation"]
                        merged = True
                        break
            if not merged:
                deduped.append(e)

        # Sort consistently: 文部科学省 -> 東京都 -> 区市町村, then year desc
        auth_order = {"文部科学省": 0, "東京都": 1, "区市町村": 2}
        deduped.sort(key=lambda x: (auth_order.get(x["authority"], 9), x["designation"], x["subject"]))

        sc["research_designations"] = deduped
        schools_with_designations += 1
        total_entries += len(deduped)

    with TOKYO_JSON.open("w", encoding="utf-8") as f:
        json.dump(schools, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Updated {TOKYO_JSON}")
    print(f"Total schools in tokyo.json: {len(schools)}")
    print(f"Schools with research designations: {schools_with_designations}")
    print(f"Total designation entries (after dedup): {total_entries}")
    print(f"Raw matched counts by source: {dict(source_counts)}")
    print(f"Skipped rows (not in tokyo.json): {len(skipped)}")
    for s in skipped:
        print("  SKIP:", s)


if __name__ == "__main__":
    main()
