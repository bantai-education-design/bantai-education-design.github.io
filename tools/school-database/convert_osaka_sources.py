#!/usr/bin/env python3
"""大阪府の公式資料を学校検索用JSONへ変換する。

原本は data-source/osaka/ に置く（Git管理外）。

大阪府教育委員会は、府内市町村立の小学校・中学校・義務教育学校の所在地一覧を
罫線付きPDF（市町村名列はrowspanでページをまたいで結合）として公開しており、
pdfplumberのextract_tables()でそのまま読み取れる。

府立高等学校・府立支援学校は、大阪府庁サイト自体には住所付きの一覧PDFが
存在しないため、大阪府教育委員会が運営する学校検索サイト「ERABO（学校navi）」
（https://www.schoolnavi.osaka-c.ed.jp/school/<ID>）を1件ずつ収集し、
郵便番号・住所・電話番号を抽出した（対象ID 173件、通信制のみの桃谷高等学校は
ERABO未掲載のため学校公式サイトから個別に補完）。

私立小学校・中学校・高等学校は大阪府庁サイトのHTMLページに直接、郵便番号・
住所・電話番号を含むテーブルとして掲載されている（BeautifulSoupで抽出）。

私立幼稚園・認定こども園は罫線付きPDF「大阪府内私立幼稚園等一覧」を
extract_tables()で読み取る。

国立学校（大阪教育大学附属校11校園）は大学公式サイトの記載を直接収録する。
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pdfplumber
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# 正規化ユーティリティ
# ---------------------------------------------------------------------------

def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("\r", "")
    return text.strip()


def normalize_name(value: Any) -> str:
    text = normalize_text(value)
    text = text.replace("\n", "")
    return re.sub(r"[ \t　]+", "", text)


def normalize_kana(value: Any) -> str:
    return normalize_name(value)


def normalize_postal_code(value: Any) -> str:
    if value is None:
        return ""
    digits = re.sub(r"\D", "", str(value))
    if len(digits) == 7:
        return f"{digits[:3]}-{digits[3:]}"
    return ""


def normalize_phone(value: Any) -> str:
    if value is None:
        return ""
    text = normalize_text(value)
    text = text.replace("\n", " / ")
    text = text.replace("‐", "-").replace("−", "-").replace("―", "-").replace("－", "-")
    text = re.sub(r"^\((\d{2,5})\)\s*", r"\1-", text)
    if text in ("", "-"):
        return ""
    return text


def normalize_address(value: Any, *, prefix: str = "") -> str:
    text = normalize_text(value)
    text = text.replace("\n", "")
    text = text.replace("‐", "-").replace("−", "-").replace("－", "-")
    text = re.sub(r"^\d{3}-?\d{4}", "", text).strip()
    text = re.sub(r"^(\S+?[市区町村])\s+", r"\1", text)
    bw = BARE_WARD_RE.match(text)
    if bw and bw.group(1) in OSAKA_CITY_WARDS and not text.startswith("大阪市"):
        text = "大阪市" + text
    if prefix and text and prefix not in text:
        for i in range(len(prefix)):
            if text.startswith(prefix[i:]):
                text = prefix[:i] + text
                break
        else:
            text = prefix + text
    if text and not text.startswith("大阪府"):
        text = "大阪府" + text
    return text


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"[^0-9a-z぀-ヿ一-鿿]+", "-", normalized)
    return normalized.strip("-")


SOURCE_DATE = "2026-05-01"
PREF = "大阪府"
DATA_DIR = Path(__file__).resolve().parents[2] / "data-source" / "osaka"

records: list[dict[str, Any]] = []


def add_record(
    *,
    name: str,
    name_kana: str = "",
    school_type: str,
    establishment: str,
    postal_code: str,
    address: str,
    municipality: str,
    phone: str,
    website: str = "",
    course: list[str] | None = None,
    source_name: str,
    source_url: str,
) -> None:
    name = normalize_name(name)
    if not name:
        return
    records.append({
        "id": "",
        "prefecture": PREF,
        "name": name,
        "name_kana": normalize_kana(name_kana),
        "postal_code": normalize_postal_code(postal_code) if postal_code else "",
        "address": address,
        "municipality": municipality,
        "school_type": school_type,
        "establishment": establishment,
        "operator": "",
        "phone": normalize_phone(phone),
        "website": website,
        "source_name": source_name,
        "source_url": source_url,
        "source_date": SOURCE_DATE,
        "verified_date": "",
        "course": course or [],
    })


# ---------------------------------------------------------------------------
# 学校名の正式名称化
# ---------------------------------------------------------------------------

FULL_NAME_SUFFIXES = (
    "幼稚園", "小学校", "中学校", "義務教育学校", "高等学校", "中等教育学校",
    "特別支援学校", "支援学校", "認定こども園", "学園", "学院",
)

SINGLE_CHAR_SUFFIX = {"小学校": "小", "中学校": "中"}

INSTITUTION_PREFIX_RE = re.compile(r"^(大阪市立|堺市立|市立|町立|村立|府立|国立)")

COURSE_QUALIFIER_RE = re.compile(r"[（(][^（）()]*[）)]\s*$")


def strip_course_qualifier(name: str) -> str:
    return COURSE_QUALIFIER_RE.sub("", name).strip()


def looks_like_official_name(name: str) -> bool:
    return "立" in name and any(name.endswith(s) for s in FULL_NAME_SUFFIXES)


def build_official_name(raw_name: str, school_type: str, establishment: str, municipality: str) -> str:
    """略称のまま収録された学校名を「{設置者}立{校名}{校種}」の正式名称に組み立てる。"""
    if establishment in ("私立", "国立"):
        return normalize_name(raw_name)

    name = strip_course_qualifier(normalize_name(raw_name))
    if looks_like_official_name(name):
        return name

    name = INSTITUTION_PREFIX_RE.sub("", name)
    if municipality and name.startswith(municipality + "立"):
        name = name[len(municipality) + 1:]
    if municipality and name.startswith(municipality):
        name = name[len(municipality):]

    full_suffix = school_type
    suffix = full_suffix
    if name.endswith(full_suffix):
        core = name[: -len(full_suffix)]
    elif name.endswith("分校") or name.endswith("分教室"):
        core = name
        suffix = ""
    else:
        single = SINGLE_CHAR_SUFFIX.get(school_type)
        if single and name.endswith(single):
            core = name[:-1]
        else:
            core = name

    prefix = municipality

    if not core:
        return f"{prefix}立{suffix}" if prefix else suffix

    return f"{prefix}立{core}{suffix}" if prefix else f"{core}{suffix}"


def collapse_repeated_block(name: str) -> str:
    n = len(name)
    for block_len in range(2, n // 2 + 1):
        if name[-block_len:] == name[-2 * block_len: -block_len]:
            return name[:-block_len]
    return name


# ---------------------------------------------------------------------------
# 公立: 小学校・中学校・義務教育学校（extract_tables）
# ---------------------------------------------------------------------------
# 「市町村名」列は大阪市の行では縦書きの見出しとして描画されており
# extract_tables()ではセル値がNoneになる（rowspanの取りこぼしではなく、
# そもそも表のセルとして認識されない）。また堺市・近隣市境界付近では
# 市町村名列のセルが直前ページ末尾の値と結合し誤った市町村名を保持し続ける
# 現象も確認された。そのため市町村名は「市町村名」列を使わず、所在地
# （住所）列の先頭から都度抽出する方式に統一する。

MUNI_FROM_ADDR_RE = re.compile(
    r"^(?:大阪府)?(?:[^\d市]+?郡)?(大阪市\S+?区|堺市\S+?区|\S+?[市町村])"
)

# 「生野区生野西3-5-40」のように大阪市が省略され区名から始まる住所を補完する。
BARE_WARD_RE = re.compile(r"^([^\d]+?区)\S")
OSAKA_CITY_WARDS = {
    "中央区", "北区", "都島区", "福島区", "此花区", "西区", "港区", "大正区",
    "天王寺区", "浪速区", "西淀川区", "淀川区", "東淀川区", "東成区", "生野区",
    "旭区", "城東区", "阿倍野区", "住吉区", "東住吉区", "西成区", "住之江区",
    "鶴見区", "平野区",
}


def _municipality_from_address(addr: str) -> str:
    m = MUNI_FROM_ADDR_RE.match(addr)
    return m.group(1) if m else ""


def _city_for_naming(muni: str) -> str:
    """大阪市・堺市は区ではなく市が設置者（正式名称は「大阪市立」であり
    「大阪市○○区立」ではない）ため、正式名称組み立て時は区を除いた市名を使う。"""
    m = re.match(r"^(大阪市|堺市)", muni)
    return m.group(1) if m else muni


def _parse_public_table(path: Path, school_type: str, source_label: str) -> None:
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 6:
                        continue
                    _muni_cell, num_cell, name_cell, postal_cell, addr_cell, phone_cell = row[:6]
                    if not num_cell or not num_cell.strip().isdigit():
                        continue
                    name = normalize_name(name_cell)
                    if not name:
                        continue
                    postal = normalize_postal_code((postal_cell or "").split("\n")[0])
                    addr = normalize_address((addr_cell or "").split("\n")[0])
                    muni = _municipality_from_address(addr)
                    phone_lines = [normalize_phone(p) for p in (phone_cell or "").split("\n") if p.strip()]
                    phone = " / ".join(dict.fromkeys(p for p in phone_lines if p))
                    official = build_official_name(name, school_type, "公立", _city_for_naming(muni))
                    add_record(
                        name=official,
                        school_type=school_type,
                        establishment="公立",
                        postal_code=postal,
                        address=addr,
                        municipality=muni,
                        phone=phone,
                        source_name=source_label,
                        source_url="https://www.pref.osaka.lg.jp/o180080/shochugakko/jyuusho/index.html",
                    )


def parse_public_elem() -> None:
    _parse_public_table(DATA_DIR / "public_shou.pdf", "小学校", "大阪府 公立小学校所在地一覧")


def parse_public_jhs() -> None:
    _parse_public_table(DATA_DIR / "public_chu.pdf", "中学校", "大阪府 公立中学校所在地一覧")


def parse_public_gimu() -> None:
    _parse_public_table(DATA_DIR / "public_gimu.pdf", "義務教育学校", "大阪府 公立義務教育学校所在地一覧")


# ---------------------------------------------------------------------------
# 公立: 高等学校・支援学校（ERABO学校naviの個別ページから収集済みのTSVを読み込む）
# ---------------------------------------------------------------------------

def parse_public_koukou_shien() -> None:
    path = DATA_DIR / "schoolnavi_master.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split("\t")
        row = dict(zip(header, cols))
        name = normalize_name(row.get("name", ""))
        if not name:
            continue
        school_type = "特別支援学校" if "支援学校" in name else "高等学校"
        muni = _municipality_from_address(row.get("address", ""))
        course = [row["course"]] if row.get("course") else []
        add_record(
            name=name,
            name_kana=row.get("kana", ""),
            school_type=school_type,
            establishment="公立",
            postal_code=row.get("postal", ""),
            address=normalize_address(row.get("address", "")),
            municipality=muni,
            phone=row.get("phone", ""),
            course=course,
            source_name="大阪府 ERABO（大阪府立高等学校・支援学校検索サイト）",
            source_url="https://www.schoolnavi.osaka-c.ed.jp/",
        )

    # ERABOに掲載のない通信制単独校を個別に補完
    add_record(
        name="大阪府立桃谷高等学校",
        school_type="高等学校",
        establishment="公立",
        postal_code="544-0021",
        address=normalize_address("大阪市生野区勝山南3-1-4"),
        municipality="大阪市生野区",
        phone="06-6712-0371",
        course=["通信制"],
        source_name="大阪府立桃谷高等学校 公式サイト",
        source_url="https://www.osaka-c.ed.jp/momodani/",
    )


# ---------------------------------------------------------------------------
# 私立: 小学校・中学校・高等学校（大阪府庁サイトのHTMLテーブル）
# ---------------------------------------------------------------------------

def _muni_from_address(addr: str) -> str:
    return _municipality_from_address(addr)


def _parse_private_html_table(path: Path, school_type: str, source_label: str, source_url: str) -> None:
    with open(path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header = [c.get_text(strip=True) for c in rows[0].find_all(["td", "th"])]
        if not header or header[0] != "学校名":
            continue
        for tr in rows[1:]:
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) < 4:
                continue
            raw_name, postal, addr, phone = cells[0], cells[1], cells[2], cells[3]
            name = normalize_name(raw_name)
            if not name:
                continue
            full_name = name if name.endswith(school_type) else name + school_type
            full_addr = normalize_address(addr)
            add_record(
                name=full_name,
                school_type=school_type,
                establishment="私立",
                postal_code=postal,
                address=full_addr,
                municipality=_muni_from_address(full_addr),
                phone=phone,
                source_name=source_label,
                source_url=source_url,
            )


def parse_private_elem() -> None:
    _parse_private_html_table(
        DATA_DIR / "private_shou.html", "小学校",
        "大阪府 私立小学校の一覧",
        "https://www.pref.osaka.lg.jp/o180160/shigaku/syoutyuukou/itiran-syou.html",
    )


def parse_private_jhs() -> None:
    _parse_private_html_table(
        DATA_DIR / "private_chu.html", "中学校",
        "大阪府 私立中学校の一覧",
        "https://www.pref.osaka.lg.jp/o180160/shigaku/syoutyuukou/itiran-chugaku.html",
    )


def parse_private_koukou() -> None:
    path = DATA_DIR / "private_koukou.html"
    with open(path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    tables = soup.find_all("table")
    # table0は集計表。table1-3が全日制（男子/女子/共学）、table4-5が通信制。
    zenjitsu_idx = {1, 2, 3}
    for i, table in enumerate(tables):
        rows = table.find_all("tr")
        if not rows:
            continue
        header = [c.get_text(strip=True) for c in rows[0].find_all(["td", "th"])]
        if not header or header[0] != "学校名":
            continue
        course = "全日制" if i in zenjitsu_idx else "通信制"
        for tr in rows[1:]:
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) < 4:
                continue
            raw_name, postal, addr, phone = cells[0], cells[1], cells[2], cells[3]
            name = normalize_name(raw_name)
            if not name:
                continue
            full_name = name if name.endswith("高等学校") else name + "高等学校"
            full_addr = normalize_address(addr)
            add_record(
                name=full_name,
                school_type="高等学校",
                establishment="私立",
                postal_code=postal,
                address=full_addr,
                municipality=_muni_from_address(full_addr),
                phone=phone,
                course=[course],
                source_name="大阪府 私立高等学校の一覧",
                source_url="https://www.pref.osaka.lg.jp/o180160/shigaku/syoutyuukou/itiran-koukou.html",
            )


# ---------------------------------------------------------------------------
# 私立: 幼稚園・認定こども園（extract_tables）
# ---------------------------------------------------------------------------

YOCHIEN_CATEGORY_TYPE = {
    "私学助成": "幼稚園",
    "施設型給付": "幼稚園",
    "幼稚園型": "幼保連携型認定こども園",
}

# 名前セルに「幼稚園型認定こども園」「認定こども園」のような類型ラベルが
# 誤って連結されている場合があるため、先頭から取り除く。
YOCHIEN_LABEL_PREFIX_RE = re.compile(r"^(幼稚園型認定こども園|認定こども園)")


def parse_private_youchien() -> None:
    path = DATA_DIR / "youchienmeibo2026_1.pdf"
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 11:
                        continue
                    manage_no, category = row[0], row[1]
                    if not manage_no or not re.match(r"^\d{2}-\d{2}-\d{3}$", manage_no.strip()):
                        continue
                    name_cell, kana_cell = row[2], row[3]
                    postal_cell, addr_cell, phone_cell = row[4], row[5], row[6]
                    muni_cell = row[10] if len(row) > 10 else ""
                    school_type = YOCHIEN_CATEGORY_TYPE.get((category or "").strip(), "幼稚園")
                    raw_name = normalize_name(name_cell)
                    raw_name = YOCHIEN_LABEL_PREFIX_RE.sub("", raw_name)
                    if not raw_name:
                        continue
                    suffix = "こども園" if school_type == "幼保連携型認定こども園" and "こども園" in raw_name else (
                        "幼稚園" if school_type == "幼稚園" else ""
                    )
                    if suffix and not raw_name.endswith(("幼稚園", "こども園", "園")):
                        raw_name = raw_name + suffix
                    muni_raw = normalize_text(muni_cell)
                    full_addr = normalize_address(addr_cell, prefix=muni_raw)
                    muni = _municipality_from_address(full_addr) or muni_raw
                    add_record(
                        name=raw_name,
                        name_kana=kana_cell,
                        school_type=school_type,
                        establishment="私立",
                        postal_code=postal_cell,
                        address=full_addr,
                        municipality=muni,
                        phone=phone_cell,
                        source_name="大阪府 私立幼稚園及び私立幼稚園型認定こども園一覧",
                        source_url="https://www.pref.osaka.lg.jp/o180160/shigaku/youchien/youchienichiran.html",
                    )


# ---------------------------------------------------------------------------
# 国立学校: 大阪教育大学附属学校園（大学公式サイト記載）
# ---------------------------------------------------------------------------

def parse_national() -> None:
    path = DATA_DIR / "national_schools.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split("\t")
        row = dict(zip(header, cols))
        addr = normalize_address(row.get("住所", ""))
        add_record(
            name=row.get("学校名", ""),
            school_type=row.get("学校種", ""),
            establishment="国立",
            postal_code=row.get("郵便番号", ""),
            address=addr,
            municipality=_muni_from_address(addr),
            phone=row.get("電話番号", ""),
            source_name="大阪教育大学 附属学校園",
            source_url="https://osaka-kyoiku.ac.jp/university/center/school/",
        )


# ---------------------------------------------------------------------------
# クリーニング・重複除去
# ---------------------------------------------------------------------------

ALLOWED_SCHOOL_TYPES = {
    "幼稚園", "幼保連携型認定こども園", "小学校", "中学校", "義務教育学校",
    "高等学校", "中等教育学校", "特別支援学校",
}

BARE_TYPE_NAMES = {"幼稚園", "小学校", "中学校", "高等学校", "特別支援学校"}


def clean_records() -> None:
    cleaned = []
    for rec in records:
        if rec["school_type"] not in ALLOWED_SCHOOL_TYPES:
            continue
        if rec["establishment"] not in ("公立", "私立", "国立"):
            continue
        if rec["name"] in BARE_TYPE_NAMES:
            continue
        if not rec["postal_code"]:
            continue
        if len(rec["address"]) < 6:
            continue
        cleaned.append(rec)
    records.clear()
    records.extend(cleaned)
    for rec in records:
        rec["name"] = collapse_repeated_block(rec["name"])


def dedup_and_assign_ids() -> list[dict[str, Any]]:
    seen: dict[tuple, dict[str, Any]] = {}
    for rec in records:
        key = (rec["name"], rec["address"], rec["phone"])
        if key in seen:
            continue
        seen[key] = rec
    result = list(seen.values())
    counts: dict[str, int] = {}
    for rec in result:
        base = slug(f"osaka-{rec['establishment']}-{rec['school_type']}-{rec['municipality']}-{rec['name']}")
        counts[base] = counts.get(base, 0) + 1
        rec["id"] = base if counts[base] == 1 else f"{base}-{counts[base]}"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "data" / "school-database" / "osaka.json"))
    args = parser.parse_args()

    parse_public_elem()
    parse_public_jhs()
    parse_public_gimu()
    parse_public_koukou_shien()
    parse_private_elem()
    parse_private_jhs()
    parse_private_koukou()
    parse_private_youchien()
    parse_national()

    clean_records()
    result = dedup_and_assign_ids()
    result.sort(key=lambda r: (r["municipality"], r["school_type"], r["name"]))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(result)} records to {out_path}")


if __name__ == "__main__":
    main()
