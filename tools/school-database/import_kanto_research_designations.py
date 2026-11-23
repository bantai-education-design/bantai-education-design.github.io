#!/usr/bin/env python3
"""Import official research-designated schools for Kanto 6 prefectures
(Chiba, Saitama, Kanagawa, Gunma, Tochigi, Ibaraki) into data/school-database/{slug}.json.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "school-database"
CACHE_DIR = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\kanto_research"
)


def clean(val: object) -> str:
    if val is None:
        return ""
    s = unicodedata.normalize("NFKC", str(val))
    return re.sub(r"\s+", " ", s).strip()


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
        ("高校", "高等学校"),
    ):
        s = s.replace(old, new)
    # Fix accidental 高等学校学校
    s = s.replace("高等学校学校", "高等学校")
    return s


def get_name(sc: dict) -> str:
    return sc.get("school_name") or sc.get("name") or ""


class SchoolMatcher:
    def __init__(self, schools: list[dict], pref_name: str):
        self.schools = schools
        self.pref_name = pref_name
        self.by_full: dict[str, list[int]] = defaultdict(list)
        self.by_short: dict[str, list[int]] = defaultdict(list)
        self.by_muni_short: dict[tuple[str, str], list[int]] = defaultdict(list)
        self.muni_set = set(clean(s.get("municipality", "")) for s in schools)

        for idx, sc in enumerate(schools):
            muni = clean(sc.get("municipality", ""))
            full = norm_chars(get_name(sc))
            short = self._strip_prefix(full, muni)
            self.by_full[full].append(idx)
            self.by_short[short].append(idx)
            if muni:
                self.by_muni_short[(muni, short)].append(idx)

    def _strip_prefix(self, s: str, muni: str = "") -> str:
        if muni and s.startswith(muni + "立"):
            return s[len(muni) + 1 :]
        for p in (
            self.pref_name + "立",
            "県立",
            "市立",
            "町立",
            "村立",
        ):
            if s.startswith(p):
                return s[len(p) :]
        # Strip any XX市立 / XX町立 / XX村立
        m = re.match(r"^[^市立町村]+[市区町村]立(.+)$", s)
        if m:
            return m.group(1)
        return s

    def match(self, raw_name: str, muni_hint: str = "", type_hint: str = "") -> list[int]:
        n = norm_chars(raw_name)
        if not n:
            return []
        cands = self.by_full.get(n, [])
        if not cands:
            # Try with prefecture prefix
            cands = self.by_full.get(norm_chars(self.pref_name + "立" + n), [])
        if not cands and muni_hint:
            # Try muni_hint + 立 + short
            sh = self._strip_prefix(n, muni_hint)
            cands = self.by_muni_short.get((muni_hint, sh), [])
            if not cands:
                # Try matching municipality ending with muni_hint (e.g. 郡付き)
                for (m, s), idxs in self.by_muni_short.items():
                    if s == sh and m.endswith(muni_hint):
                        cands = idxs
                        break
        if not cands:
            sh = self._strip_prefix(n, muni_hint)
            cands = self.by_short.get(sh, [])
            if len(cands) > 1 and muni_hint:
                filtered = [i for i in cands if muni_hint in clean(self.schools[i].get("municipality", ""))]
                if filtered:
                    cands = filtered
        if len(cands) > 1 and type_hint:
            filtered = [i for i in cands if self.schools[i].get("school_type") == type_hint]
            if filtered:
                cands = filtered
        return cands


def save_designations(slug: str, schools: list[dict], per_school: dict[int, list[dict]], pref_name: str) -> tuple[int, int]:
    auth_order = {"文部科学省": 0, pref_name: 1, "市町村": 2}
    school_count = 0
    entry_count = 0
    for idx, sc in enumerate(schools):
        entries = per_school.get(idx, [])
        if not entries:
            sc.pop("research_designations", None)
            continue
        deduped = []
        seen = set()
        for e in entries:
            key = (e["authority"], e["year"], norm_chars(e["subject"]), norm_chars(e["designation"]))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(e)
        deduped.sort(key=lambda x: (auth_order.get(x["authority"], 9), x["designation"], x["subject"]))
        sc["research_designations"] = deduped
        school_count += 1
        entry_count += len(deduped)

    out_path = DATA_DIR / f"{slug}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(schools, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return school_count, entry_count


# ---------------------------------------------------------------------------
# 1. CHIBA
# ---------------------------------------------------------------------------
def import_chiba():
    schools = json.loads((DATA_DIR / "chiba.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "千葉県")
    per_school: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    pdf_files = [
        ("chiba_01_elem_jhs.pdf", True),
        ("chiba_08_pref_jhs.pdf", False),
        ("chiba_09_pref_hs.pdf", False),
        ("chiba_10_pref_sp.pdf", False),
    ]

    def map_chiba_auth(raw: str) -> str:
        r = clean(raw)
        if "文" in r or "国" in r:
            return "文部科学省"
        if "県" in r:
            return "千葉県"
        return "市町村"

    def fmt_chiba_year(y1: str, y2: str) -> str:
        s1 = re.sub(r"[^\d]", "", clean(y1))
        s2 = re.sub(r"[^\d]", "", clean(y2))
        if s1 and s2:
            return f"令和{s1}" if s1 == s2 else f"令和{s1}〜{s2}"
        if s1:
            return f"令和{s1}"
        if s2:
            return f"令和{s2}"
        return "令和8"

    for fname, has_office in pdf_files:
        with pdfplumber.open(CACHE_DIR / fname) as pdf:
            for page in pdf.pages:
                for t in page.extract_tables():
                    for row in t:
                        if not row or len(row) < 8:
                            continue
                        no = clean(row[0])
                        if not no or not no.isdigit():
                            continue
                        if has_office:
                            # [No, 教育事務所, 校種, 学校名, 種別, 開始, 終了, 教科・領域等, 研究主題等, 公開有無, 公開期日]
                            stype = clean(row[2])
                            sname = clean(row[3])
                            auth = map_chiba_auth(row[4])
                            yr = fmt_chiba_year(row[5], row[6])
                            subj = clean(row[7])
                            theme = clean(row[8]) if len(row) > 8 else ""
                            pres = clean(row[10]) if len(row) > 10 else ""
                        else:
                            # [No, 校種, 学校名, 種別, 開始, 終了, 教科・領域等, 研究主題等, 公開有無, 公開期日]
                            stype = clean(row[1])
                            sname = clean(row[2])
                            auth = map_chiba_auth(row[3])
                            yr = fmt_chiba_year(row[4], row[5])
                            subj = clean(row[6])
                            theme = clean(row[7]) if len(row) > 7 else ""
                            pres = clean(row[9]) if len(row) > 9 else ""

                        tmap = {"小": "小学校", "中": "中学校", "義": "義務教育学校", "高": "高等学校"}
                        thint = tmap.get(stype, stype if stype in ("小学校", "中学校", "高等学校", "特別支援学校") else "")
                        idxs = matcher.match(sname, type_hint=thint)
                        if not idxs:
                            unmatched.append((fname, sname))
                            continue
                        # Shorten overly long theme if needed
                        desig = theme[:60] + ("…" if len(theme) > 60 else "") if theme else "研究指定校"
                        entry = {
                            "year": yr,
                            "subject": subj,
                            "designation": desig,
                            "authority": auth,
                        }
                        if pres and pres not in ("1", "無", "未定", "-"):
                            entry["presentation"] = pres
                        for i in idxs:
                            per_school[i].append(entry)

    sc_cnt, ent_cnt = save_designations("chiba", schools, per_school, "千葉県")
    print(f"[chiba] schools={sc_cnt}, entries={ent_cnt}, unmatched={len(unmatched)}")
    if unmatched:
        print("  chiba unmatched sample:", unmatched[:10])


# ---------------------------------------------------------------------------
# 2. GUNMA
# ---------------------------------------------------------------------------
def import_gunma():
    schools = json.loads((DATA_DIR / "gunma.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "群馬県")
    per_school: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    text = (CACHE_DIR / "gunma_710284.pdf.txt").read_text(encoding="utf-8")
    authority = "群馬県"
    cur_proj = ""
    cur_year = "令和8"

    def parse_gunma_year(s: str) -> str:
        s = clean(s).replace(" ", "")
        s = re.sub(r"^\([^)]*\)", "", s)
        s = s.replace("令", "令和").replace("平", "平成").replace("~", "〜").replace("～", "〜")
        s = s.replace("令和和", "令和").replace("平成成", "平成")
        if s in ("", "〃", "経過措置"):
            return ""
        return s

    for line in text.splitlines():
        l = clean(line)
        if not l or l.startswith("===") or l.startswith("- ") or l.startswith("１５") or l.startswith("指 定") or l.startswith("種 別"):
            continue
        if "ア 県教育委員会指定" in l:
            authority = "群馬県"
            continue
        if "イ 文部科学省指定" in l:
            authority = "文部科学省"
            continue
        if l.startswith("(2) 高等学校") or l.startswith("(3) 特別支援学校"):
            authority = "群馬県"
            continue

        # Detect project title
        if l.startswith("・"):
            # Split project name and possible school name on same line
            body = l[1:].strip()
            # Extract school name if present (contains 学校/幼稚園/高校/中学/小学)
            m_sc = re.search(r"((?:群馬県立|群馬大学共同教育学部附属|[^\s・]+(?:市立|町立|村立))[^\s（(]+(?:小学校|中学校|高等学校|特別支援学校|幼稚園))", body)
            if m_sc:
                proj_part = body[: m_sc.start()].strip()
                if proj_part:
                    cur_proj = proj_part
                sname = m_sc.group(1)
                rest = body[m_sc.end() :].strip()
                yr = parse_gunma_year(rest)
                if yr:
                    cur_year = yr
                proj_auth = "文部科学省" if any(k in cur_proj for k in ("スーパーサイエンス", "DX加速化", "教育課程実践検証", "道徳教育総合支援", "教育課程柔軟化")) else authority
                idxs = matcher.match(sname)
                if idxs:
                    for i in idxs:
                        per_school[i].append({"year": cur_year, "subject": "", "designation": cur_proj, "authority": proj_auth})
                else:
                    unmatched.append((cur_proj, sname))
            else:
                cur_proj = body
            continue

        # Continuation lines with school names
        m_sc = re.search(r"((?:群馬県立|群馬大学共同教育学部附属|[^\s・]+(?:市立|町立|村立))[^\s（(]+(?:小学校|中学校|高等学校|特別支援学校|幼稚園))", l)
        if m_sc and cur_proj:
            sname = m_sc.group(1)
            rest = l[m_sc.end() :].strip()
            yr = parse_gunma_year(rest)
            if yr:
                cur_year = yr
            proj_auth = "文部科学省" if any(k in cur_proj for k in ("スーパーサイエンス", "DX加速化", "教育課程実践検証", "道徳教育総合支援", "教育課程柔軟化")) else authority
            idxs = matcher.match(sname)
            if idxs:
                for i in idxs:
                    per_school[i].append({"year": cur_year, "subject": "", "designation": cur_proj, "authority": proj_auth})
            else:
                unmatched.append((cur_proj, sname))

    sc_cnt, ent_cnt = save_designations("gunma", schools, per_school, "群馬県")
    print(f"[gunma] schools={sc_cnt}, entries={ent_cnt}, unmatched={len(unmatched)}")
    if unmatched:
        print("  gunma unmatched:", unmatched[:10])


# ---------------------------------------------------------------------------
# 3. SAITAMA
# ---------------------------------------------------------------------------
def import_saitama():
    schools = json.loads((DATA_DIR / "saitama.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "埼玉県")
    per_school: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    # Parse structured tables directly from saitama_5035.pdf
    cur_year = "令和7"
    cur_auth = "埼玉県"

    def extract_schools_from_text(txt: str):
        # Clean line breaks inside school names
        t = re.sub(r"\s+", "", clean(txt))
        # Split by 、 or ・ (careful with 技術・家庭)
        # Better: regex find all school names ending in 小学校/中学校/小中学校/高等学校/高校/特別支援学校/分校
        # First check for (科目) pattern used in 実践検証協力校
        results = []
        pattern = re.compile(
            r"([一-龥ぁ-んァ-ヶ々ヶa-zA-Z]+?(?:市立|町立|村立|県立)?[一-龥ぁ-んァ-ヶ々ヶ]+?(?:小学校|中学校|小中学校|高等学校|高校|特別支援学校(?:[一-龥]+分校)?))(?:\(([^)]+)\))?"
        )
        for m in pattern.finditer(t):
            sname = m.group(1)
            note = m.group(2) or ""
            # Strip leading non-school labels like 【全日制】【定時制】【指定校】【推進校】【派遣校】【受入校】
            sname = re.sub(r"^.*?(?:】|、|,)", "", sname)
            if not sname or sname.startswith("県内") or "全137校" in sname:
                continue
            results.append((sname, note))
        return results

    with pdfplumber.open(CACHE_DIR / "saitama_5035.pdf") as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            txt = page.extract_text() or ""
            if "文部科学省研究指定校" in txt:
                # Page 5 has both Saitama (top) and MEXT (bottom)
                pass
            for ti, t in enumerate(page.extract_tables()):
                # Determine year & authority context by page/table
                if pno == 1:
                    yr_map = {0: "令和5〜7", 1: "令和6〜7", 2: "令和7", 3: "令和7〜8"}
                    cur_year = yr_map.get(ti, "令和7")
                    cur_auth = "埼玉県"
                elif pno == 2:
                    yr_map = {0: "令和5〜7", 1: "令和6〜7", 2: "令和7"}
                    cur_year = yr_map.get(ti, "令和7")
                    cur_auth = "埼玉県"
                elif pno in (3, 4):
                    cur_year = "令和7"
                    cur_auth = "埼玉県"
                elif pno == 5:
                    if ti == 0:
                        cur_year = "令和7〜8"
                        cur_auth = "埼玉県"
                    else:
                        cur_year = "令和7"
                        cur_auth = "文部科学省"

                cur_proj = ""
                for row in t:
                    if not row or len(row) < 2:
                        continue
                    c0 = clean(row[0]).replace(" ", "")
                    c1 = clean(row[1])
                    if c0 in ("研究領域等", "") and ("学校名" in c1.replace(" ", "") or "特別支援学校名" in c1.replace(" ", "")):
                        continue
                    if c0:
                        cur_proj = c0
                    if not cur_proj or "生徒指導重点校" in cur_proj or "未来を拓く" in cur_proj or "学力保障スクラム" in cur_proj:
                        continue
                    # Extract schools from c1
                    found = extract_schools_from_text(c1)
                    for sname, note in found:
                        # Handle 川島町立つばさ小学校・川島中学校 etc.
                        pres = ""
                        subj = ""
                        if note:
                            if note.startswith("R") or "合同開催" in note or "成果報告" in note:
                                pres = note
                            elif note not in ("通", "定", "単定・単通"):
                                subj = note
                        if cur_proj == "スーパーサイエンスハイスクール事業(SSH)":
                            subj = "理数・科学技術"
                        idxs = matcher.match(sname)
                        if not idxs:
                            unmatched.append((pno, cur_proj, sname))
                            continue
                        entry = {
                            "year": cur_year,
                            "subject": subj,
                            "designation": cur_proj,
                            "authority": cur_auth,
                        }
                        if pres:
                            entry["presentation"] = pres
                        for i in idxs:
                            per_school[i].append(entry)

    sc_cnt, ent_cnt = save_designations("saitama", schools, per_school, "埼玉県")
    print(f"[saitama] schools={sc_cnt}, entries={ent_cnt}, unmatched={len(unmatched)}")
    if unmatched:
        print("  saitama unmatched sample:", unmatched[:12])


# ---------------------------------------------------------------------------
# 4. KANAGAWA
# ---------------------------------------------------------------------------
def import_kanagawa():
    schools = json.loads((DATA_DIR / "kanagawa.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "神奈川県")
    per_school: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    # Source 1: 県立高校改革実施計画(Ⅲ期) 令和7〜9年度指定校 (verified from kanagawa_hs_ichiran.jpg)
    hs_data = [
        ("シチズンシップ教育", "教育課程研究開発校", ["城郷", "横浜瀬谷", "藤沢総合", "小田原東", "相模田名", "厚木王子"]),
        ("学習評価", "教育課程研究開発校", ["新城", "松陽", "逗子葉山", "平塚農商", "上溝"]),
        ("総合的な探究の時間", "教育課程研究開発校", ["市ヶ尾", "横浜清陵", "藤沢西", "秦野総合", "大和", "津久井"]),
        ("総合的な探究の時間（SDGs）", "教育課程研究開発校", ["川崎", "舞岡", "大船", "山北", "有馬"]),
        ("", "授業力向上推進重点校", ["元石川", "横浜立野", "追浜", "秦野曽屋", "上溝南"]),
        ("ICT利活用", "ICT利活用授業研究推進校", ["生田東", "横浜南陵", "藤沢工科", "伊勢原", "神奈川総合産業"]),
        ("プログラミング教育", "プログラミング教育研究推進校", ["住吉", "横浜栄", "茅ヶ崎西浜", "西湘", "相模原城山"]),
        ("", "確かな学力育成推進校", ["菅", "永谷", "寒川", "平塚湘風", "愛川"]),
        ("STEAM教育", "STEAM教育研究推進校", ["神奈川工業", "光陵", "横須賀", "秦野", "相模原弥栄"]),
        ("理数教育", "理数教育推進校", ["生田", "鎌倉"]),
        ("グローバル教育", "グローバル教育研究推進校", ["神奈川総合", "横浜氷取沢", "鶴嶺", "大磯", "大和西"]),
    ]
    for subj, desig, names in hs_data:
        for short_name in names:
            yr = "令和7〜8" if short_name == "永谷" else "令和7〜9"
            # Match 神奈川県立{short_name}高等学校
            full_cand = f"神奈川県立{short_name}高等学校"
            idxs = matcher.match(full_cand, type_hint="高等学校")
            if not idxs:
                # Filter by 公立高等学校
                idxs = [i for i in matcher.match(short_name + "高等学校", type_hint="高等学校") if schools[i].get("establishment") == "公立"]
            if not idxs:
                unmatched.append(("HS", short_name))
                continue
            for i in idxs:
                per_school[i].append({
                    "year": yr,
                    "subject": subj,
                    "designation": desig,
                    "authority": "神奈川県",
                })

    # Source 2: かながわ学びづくり推進地域（令和7年度・小中学校）
    req = urllib.request.Request("https://www.pref.kanagawa.jp/docs/v3p/manabi/torikumi/toppupeji.html", headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="ignore")
    cur_muni = ""
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+\.pdf)["\'][^>]*>(.*?)</a>', html, re.S | re.I):
        txt = clean(re.sub(r"<[^>]+>", "", m.group(2)))
        txt = re.sub(r"\(PDF[^)]*\)", "", txt).strip()
        m_city = re.match(r"^([^\s]+(?:市|町|村))の取組$", txt)
        if m_city:
            cur_muni = m_city.group(1)
            continue
        if cur_muni and any(txt.endswith(suf) for suf in ("小学校", "中学校", "義務教育学校")):
            idxs = matcher.match(txt, muni_hint=cur_muni)
            if not idxs:
                unmatched.append(("MANABI", f"{cur_muni}:{txt}"))
                continue
            for i in idxs:
                per_school[i].append({
                    "year": "令和7",
                    "subject": "学力向上・授業改善",
                    "designation": "かながわ学びづくり推進地域 推進校",
                    "authority": "神奈川県",
                })

    sc_cnt, ent_cnt = save_designations("kanagawa", schools, per_school, "神奈川県")
    print(f"[kanagawa] schools={sc_cnt}, entries={ent_cnt}, unmatched={len(unmatched)}")
    if unmatched:
        print("  kanagawa unmatched:", unmatched[:10])


# ---------------------------------------------------------------------------
# 5. TOCHIGI
# ---------------------------------------------------------------------------
def import_tochigi():
    schools = json.loads((DATA_DIR / "tochigi.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "栃木県")
    per_school: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    req = urllib.request.Request(
        "https://www.pref.tochigi.lg.jp/m04/education/gakkoukyouiku/koutou/1192616205884.html",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="ignore")
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I)

    cur_proj = ""
    cur_period = ""
    for r in rows:
        cells = [clean(re.sub(r"<[^>]+>", "", c).replace("&nbsp;", " ")) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.S | re.I)]
        if len(cells) < 2:
            continue
        k, v = cells[0], cells[1]
        if k == "事業名":
            cur_proj = v
        elif k == "実施期間":
            cur_period = v.replace("~", "〜").replace("～", "〜")
        elif k == "指定校名" and cur_proj:
            auth = "文部科学省" if any(w in cur_proj for w in ("スーパーサイエンス", "地域との協働", "エネルギー教育")) else "栃木県"
            subj = "理数・科学技術" if "スーパーサイエンス" in cur_proj else ("人権教育" if "人権教育" in cur_proj else ("農業" if "農業教育" in cur_proj else ("英語・グローバル" if "グローバル" in cur_proj else "")))
            # Extract school names
            for m in re.finditer(r"([一-龥ぁ-んァ-ヶ々ヶ]+?(?:高等学校|附属中学校|特別支援学校|中学校|小学校))", v):
                sname = m.group(1)
                sname = re.sub(r"^(?:プロフェッショナル型指定校|指定校|設置|年度)", "", sname)
                if sname == "附属中学校":
                    sname = "宇都宮東高等学校附属中学校"
                idxs = matcher.match(sname)
                if not idxs:
                    unmatched.append((cur_proj, sname))
                    continue
                yr = cur_period.replace("年度", "").replace("から", "〜")
                for i in idxs:
                    per_school[i].append({
                        "year": yr,
                        "subject": subj,
                        "designation": cur_proj,
                        "authority": auth,
                    })

    sc_cnt, ent_cnt = save_designations("tochigi", schools, per_school, "栃木県")
    print(f"[tochigi] schools={sc_cnt}, entries={ent_cnt}, unmatched={len(unmatched)}")
    if unmatched:
        print("  tochigi unmatched:", unmatched[:10])


# ---------------------------------------------------------------------------
# 6. IBARAKI
# ---------------------------------------------------------------------------
def import_ibaraki():
    schools = json.loads((DATA_DIR / "ibaraki.json").read_text(encoding="utf-8"))
    matcher = SchoolMatcher(schools, "茨城県")
    per_school: dict[int, list[dict]] = defaultdict(list)
    unmatched = []

    with pdfplumber.open(CACHE_DIR / "ibaraki_2023.pdf") as pdf:
        for page in pdf.pages:
            for t in page.extract_tables():
                cur_cat = ""
                for row in t:
                    if not row or len(row) < 3:
                        continue
                    c0 = clean(row[0]).replace(" ", "")
                    c1 = clean(row[1]).replace(" ", "")
                    c2 = clean(row[2])
                    if c0 == "分類" or c1 == "事業名等":
                        continue
                    if c0:
                        cur_cat = c0
                    if not c1 or not c2:
                        continue
                    auth = "文部科学省" if "文部科学省" in cur_cat else "茨城県"
                    # Extract subject in parentheses if present
                    m_sub = re.search(r"\(([^)]+)\)", c1)
                    subj = m_sub.group(1) if m_sub else cur_cat
                    for m in re.finditer(r"([一-龥ぁ-んァ-ヶ々ヶ]+?(?:市立|町立|村立)[一-龥ぁ-んァ-ヶ々ヶ]+?(?:小学校|中学校|義務教育学校|高等学校|特別支援学校))", c2):
                        sname = m.group(1)
                        idxs = matcher.match(sname)
                        if not idxs:
                            unmatched.append((c1, sname))
                            continue
                        for i in idxs:
                            per_school[i].append({
                                "year": "令和5",
                                "subject": subj,
                                "designation": c1,
                                "authority": auth,
                            })

    sc_cnt, ent_cnt = save_designations("ibaraki", schools, per_school, "茨城県")
    print(f"[ibaraki] schools={sc_cnt}, entries={ent_cnt}, unmatched={len(unmatched)}")
    if unmatched:
        print("  ibaraki unmatched:", unmatched[:10])


if __name__ == "__main__":
    import_chiba()
    import_saitama()
    import_kanagawa()
    import_gunma()
    import_tochigi()
    import_ibaraki()
