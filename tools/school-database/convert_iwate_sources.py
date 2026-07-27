#!/usr/bin/env python3
"""岩手県の公式PDF名簿を学校検索用JSONへ変換する。

原本は data-source/iwate/ に置く（Git管理外）。

岩手県教育委員会は、県立・市町村立の幼稚園・小学校・中学校・義務教育学校・
高等学校・特別支援学校をまとめた単一のPDF「学校一覧」（統計編+学校一覧編）
を公開している。学校一覧編は罫線のない統計表形式のため、pdfplumberの
extract_text()で1行1校のテキストとして読み取り、正規表現で学校名・かな・
郵便番号・住所・電話番号を抽出する。

私立学校（幼稚園・中学校・高等学校・特別支援学校）は別のPDF「私立学校一覧」
に掲載され、こちらは罫線表のためextract_tables()で読み取る。

特別支援学校（県立）は元のPDFが幼稚部/小学部/中学部/高等部が別行に分かれる
複雑な表形式のため、目視で書き起こしたTSVを使用する。

国立学校（岩手大学教育学部附属校）は大学公式サイトの記載を直接収録する。
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pdfplumber


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
    text = text.replace("\n", "")
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
    if prefix and text and prefix not in text:
        for i in range(len(prefix)):
            if text.startswith(prefix[i:]):
                text = prefix[:i] + text
                break
        else:
            text = prefix + text
    if text and not text.startswith("岩手県"):
        text = "岩手県" + text
    return text


MUNI_FROM_ADDR_RE = re.compile(r"(?:岩手県)?(?:[^\d市]+郡)?([^\d]+?[市町村])")


def municipality_from_address(addr: str) -> str:
    """住所から市町村名を取り出す（「紫波郡矢巾町」のような郡名混入を除去）。"""
    m = MUNI_FROM_ADDR_RE.match(addr)
    return m.group(1) if m else ""


def strip_gun_prefix(muni: str, addr: str) -> str:
    """PDFの郡市名列が「上閉伊郡」のような郡名のままの場合、住所から実際の市町村名に補正する。"""
    if muni.endswith("郡"):
        from_addr = municipality_from_address(addr)
        if from_addr:
            return from_addr
    return muni


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"[^0-9a-z぀-ヿ一-鿿]+", "-", normalized)
    return normalized.strip("-")


SOURCE_DATE = "2026-05-01"
PREF = "岩手県"
DATA_DIR = Path(__file__).resolve().parents[2] / "data-source" / "iwate"

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
# 学校名の正式名称化（北海道版で確立したロジックを流用）
# ---------------------------------------------------------------------------

FULL_NAME_SUFFIXES = (
    "幼稚園", "小学校", "中学校", "義務教育学校", "高等学校", "中等教育学校",
    "特別支援学校", "認定こども園", "学園", "学院",
)

SINGLE_CHAR_SUFFIX = {"小学校": "小", "中学校": "中"}

INSTITUTION_PREFIX_RE = re.compile(r"^(市立|町立|村立|県立|国立)")

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
        name = name[len(municipality) + 1 :]

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

    if school_type == "高等学校":
        prefix = "岩手県" if establishment == "県立" else municipality
    else:
        prefix = municipality

    if not core:
        return f"{prefix}立{suffix}" if prefix else suffix

    return f"{prefix}立{core}{suffix}" if prefix else f"{core}{suffix}"


def collapse_repeated_block(name: str) -> str:
    n = len(name)
    for block_len in range(2, n // 2 + 1):
        if name[-block_len:] == name[-2 * block_len : -block_len]:
            return name[:-block_len]
    return name


# ---------------------------------------------------------------------------
# 公立: 幼稚園（市町村立）・小中学校・義務教育学校 （学校一覧編、extract_text）
# ---------------------------------------------------------------------------

PHONE_TAIL_RE = re.compile(r"\(\d{2,4}\)\s*\d{2,4}-\d{3,4}\s*$")
ADDR_PHONE_RE = re.compile(
    r"(?P<postal>\d{3}-\d{4})(?P<addr>[^\d]+?[^\s].*?)\s*(?P<phone>\(\d{2,4}\)\s*\d{2,4}-\d{3,4})\s*$"
)
NAME_KANA_RE = re.compile(
    r"^(?P<name>(?:[一-龥ー々](?:\s|(?=[一-龥ー々])))*[一-龥ー々])\s+"
    r"(?P<kana>(?:[ぁ-んー](?:\s|(?=[ぁ-んー])))*[ぁ-んー])\s+(?P<rest>.*)$"
)

MUNI_LINE_RE = re.compile(r"^([^\s]+?[市町村])$")
TYPE_TAG_RE = re.compile(r"^<(小学校|中学校|義務教育学校)>")


def parse_public_elem_jhs_kindergarten() -> None:
    path = DATA_DIR / "public_ichiran.pdf"
    with pdfplumber.open(path) as pdf:
        # 幼稚園（市町村立） p.20-... / 小・中・義務教育学校 p.21-30 相当
        _parse_kindergarten_pages(pdf, range(20, 21))
        _parse_elem_jhs_pages(pdf, range(21, 34))


def _parse_kindergarten_pages(pdf, page_range) -> None:
    current_muni = ""
    for i in page_range:
        if i >= len(pdf.pages):
            break
        text = pdf.pages[i].extract_text() or ""
        for raw_line in text.split("\n"):
            line = normalize_text(raw_line)
            if not line or "幼稚園" in line[:6] and "在" in line:
                continue
            m = ADDR_PHONE_RE.search(line)
            if not m:
                muni_m = MUNI_LINE_RE.match(line)
                if muni_m:
                    current_muni = muni_m.group(1)
                continue
            head = line[: m.start()].strip()
            # head 例: "太 田 3 7 3 2 2 4 2 1 1" のように 園名(漢字/かな混在) + 数字列
            name_m = re.match(r"^((?:[^\d\s]\s)*[^\d\s])\s+[\d\s]+$", head)
            if not name_m:
                continue
            raw_name = name_m.group(1).replace(" ", "")
            if not raw_name or raw_name in ("学校法人",):
                continue
            postal = m.group("postal")
            addr = m.group("addr").strip()
            phone = m.group("phone")
            # 「盛岡市」のように市町村名が住所側にすでに含まれるため、
            # current_muniが無くても住所から補完可能。
            muni_guess = current_muni
            m2 = re.match(r"^([^\d]+?[市町村])", addr)
            if m2:
                muni_guess = m2.group(1)
            # 市町村が変わる行では「市町村名」列の文字列が園名の直前に連結されて
            # 抽出されてしまう（例:「盛岡市太田」）ため、先頭の市町村名を除去する。
            if muni_guess and raw_name.startswith(muni_guess):
                raw_name = raw_name[len(muni_guess):]
            official = build_official_name(raw_name, "幼稚園", "公立", muni_guess)
            add_record(
                name=official,
                school_type="幼稚園",
                establishment="公立",
                postal_code=postal,
                address=normalize_address(addr, prefix=muni_guess),
                municipality=muni_guess,
                phone=phone,
                source_name="岩手県教育委員会 学校一覧（幼稚園）",
                source_url="https://www.pref.iwate.jp/kyouikubunka/kyouiku/ippan/toukei/1006311.html",
            )


ESTABLISHMENT_HEADER_RE = re.compile(r"^(県立|市町村立)$")


def _parse_elem_jhs_pages(pdf, page_range) -> None:
    current_muni = ""
    current_type = "小学校"
    current_est = "公立"
    for i in page_range:
        if i >= len(pdf.pages):
            break
        text = pdf.pages[i].extract_text() or ""
        if "小・中・義務教育学校" not in text and i > 21:
            # 高校セクションに入ったら終了
            if "高等学校" in text.split("\n")[0]:
                break
        for raw_line in text.split("\n"):
            line = normalize_text(raw_line)
            if not line:
                continue
            if ESTABLISHMENT_HEADER_RE.match(line):
                current_est = "県立" if line == "県立" else "公立"
                continue
            type_m = TYPE_TAG_RE.match(line)
            if type_m:
                current_type = type_m.group(1)
                continue
            muni_m = MUNI_LINE_RE.match(line)
            if muni_m and "立" not in line:
                current_muni = muni_m.group(1)
                current_est = "公立"
                continue
            m = ADDR_PHONE_RE.search(line)
            if not m:
                continue
            head = line[: m.start()].strip()
            nm = NAME_KANA_RE.match(head)
            if not nm:
                continue
            raw_name = nm.group("name").replace(" ", "")
            postal = m.group("postal")
            addr = m.group("addr").strip()
            phone = m.group("phone")
            muni_guess = current_muni
            m2 = re.match(r"^([^\d]+?[市町村])", addr)
            if m2:
                muni_guess = m2.group(1)
            establishment = current_est
            official = build_official_name(raw_name, current_type, establishment, muni_guess)
            add_record(
                name=official,
                name_kana=nm.group("kana"),
                school_type=current_type,
                establishment=establishment,
                postal_code=postal,
                address=normalize_address(addr, prefix=muni_guess),
                municipality=muni_guess,
                phone=phone,
                source_name="岩手県教育委員会 学校一覧（小・中・義務教育学校）",
                source_url="https://www.pref.iwate.jp/kyouikubunka/kyouiku/ippan/toukei/1006311.html",
            )


# ---------------------------------------------------------------------------
# 公立高等学校（県立・市立）
# ---------------------------------------------------------------------------

def parse_public_koukou() -> None:
    path = DATA_DIR / "public_ichiran.pdf"
    with pdfplumber.open(path) as pdf:
        current_est = "県立"
        for i in range(34, 39):
            if i >= len(pdf.pages):
                break
            text = pdf.pages[i].extract_text() or ""
            if "高等学校" not in text.split("\n")[0]:
                continue
            for raw_line in text.split("\n"):
                line = normalize_text(raw_line)
                if not line:
                    continue
                if line in ("県立", "市立"):
                    current_est = line
                    continue
                m = ADDR_PHONE_RE.search(line)
                if not m:
                    continue
                head = line[: m.start()].strip()
                # 高校の行は「学校名(全角スペースなし)全日制/定時制/通信制...」の形式。
                # 課程マーカーの直前までを学校名とする。分校名の「（○○）」は除去する。
                name_m = re.match(r"^(?P<name>\S+?)\s*(?:全日制|定時制|通信制)", head)
                if not name_m:
                    continue
                raw_name = name_m.group("name")
                raw_name = re.sub(r"^[（(][^（）()]*[）)]", "", raw_name).strip()
                if not raw_name:
                    continue
                postal = m.group("postal")
                addr = m.group("addr").strip()
                phone = m.group("phone")
                muni_guess = ""
                m2 = re.match(r"^([^\d]+?[市町村])", addr)
                if m2:
                    muni_guess = m2.group(1)
                official = build_official_name(raw_name, "高等学校", current_est, muni_guess)
                add_record(
                    name=official,
                    school_type="高等学校",
                    establishment="公立" if current_est else "公立",
                    postal_code=postal,
                    address=normalize_address(addr, prefix=muni_guess),
                    municipality=muni_guess,
                    phone=phone,
                    source_name="岩手県教育委員会 学校一覧（高等学校）",
                    source_url="https://www.pref.iwate.jp/kyouikubunka/kyouiku/ippan/toukei/1006311.html",
                )


# ---------------------------------------------------------------------------
# 特別支援学校（県立、目視書き起こしTSV）
# ---------------------------------------------------------------------------

def parse_tokushi() -> None:
    path = DATA_DIR / "tokushi_transcribed.tsv"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split("\t")
        row = dict(zip(header, cols))
        muni = municipality_from_address(row.get("所在地", ""))
        add_record(
            name=row.get("学校名", ""),
            school_type="特別支援学校",
            establishment="公立",
            postal_code=row.get("郵便番号", ""),
            address=normalize_address(row.get("所在地", "")),
            municipality=muni,
            phone=row.get("電話番号", ""),
            source_name="岩手県教育委員会 学校一覧（特別支援学校）",
            source_url="https://www.pref.iwate.jp/kyouikubunka/kyouiku/ippan/toukei/1006311.html",
        )


# ---------------------------------------------------------------------------
# 私立学校（幼稚園・中学校・高等学校）extract_tables
# ---------------------------------------------------------------------------

def _join_multiline(cell: str | None) -> str:
    if not cell:
        return ""
    return normalize_text(cell).replace("\n", "")


def parse_private_yochien() -> None:
    path = DATA_DIR / "private_all.pdf"
    with pdfplumber.open(path) as pdf:
        current_muni = ""
        for i in range(4, 8):
            if i >= len(pdf.pages):
                break
            page = pdf.pages[i]
            if "中 学 校" in (page.extract_text() or "")[:200]:
                break
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 9:
                        continue
                    muni_cell, num_cell, name_cell, kind_cell = row[0], row[1], row[2], row[3]
                    addr_cell, postal_cell, phone_cell = row[5], row[6], row[7]
                    if muni_cell:
                        m = re.sub(r"\s+", "", muni_cell)
                        if m:
                            current_muni = m
                    name = normalize_name(name_cell)
                    if not name or not num_cell:
                        continue
                    postal = normalize_postal_code((postal_cell or "").replace("‐", ""))
                    addr = _join_multiline(addr_cell)
                    phone = (_join_multiline(phone_cell).split("019")[0] or _join_multiline(phone_cell))
                    phone_lines = (phone_cell or "").split("\n")
                    phone = normalize_phone(phone_lines[0]) if phone_lines else ""
                    if "休園中" in "".join(str(c) for c in row):
                        continue
                    school_type = "幼保連携型認定こども園" if kind_cell and "こども園" in kind_cell else "幼稚園"
                    final_address = normalize_address(addr, prefix=current_muni)
                    add_record(
                        name=name if any(name.endswith(s) for s in ("幼稚園", "こども園")) else name + "幼稚園",
                        school_type=school_type,
                        establishment="私立",
                        postal_code=postal,
                        address=final_address,
                        municipality=strip_gun_prefix(current_muni, final_address),
                        phone=phone,
                        source_name="岩手県私立学校一覧（幼稚園）",
                        source_url="https://www.pref.iwate.jp/kyouikubunka/kyouiku/shigaku/1006747/1006748.html",
                    )


def _parse_private_school_table(page_range, school_type: str, source_label: str) -> None:
    path = DATA_DIR / "private_all.pdf"
    with pdfplumber.open(path) as pdf:
        current_muni = ""
        for i in page_range:
            if i >= len(pdf.pages):
                break
            page = pdf.pages[i]
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 8:
                        continue
                    muni_cell, num_cell, name_cell = row[0], row[1], row[2]
                    addr_cell = row[3] if len(row) > 3 else ""
                    postal_cell = row[4] if len(row) > 4 else ""
                    phone_cell = row[5] if len(row) > 5 else ""
                    if muni_cell:
                        m = re.sub(r"\s+", "", muni_cell)
                        if m:
                            current_muni = m
                    name = normalize_name(name_cell)
                    if not name or not num_cell:
                        continue
                    postal = normalize_postal_code((postal_cell or "").replace("‐", ""))
                    addr = _join_multiline(addr_cell)
                    phone_lines = (phone_cell or "").split("\n")
                    phone = normalize_phone(phone_lines[0]) if phone_lines else ""
                    full_name = name if name.endswith(school_type) else name + school_type
                    final_address = normalize_address(addr, prefix=current_muni)
                    add_record(
                        name=full_name,
                        school_type=school_type,
                        establishment="私立",
                        postal_code=postal,
                        address=final_address,
                        municipality=strip_gun_prefix(current_muni, final_address),
                        phone=phone,
                        source_name=source_label,
                        source_url="https://www.pref.iwate.jp/kyouikubunka/kyouiku/shigaku/1006747/1006748.html",
                    )


def parse_private_chu() -> None:
    _parse_private_school_table(range(8, 9), "中学校", "岩手県私立学校一覧（中学校）")


def parse_private_koukou() -> None:
    _parse_private_school_table(range(9, 12), "高等学校", "岩手県私立学校一覧（高等学校）")


# ---------------------------------------------------------------------------
# 国立学校: 岩手大学教育学部附属校（大学公式サイト記載）
# ---------------------------------------------------------------------------

NATIONAL_SCHOOLS = [
    ("岩手大学教育学部附属幼稚園", "020-0807", "盛岡市加賀野三丁目9番1号", "盛岡市", "019-622-4691", "幼稚園"),
    ("岩手大学教育学部附属小学校", "020-0807", "盛岡市加賀野二丁目6番1号", "盛岡市", "019-623-7275", "小学校"),
    ("岩手大学教育学部附属中学校", "020-0807", "盛岡市加賀野3-9-1", "盛岡市", "019-623-4241", "中学校"),
    ("岩手大学教育学部附属特別支援学校", "020-0824", "盛岡市東安庭3-4-20", "盛岡市", "019-651-9002", "特別支援学校"),
]


def parse_national() -> None:
    for name, postal, addr, muni, phone, stype in NATIONAL_SCHOOLS:
        add_record(
            name=name,
            school_type=stype,
            establishment="国立",
            postal_code=postal,
            address=normalize_address(addr, prefix=muni),
            municipality=muni,
            phone=phone,
            source_name="岩手大学教育学部 附属学校一覧",
            source_url="https://www.edu.iwate-u.ac.jp/gakubu/huzoku/",
        )


# ---------------------------------------------------------------------------
# 統合・重複除外・ID付与・出力
# ---------------------------------------------------------------------------

ALLOWED_SCHOOL_TYPES = {
    "幼稚園", "幼保連携型認定こども園", "小学校", "中学校", "義務教育学校",
    "高等学校", "中等教育学校", "特別支援学校",
}

BARE_TYPE_NAMES = ALLOWED_SCHOOL_TYPES


# PDFの行折り返しで園名が前後の行に分裂したため手動補正
# （p.20: 「幼稚園ひめほた」/「九戸村...」/「る こ ど も 園」の3行に分裂）
KNOWN_NAME_CORRECTIONS = {
    ("九戸村", "岩手県九戸村大字長興寺14-33-3"): ("ひめほたるこども園", "幼保連携型認定こども園"),
}


def clean_records() -> None:
    cleaned = []
    for rec in records:
        fix = KNOWN_NAME_CORRECTIONS.get((rec["municipality"], rec["address"]))
        if fix:
            rec["name"], rec["school_type"] = fix
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
        base = slug(f"iwate-{rec['establishment']}-{rec['school_type']}-{rec['municipality']}-{rec['name']}")
        counts[base] = counts.get(base, 0) + 1
        rec["id"] = base if counts[base] == 1 else f"{base}-{counts[base]}"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "data" / "school-database" / "iwate.json"))
    args = parser.parse_args()

    parse_public_elem_jhs_kindergarten()
    parse_public_koukou()
    parse_tokushi()
    parse_private_yochien()
    parse_private_chu()
    parse_private_koukou()
    parse_national()

    clean_records()
    result = dedup_and_assign_ids()
    result.sort(key=lambda r: (r["municipality"], r["school_type"], r["name"]))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(result)} records to {out_path}")


if __name__ == "__main__":
    main()
