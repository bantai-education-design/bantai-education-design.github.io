#!/usr/bin/env python3
"""Parse MEXT FY2026 national official research school PDFs into a per-prefecture JSON cache:
1. 令和8年度 高等学校DX加速化推進事業（DXハイスクール）採択校一覧 (1,249 schools)
2. 教育課程柔軟化サキドリ研究校指定一覧（令和8年7月現在）
3. 令和8年度 スーパーサイエンスハイスクール（SSH）内定校一覧
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

CACHE_DIR = Path(
    r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\national_and_tohoku"
)
OUT_JSON = CACHE_DIR / "mext_r8_national_parsed.json"

PREF_SLUGS = {
    "北海道": "hokkaido", "青森県": "aomori", "岩手県": "iwate", "宮城県": "miyagi",
    "秋田県": "akita", "山形県": "yamagata", "福島県": "fukushima",
    "茨城県": "ibaraki", "栃木県": "tochigi", "群馬県": "gunma", "埼玉県": "saitama",
    "千葉県": "chiba", "東京都": "tokyo", "神奈川県": "kanagawa",
    "新潟県": "niigata", "富山県": "toyama", "石川県": "ishikawa", "福井県": "fukui",
    "山梨県": "yamanashi", "長野県": "nagano", "岐阜県": "gifu", "静岡県": "shizuoka", "愛知県": "aichi",
    "三重県": "mie", "滋賀県": "shiga", "京都府": "kyoto", "大阪府": "osaka",
    "兵庫県": "hyogo", "奈良県": "nara", "和歌山県": "wakayama",
    "鳥取県": "tottori", "島根県": "shimane", "岡山県": "okayama", "広島県": "hiroshima", "山口県": "yamaguchi",
    "徳島県": "tokushima", "香川県": "kagawa", "愛媛県": "ehime", "高知県": "kochi",
    "福岡県": "fukuoka", "佐賀県": "saga", "長崎県": "nagasaki", "熊本県": "kumamoto",
    "大分県": "oita", "宮崎県": "miyazaki", "鹿児島県": "kagoshima", "沖縄県": "okinawa",
}

DESIGNATED_CITY_TO_PREF = {
    "札幌市": "北海道", "仙台市": "宮城県", "さいたま市": "埼玉県", "千葉市": "千葉県",
    "横浜市": "神奈川県", "川崎市": "神奈川県", "相模原市": "神奈川県", "新潟市": "新潟県",
    "静岡市": "静岡県", "浜松市": "静岡県", "名古屋市": "愛知県", "京都市": "京都府",
    "大阪市": "大阪府", "堺市": "大阪府", "神戸市": "兵庫県", "岡山市": "岡山県",
    "広島市": "広島県", "北九州市": "福岡県", "福岡市": "福岡県", "熊本市": "熊本県",
}


def clean(val: object) -> str:
    if val is None:
        return ""
    s = unicodedata.normalize("NFKC", str(val))
    return re.sub(r"\s+", " ", s).strip()


def norm_pref(raw: str) -> str:
    s = clean(raw).replace(" ", "")
    s = re.sub(r"^\d{2}", "", s)
    if s in PREF_SLUGS:
        return s
    for p in PREF_SLUGS:
        if p.startswith(s) and len(s) >= 2:
            return p
    return ""


def parse_all() -> dict[str, list[dict]]:
    by_slug: dict[str, list[dict]] = defaultdict(list)

    # 1. DX High School (FY2026)
    dx_cnt = 0
    with pdfplumber.open(CACHE_DIR / "mext_dx_r8.pdf") as pdf:
        for page in pdf.pages[1:]:
            for t in page.extract_tables():
                for row in t:
                    if not row or len(row) < 5:
                        continue
                    pref = norm_pref(row[0])
                    if not pref:
                        continue
                    sname = clean(row[3]).replace(" ", "")
                    status = clean(row[4]).replace(" ", "")
                    if not sname or sname == "学校名" or sname.isdigit():
                        continue
                    yr = "令和6〜8" if "3年目" in status else ("令和7〜8" if "2年目" in status else "令和8")
                    by_slug[PREF_SLUGS[pref]].append({
                        "school_name": sname,
                        "muni_hint": "",
                        "year": yr,
                        "subject": "情報・数学・DX探究",
                        "designation": "高等学校DX加速化推進事業（DXハイスクール）",
                        "authority": "文部科学省",
                    })
                    dx_cnt += 1

    # 2. 教育課程柔軟化サキドリ研究校 (FY2026)
    saki_cnt = 0
    with pdfplumber.open(CACHE_DIR / "mext_sakidori_r8.pdf") as pdf:
        cur_pref = ""
        for page in pdf.pages:
            for t in page.extract_tables():
                for row in t:
                    if not row or len(row) < 3:
                        continue
                    p_cand = norm_pref(row[0])
                    if p_cand:
                        cur_pref = p_cand
                    org = clean(row[1]).replace(" ", "")
                    sname = clean(row[2]).replace(" ", "")
                    if not sname or sname in ("指定学校名", "学校名") or sname.isdigit():
                        continue
                    # Override prefecture when row belongs to a designated city (政令指定都市)
                    row_pref = cur_pref
                    for city_name, city_pref in DESIGNATED_CITY_TO_PREF.items():
                        if city_name in org or sname.startswith(city_name):
                            row_pref = city_pref
                            break
                    if not row_pref:
                        continue
                    muni_hint = org.replace("教育委員会", "")
                    if muni_hint in ("", row_pref) or muni_hint.endswith(("県", "府", "都", "道")):
                        muni_hint = ""
                    by_slug[PREF_SLUGS[row_pref]].append({
                        "school_name": sname,
                        "muni_hint": muni_hint,
                        "year": "令和8〜9",
                        "subject": "調整授業時数・教育課程柔軟化",
                        "designation": "教育課程柔軟化サキドリ研究校事業",
                        "authority": "文部科学省",
                    })
                    saki_cnt += 1

    # 3. JST SSH all active schools (230 schools nationwide)
    ssh_cnt = 0
    jst_html_path = Path(
        r"C:\Users\User\.gemini\antigravity\brain\d33ccb9c-6d5b-43b8-ad87-7b7acc4093e6\scratch\chubu_research\jst_ssh.html"
    )
    if jst_html_path.exists():
        jhtml = jst_html_path.read_text(encoding="utf-8")
        card_pat = re.compile(
            r'<p class="pre-txt">都道府県：<span>([^<]+)</span></p>.*?'
            r'<p class="school-name">(?:<a[^>]*>)?([^<]+)(?:</a>)?</p>.*?'
            r'<span class="rect">指定年度</span><span>([^<]+)</span>.*?'
            r'<span class="rect">分類</span><span>([^<]+)</span>',
            re.S,
        )
        for m in card_pat.finditer(jhtml):
            pref = norm_pref(m.group(1))
            sname = clean(m.group(2)).replace(" ", "")
            yr_raw = clean(m.group(3)).replace("年度", "")
            cls_raw = clean(m.group(4))
            if not pref or not sname:
                continue
            by_slug[PREF_SLUGS[pref]].append({
                "school_name": sname,
                "muni_hint": "",
                "year": yr_raw,
                "subject": "理数・科学技術",
                "designation": f"スーパーサイエンスハイスクール（SSH・{cls_raw}）" if cls_raw else "スーパーサイエンスハイスクール（SSH）",
                "authority": "文部科学省",
            })
            ssh_cnt += 1
    else:
        with pdfplumber.open(CACHE_DIR / "mext_ssh_r8.pdf") as pdf:
            for page in pdf.pages:
                for t in page.extract_tables():
                    for row in t:
                        if not row or len(row) < 3:
                            continue
                        no = clean(row[0])
                        if not no.isdigit():
                            continue
                        pref = norm_pref(row[1])
                        if not pref:
                            continue
                        sname = clean(row[2]).replace(" ", "")
                        if not sname:
                            continue
                        by_slug[PREF_SLUGS[pref]].append({
                            "school_name": sname,
                            "muni_hint": "",
                            "year": "令和8〜12",
                            "subject": "理数・科学技術",
                            "designation": "スーパーサイエンスハイスクール（SSH）",
                            "authority": "文部科学省",
                        })
                        ssh_cnt += 1

    OUT_JSON.write_text(json.dumps(by_slug, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Parsed MEXT national R8: DX={dx_cnt}, Sakidori={saki_cnt}, SSH_R8={ssh_cnt}, prefectures={len(by_slug)}")
    return by_slug


if __name__ == "__main__":
    parse_all()
