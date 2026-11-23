#!/usr/bin/env python3
"""Import official Japan Kanji Aptitude Test (漢検) Quasi-Venue Group Award schools
(2024 & 2025, from https://www.kanken.or.jp/kanken/kanken-awards/js/{2024,2025}.js)
into Nationwide School DB (data/school-database/*.json) as `culture_awards`.
Also adds '漢検（準会場・団体表彰）' to all 47 prefecture culture filter dropdowns.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "school-database"
KANKEN_DIR = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\kanken_probe"
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_kanto_research_designations import SchoolMatcher, clean
from mext_national_research import PREF_SLUGS, norm_pref

CAT = "漢検（準会場・団体表彰）"
SCHOOL_KEYWORDS = ("小学校", "中学校", "高等学校", "中等教育学校", "義務教育学校", "小学部", "中学部", "高等部", "高校", "学園", "学院")
NON_SCHOOL_KEYWORDS = ("株式会社", "社会福祉法人", "一般社団法人", "NPO", "学習塾", "ゼミナール", "進学教室", "英会話", "パソコン", "書道教室", "そろばん", "児童クラブ", "学童", "大学", "専門学校", "高等専門学校")

AWARD_ORDER = {
    "文部科学大臣賞": 0,
    "最優秀団体賞": 1,
    "日本漢字能力検定協会賞": 1,
    "優秀団体賞": 2,
    "奨励賞": 3,
    "特別賞": 4,
    "最優秀賞": 0,
    "優勝": 0,
    "準優勝": 1,
    "優秀賞": 1,
    "3位": 2,
}


def extract_data_group(js_path: Path) -> list[dict]:
    txt = js_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"dataGroup\s*=\s*\[", txt)
    if not m:
        raise RuntimeError(f"Could not find dataGroup array in {js_path}")
    start = m.end() - 1
    depth = 0
    in_str = False
    esc = False
    end = -1
    for i in range(start, len(txt)):
        ch = txt[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
    if end < 0:
        raise RuntimeError(f"Unclosed dataGroup array in {js_path}")
    arr_js = txt[start:end]
    out = subprocess.check_output(
        ["node", "-e", "const arr = eval(require('fs').readFileSync(0,'utf8')); process.stdout.write(JSON.stringify(arr));"],
        input=arr_js,
        text=True,
        encoding="utf-8",
    )
    return json.loads(out)


def expand_school_names(raw_name: str) -> list[str]:
    # Strip trailing group suffixes like "　Ａ", " A", " ①"
    name = clean(raw_name)
    name = re.sub(r"[\s　]+(?:[A-Za-zＡ-Ｚａ-ｚ0-9０-９①-⑩]+|（[^）]*）|\([^)]*\))$", "", name).strip()
    if not name:
        return []
    # Filter obvious non-school orgs (keep 大学附属/大学付属 schools)
    if any(k in name for k in NON_SCHOOL_KEYWORDS):
        if not any(s in name for s in ("小学校", "中学校", "高等学校", "小学部", "中学部", "高等部", "高校")):
            return []
    if not any(k in name for k in SCHOOL_KEYWORDS):
        return []

    # Handle combined "〇〇中学校・高等学校" or "〇〇中学・高等学校" or "〇〇小・中学校"
    m_jh_hs = re.match(r"^(.+?)(?:中学校|中学)[・／/](?:高等学校|高校)$", name)
    if m_jh_hs:
        base = m_jh_hs.group(1)
        return [f"{base}中学校", f"{base}高等学校"]
    m_el_jh = re.match(r"^(.+?)(?:小学校|小学)[・／/](?:中学校|中学)$", name)
    if m_el_jh:
        base = m_el_jh.group(1)
        return [f"{base}小学校", f"{base}中学校"]
    m_all = re.match(r"^(.+?)中等部[・／/]高等部$", name)
    if m_all:
        base = m_all.group(1)
        return [f"{base}中等部", f"{base}高等部"]
    return [name]


def update_html_dropdowns() -> int:
    updated = 0
    for slug in PREF_SLUGS.values():
        p = ROOT / "tools" / "school-database" / slug / "index.html"
        html = p.read_text(encoding="utf-8")
        if CAT in html:
            continue
        html = html.replace(
            "<label>文化部全国大会実績（演劇・書道・将棋・囲碁・箏曲・華道・絵画・ロボット）</label>",
            "<label>文化部・検定全国実績（演劇・書道・将棋・囲碁・箏曲・華道・絵画・ロボット・漢検）</label>",
            1,
        )
        html = html.replace(
            '<option value="ロボット">ロボット</option>',
            '<option value="ロボット">ロボット</option>\n'
            f'                  <option value="{CAT}">{CAT}</option>',
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
    school_candidates = 0
    unmatched: list[tuple[str, str, str]] = []

    for year_str, fname in [("2025年度", "2025.js"), ("2024年度", "2024.js")]:
        rows = extract_data_group(KANKEN_DIR / fname)
        for row in rows:
            pref = norm_pref(str(row.get("group_prefecture") or ""))
            prize = clean(str(row.get("group_prize") or ""))
            raw_name = str(row.get("group_name") or "")
            if not pref or pref not in PREF_SLUGS or not prize:
                continue
            names = expand_school_names(raw_name)
            if not names:
                continue
            slug = PREF_SLUGS[pref]
            for sname in names:
                school_candidates += 1
                idxs = matchers[slug].match(sname)
                if not idxs:
                    alt = re.sub(r"^(?:北海道|東京都|(?:大阪|京都)府|.+?県)立?", "", sname)
                    idxs = matchers[slug].match(alt)
                if idxs:
                    additions[slug][idxs[0]].append({
                        "category": CAT,
                        "contest": "日本漢字能力検定（漢検）準会場 団体表彰",
                        "year": year_str,
                        "division": "団体の部（準会場校）",
                        "award": prize,
                    })
                    matched_cnt += 1
                else:
                    unmatched.append((year_str, pref, sname))

    total_sc = 0
    total_ent = 0
    prefs_with_culture = 0
    newly_added = 0

    for pref_name, slug in PREF_SLUGS.items():
        schools = pref_schools[slug]
        sc_add = additions.get(slug, {})
        changed = False
        p_sc = 0
        for idx, sc in enumerate(schools):
            existing = list(sc.get("culture_awards") or [])
            new_items = sc_add.get(idx, [])
            combined = existing + new_items
            if not combined:
                continue
            deduped = []
            seen = set()
            for e in combined:
                k = (e["category"], e["contest"], e["year"], e["division"], e["award"])
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
                    x["category"],
                )
            )
            sc["culture_awards"] = deduped
            p_sc += 1
            total_sc += 1
            total_ent += len(deduped)
        if p_sc > 0:
            prefs_with_culture += 1
        if changed:
            out_path = DATA_DIR / f"{slug}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(schools, f, ensure_ascii=False, indent=2)
                f.write("\n")

    html_updated = update_html_dropdowns()
    print(f"MATCHED Kanken school records: {matched_cnt}/{school_candidates} (unmatched={len(unmatched)})")
    print(f"TOTAL school DB culture_awards: {prefs_with_culture}/47 prefectures, {total_sc} schools, {total_ent} entries (+{newly_added} new)")
    print(f"Updated HTML dropdowns: {html_updated}/47")
    if unmatched:
        print("Unmatched sample:", unmatched[:12])


if __name__ == "__main__":
    main()
