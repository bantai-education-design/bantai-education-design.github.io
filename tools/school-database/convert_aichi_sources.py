#!/usr/bin/env python3
"""Build the Aichi school database from official prefectural source files."""

from __future__ import annotations

import io
import json
import re
import sys
import unicodedata
from collections import Counter, OrderedDict
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pdfplumber
import requests

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "school-database" / "aichi.json"
WARNINGS_PATH = ROOT / "tools" / "school-database" / "aichi_conversion_warnings.json"
MANIFEST_PATH = ROOT / "docs" / "school-database" / "aichi" / "source-manifest.md"
TODAY = "2026-07-26"

SOURCES = {
    "public_index": "https://www.pref.aichi.jp/soshiki/kyoiku-somu/gakkoichiran.html",
    "public_elementary": "https://www.pref.aichi.jp/uploaded/attachment/582997.xlsx",
    "public_middle_obligation": "https://www.pref.aichi.jp/uploaded/attachment/582998.xlsx",
    "public_high": "https://www.pref.aichi.jp/uploaded/attachment/582999.xlsx",
    "public_special": "https://www.pref.aichi.jp/uploaded/attachment/583000.xlsx",
    "public_other": "https://www.pref.aichi.jp/uploaded/attachment/583001.xlsx",
    "private_index": "https://www.pref.aichi.jp/soshiki/shigaku/shigakumeibo.html",
    "private_high": "https://www.pref.aichi.jp/uploaded/life/588285_2703650_misc.pdf",
    "private_elementary_middle_secondary": "https://www.pref.aichi.jp/uploaded/life/588285_2703651_misc.pdf",
    "private_kindergarten_nagoya": "https://www.pref.aichi.jp/uploaded/life/588285_2703652_misc.pdf",
    "private_kindergarten_other": "https://www.pref.aichi.jp/uploaded/life/588285_2703653_misc.pdf",
}

SOURCE_NAMES = {
    "public_index": "愛知県教育委員会 令和7年度学校一覧",
    "public_elementary": "愛知県教育委員会 令和7年度学校一覧 小学校",
    "public_middle_obligation": "愛知県教育委員会 令和7年度学校一覧 中学校・義務教育学校",
    "public_high": "愛知県教育委員会 令和7年度学校一覧 高等学校",
    "public_special": "愛知県教育委員会 令和7年度学校一覧 特別支援学校",
    "public_other": "愛知県教育委員会 令和7年度学校一覧 幼稚園・中等教育学校等",
    "private_index": "愛知県県民文化局 私立学校名簿",
    "private_high": "愛知県 私立高等学校名簿（令和7年4月1日現在）",
    "private_elementary_middle_secondary": "愛知県 私立小学校・中学校・中等教育学校名簿（令和7年4月1日現在）",
    "private_kindergarten_nagoya": "愛知県 私立幼稚園名簿 名古屋市内（令和7年4月1日現在）",
    "private_kindergarten_other": "愛知県 私立幼稚園名簿 名古屋市外（令和7年4月1日現在）",
}

SOURCE_DATES = {
    "public_elementary": "2025-05-01",
    "public_middle_obligation": "2025-05-01",
    "public_high": "2025-05-01",
    "public_special": "2025-05-01",
    "public_other": "2025-05-01",
    "private_high": "2025-04-01",
    "private_elementary_middle_secondary": "2025-04-01",
    "private_kindergarten_nagoya": "2025-04-01",
    "private_kindergarten_other": "2025-04-01",
}

SCHOOL_TYPE_ORDER = ["幼稚園", "小学校", "中学校", "義務教育学校", "高等学校", "中等教育学校", "特別支援学校"]
ESTABLISHMENT_ORDER = ["国立", "公立", "私立"]

# 愛知県庁の市町村一覧（市、郡内町村の掲載順）を基準にした行政順。
MUNICIPALITY_ORDER = [
    "名古屋市千種区", "名古屋市東区", "名古屋市北区", "名古屋市西区", "名古屋市中村区", "名古屋市中区",
    "名古屋市昭和区", "名古屋市瑞穂区", "名古屋市熱田区", "名古屋市中川区", "名古屋市港区", "名古屋市南区",
    "名古屋市守山区", "名古屋市緑区", "名古屋市名東区", "名古屋市天白区",
    "豊橋市", "岡崎市", "一宮市", "瀬戸市", "半田市", "春日井市", "豊川市", "津島市", "碧南市", "刈谷市",
    "豊田市", "安城市", "西尾市", "蒲郡市", "犬山市", "常滑市", "江南市", "小牧市", "稲沢市", "新城市",
    "東海市", "大府市", "知多市", "知立市", "尾張旭市", "高浜市", "岩倉市", "豊明市", "日進市", "田原市",
    "愛西市", "清須市", "北名古屋市", "弥富市", "みよし市", "あま市", "長久手市",
    "愛知郡東郷町", "西春日井郡豊山町", "丹羽郡大口町", "丹羽郡扶桑町",
    "海部郡大治町", "海部郡蟹江町", "海部郡飛島村",
    "知多郡阿久比町", "知多郡東浦町", "知多郡南知多町", "知多郡美浜町", "知多郡武豊町",
    "額田郡幸田町", "北設楽郡設楽町", "北設楽郡東栄町", "北設楽郡豊根村",
]

WARD_NAMES = [
    "千種区", "東区", "北区", "西区", "中村区", "中区", "昭和区", "瑞穂区", "熱田区", "中川区", "港区",
    "南区", "守山区", "緑区", "名東区", "天白区",
]

CITY_NAMES = [name for name in MUNICIPALITY_ORDER if name.endswith("市")]

TOWN_TO_DISTRICT = {
    "東郷町": "愛知郡東郷町",
    "豊山町": "西春日井郡豊山町",
    "大口町": "丹羽郡大口町",
    "扶桑町": "丹羽郡扶桑町",
    "大治町": "海部郡大治町",
    "蟹江町": "海部郡蟹江町",
    "飛島村": "海部郡飛島村",
    "阿久比町": "知多郡阿久比町",
    "東浦町": "知多郡東浦町",
    "南知多町": "知多郡南知多町",
    "美浜町": "知多郡美浜町",
    "武豊町": "知多郡武豊町",
    "幸田町": "額田郡幸田町",
    "設楽町": "北設楽郡設楽町",
    "東栄町": "北設楽郡東栄町",
    "豊根村": "北設楽郡豊根村",
}

COUNTY_ADDRESS_PREFIXES = {
    "愛知郡": [("諸輪", "愛知郡東郷町")],
    "西春日井郡": [("豊場", "西春日井郡豊山町")],
    "丹羽郡": [("奈良子", "丹羽郡大口町"), ("柏森", "丹羽郡扶桑町")],
    "海部郡": [("堀之内", "海部郡大治町"), ("城", "海部郡蟹江町"), ("宝", "海部郡蟹江町")],
    "知多郡": [
        ("宮津", "知多郡阿久比町"),
        ("藤江", "知多郡東浦町"),
        ("石浜", "知多郡東浦町"),
        ("内海", "知多郡南知多町"),
        ("篠島", "知多郡南知多町"),
        ("野間", "知多郡美浜町"),
        ("上野間", "知多郡美浜町"),
        ("高野前", "知多郡武豊町"),
        ("中根", "知多郡武豊町"),
    ],
    "額田郡": [("坂崎", "額田郡幸田町"), ("菱池", "額田郡幸田町")],
    "北設楽郡": [("田口", "北設楽郡設楽町")],
}


@dataclass
class ExtractedRecord:
    name: str
    school_type: str
    establishment: str
    postal_code: str
    address: str
    municipality: str
    operator: str
    phone: str
    website: str
    source_key: str
    source_url: str
    source_date: str
    course: list[str]


def clean_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = text.replace("\xa0", " ").replace("\u3000", " ")
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compact(value: object) -> str:
    return re.sub(r"\s+", "", clean_text(value))


def normalize_postal(value: object) -> str:
    match = re.search(r"(\d{3})-?(\d{4})", clean_text(value))
    return f"{match.group(1)}-{match.group(2)}" if match else ""


def normalize_phone(value: object) -> str:
    text = clean_text(value)
    text = text.replace("(", "").replace(")", "-").replace("ー", "-").replace("−", "-").replace("―", "-")
    text = re.sub(r"[^0-9-]", "", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def is_school_name(value: str) -> bool:
    if not value:
        return False
    bad = ["計", "学校名", "市区町村", "課程", "所在地", "電話", "園名", "合計"]
    if value in bad or any(value.startswith(x) for x in bad):
        return False
    if re.fullmatch(r"[ぁ-んァ-ンー・]+", value):
        return False
    return True


def suffix_name(name: str, school_type: str, type_label: str = "") -> str:
    raw = compact(name)
    if not raw:
        return ""
    is_branch = raw.startswith(("(", "（")) and raw.endswith((")", "）"))
    base = raw.strip("()（）") if is_branch else raw
    if school_type == "幼稚園":
        return base if base.endswith(("幼稚園", "園")) else f"{base}幼稚園"
    if school_type == "小学校":
        return base if base.endswith("小学校") else f"{base}小学校"
    if school_type == "中学校":
        if "中学校" in base:
            return base
        name = base if base.endswith("中学校") else f"{base}中学校"
        return f"{name}分校" if is_branch else name
    if school_type == "義務教育学校":
        return base if base.endswith("義務教育学校") else f"{base}義務教育学校"
    if school_type == "高等学校":
        paren = re.fullmatch(r"(.+?)[(（](.+?)[)）]", base)
        if paren and "高等学校" not in paren.group(1):
            return f"{paren.group(1)}高等学校{paren.group(2)}"
        if "高等学校" in base:
            return base
        return base if base.endswith("高等学校") else f"{base}高等学校"
    if school_type == "中等教育学校":
        return base if base.endswith("中等教育学校") else f"{base}中等教育学校"
    if school_type == "特別支援学校":
        label = compact(type_label) or "特別支援学校"
        if label in {"盲学校", "聾学校"}:
            return base if base.endswith(label) else f"{base}{label}"
        if label == "高等特支":
            return base if base.endswith("高等特別支援学校") else f"{base}高等特別支援学校"
        return base if base.endswith("特別支援学校") else f"{base}特別支援学校"
    return base


def normalize_municipality(value: object) -> str:
    text = compact(value)
    if text in WARD_NAMES:
        return f"名古屋市{text}"
    return TOWN_TO_DISTRICT.get(text, text)


def normalize_address(value: object, municipality_hint: str = "") -> str:
    address = compact(value)
    if not address or "省略" in address:
        return ""
    address = address.removeprefix("愛知県")
    for ward in WARD_NAMES:
        if address.startswith(ward):
            address = f"名古屋市{address}"
            break
    municipality_hint = expand_municipality_hint(municipality_hint, address)
    if municipality_hint and not address.startswith(municipality_hint) and not address_has_municipality(address):
        muni = municipality_hint.removeprefix("名古屋市") if municipality_hint.startswith("名古屋市") else municipality_hint
        if not address.startswith(muni):
            address = f"{municipality_hint}{address}"
    return f"愛知県{address}"


def expand_municipality_hint(municipality_hint: str, address: str) -> str:
    if municipality_hint in MUNICIPALITY_ORDER:
        return municipality_hint
    for prefix, municipality in COUNTY_ADDRESS_PREFIXES.get(municipality_hint, []):
        if address.startswith(prefix):
            return municipality
    return municipality_hint


def address_has_municipality(address: str) -> bool:
    if address.startswith("名古屋市") or any(address.startswith(ward) for ward in WARD_NAMES):
        return True
    if any(address.startswith(city) for city in CITY_NAMES):
        return True
    if any(address.startswith(municipality) for municipality in MUNICIPALITY_ORDER if "郡" in municipality):
        return True
    return any(address.startswith(town) for town in TOWN_TO_DISTRICT)


def municipality_from_address(address: str, fallback: str = "") -> str:
    text = address.removeprefix("愛知県")
    if text.startswith("名古屋市"):
        for ward in WARD_NAMES:
            if text.startswith(f"名古屋市{ward}"):
                return f"名古屋市{ward}"
    match = re.match(r"(.+?市)", text)
    if match:
        return match.group(1)
    match = re.match(r"(.+?郡.+?[町村])", text)
    if match:
        return match.group(1)
    for town, full_name in TOWN_TO_DISTRICT.items():
        if text.startswith(town):
            return full_name
    return normalize_municipality(fallback)


def download(url: str) -> bytes:
    response = requests.get(url, timeout=45)
    response.raise_for_status()
    return response.content


def iter_xlsx_rows(source_key: str):
    content = download(SOURCES[source_key])
    xl = pd.ExcelFile(io.BytesIO(content))
    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet, header=None, dtype=str).fillna("")
        for row in df.itertuples(index=False, name=None):
            yield sheet, [clean_text(cell) for cell in row]


def add_record(records: list[ExtractedRecord], warnings: list[dict[str, str]], record: ExtractedRecord) -> None:
    if not record.name or not record.school_type:
        return
    if not record.postal_code:
        warnings.append({"level": "warning", "type": "missing_postal_code", "name": record.name, "source": record.source_key})
    if not record.address:
        warnings.append({"level": "warning", "type": "missing_address", "name": record.name, "source": record.source_key})
    records.append(record)


def extract_standard_xlsx(records: list[ExtractedRecord], warnings: list[dict[str, str]], source_key: str, school_type: str, name_col: int, postal_col: int, address_col: int, phone_col: int, default_establishment: str = "公立", type_col: int | None = None) -> None:
    current_municipality = ""
    current_establishment = default_establishment
    current_special_base = ""
    current_sheet = ""
    for sheet, row in iter_xlsx_rows(source_key):
        if sheet != current_sheet:
            current_sheet = sheet
            current_establishment = default_establishment
            if source_key == "public_elementary" and sheet.startswith("P.26"):
                current_establishment = "国立"
            if source_key == "public_middle_obligation" and sheet.startswith("P.39"):
                current_establishment = "国立"
            if source_key == "public_high" and sheet.startswith("P.47"):
                current_establishment = "国立"
            if source_key == "public_high" and sheet.startswith("P.48"):
                current_establishment = "私立"
        row_text = compact(" ".join(row))
        if not row_text:
            continue
        if source_key == "public_elementary" and sheet.startswith("P.26"):
            continue
        if source_key == "public_middle_obligation" and sheet.startswith("P.39"):
            continue
        if "国立" in row_text and "私立" not in row_text and len(row_text) < 20:
            current_establishment = "国立"
        if row_text in {"私立", "私立学校"} or (source_key == "public_high" and sheet.startswith("P.48")):
            current_establishment = "私立"
        if source_key in {"public_elementary", "public_middle_obligation", "public_high"} and ("国立・私立" in sheet or sheet.startswith("P.47") or sheet.startswith("P.26") or sheet.startswith("P.39")):
            if current_establishment == default_establishment:
                current_establishment = "国立"
        postal = normalize_postal(row[postal_col] if len(row) > postal_col else "")
        if not postal:
            if row and is_school_name(compact(row[0])) and "休" not in row_text:
                current_municipality = normalize_municipality(row[0])
            continue
        if current_establishment == "私立":
            continue
        if source_key in {"public_high", "public_special"}:
            municipality_hint = current_municipality
        else:
            municipality_hint = normalize_municipality(row[0] if len(row) > 0 else current_municipality)
        if municipality_hint:
            current_municipality = municipality_hint
        type_label = compact(row[type_col]) if type_col is not None and len(row) > type_col else ""
        raw_name = row[name_col] if len(row) > name_col else ""
        if school_type == "特別支援学校" and compact(raw_name).startswith(("(", "（")):
            name = f"{current_special_base}{compact(raw_name).strip('()（）')}"
        else:
            name = suffix_name(raw_name, school_type, type_label)
        if not is_school_name(name):
            continue
        if school_type == "特別支援学校" and not name.endswith("校舎"):
            current_special_base = name
        address = normalize_address(row[address_col] if len(row) > address_col else "", current_municipality)
        municipality = municipality_from_address(address, current_municipality)
        add_record(records, warnings, ExtractedRecord(
            name=name,
            school_type=school_type,
            establishment=current_establishment,
            postal_code=postal,
            address=address,
            municipality=municipality,
            operator="",
            phone=normalize_phone(row[phone_col] if len(row) > phone_col else ""),
            website="",
            source_key=source_key,
            source_url=SOURCES[source_key],
            source_date=SOURCE_DATES[source_key],
            course=[],
        ))


def extract_national_elementary_middle(records: list[ExtractedRecord], warnings: list[dict[str, str]]) -> None:
    targets = {
        ("public_elementary", "461-0047"): ("愛知教育大学附属名古屋小学校", "小学校"),
        ("public_elementary", "444-0072"): ("愛知教育大学附属岡崎小学校", "小学校"),
        ("public_middle_obligation", "464-8601"): ("名古屋大学教育学部附属中学校", "中学校"),
        ("public_middle_obligation", "461-0047"): ("愛知教育大学附属名古屋中学校", "中学校"),
        ("public_middle_obligation", "444-0864"): ("愛知教育大学附属岡崎中学校", "中学校"),
    }
    for source_key in ["public_elementary", "public_middle_obligation"]:
        for sheet, row in iter_xlsx_rows(source_key):
            if not (sheet.startswith("P.26") or sheet.startswith("P.39")):
                continue
            postal = normalize_postal(" ".join(row))
            target = targets.get((source_key, postal))
            if not target:
                continue
            address_col = 11 if source_key == "public_elementary" else 8
            phone_col = 13 if source_key == "public_elementary" else 10
            address = normalize_address(row[address_col])
            add_record(records, warnings, ExtractedRecord(
                target[0], target[1], "国立", postal, address, municipality_from_address(address),
                "", normalize_phone(row[phone_col]), "", source_key, SOURCES[source_key], SOURCE_DATES[source_key], []
            ))


def extract_public_kindergarten_and_secondary(records: list[ExtractedRecord], warnings: list[dict[str, str]], exclusions: list[dict[str, str]]) -> None:
    source_key = "public_other"
    current_municipality = ""
    current_establishment = "公立"
    current_sheet = ""
    for sheet, row in iter_xlsx_rows(source_key):
        if sheet != current_sheet:
            current_sheet = sheet
            current_establishment = "公立"
        row_text = compact(" ".join(row))
        if not row_text:
            continue
        if "国立" in row_text and len(row_text) < 20:
            current_establishment = "国立"
        if sheet.startswith("P54"):
            school_type = "中等教育学校"
            name_col, postal_col, address_col, phone_col = 0, 9, 10, 12
        elif sheet.startswith(("P51", "P52", "P53")):
            school_type = "幼稚園"
            name_col, postal_col, address_col, phone_col = 1, 7, 8, 10
        else:
            continue
        postal = normalize_postal(row[postal_col] if len(row) > postal_col else "")
        if not postal:
            candidate = normalize_municipality(row[0] if row else "")
            if candidate:
                current_municipality = candidate
            if "休園" in row_text:
                exclusions.append({"name": compact(row[name_col] if len(row) > name_col else ""), "reason": "公式一覧で休園と記載され、郵便番号・所在地が省略されているため除外", "source": source_key})
            continue
        municipality_hint = normalize_municipality(row[0] if len(row) > 0 else current_municipality)
        if municipality_hint:
            current_municipality = municipality_hint
        if sheet.startswith("P53") and compact(row[0] if row else "") == "愛知教育大学附属":
            name = "愛知教育大学附属幼稚園"
            current_establishment = "国立"
        else:
            name = suffix_name(row[name_col] if len(row) > name_col else "", school_type)
        if not is_school_name(name):
            continue
        address = normalize_address(row[address_col] if len(row) > address_col else "", current_municipality)
        add_record(records, warnings, ExtractedRecord(
            name, school_type, current_establishment, postal, address, municipality_from_address(address, current_municipality),
            "", normalize_phone(row[phone_col] if len(row) > phone_col else ""), "", source_key, SOURCES[source_key],
            SOURCE_DATES[source_key], []
        ))


def pdf_tables(source_key: str):
    with pdfplumber.open(io.BytesIO(download(SOURCES[source_key]))) as pdf:
        for page_number, page in enumerate(pdf.pages):
            for table_number, table in enumerate(page.extract_tables() or []):
                yield page_number, table_number, [[clean_text(cell) for cell in row] for row in table]


def extract_private_high(records: list[ExtractedRecord], warnings: list[dict[str, str]]) -> None:
    source_key = "private_high"
    for _, _, table in pdf_tables(source_key):
        for row in table:
            if len(row) < 4 or row[0] in {"学校名", ""}:
                continue
            postal = normalize_postal(row[1])
            if not postal:
                continue
            address = normalize_address(row[2])
            add_record(records, warnings, ExtractedRecord(
                suffix_name(row[0], "高等学校"), "高等学校", "私立", postal, address, municipality_from_address(address),
                "", normalize_phone(row[3]), "", source_key, SOURCES[source_key], SOURCE_DATES[source_key],
                [clean_text(row[4])] if len(row) > 4 and clean_text(row[4]) else []
            ))


def extract_private_elementary_middle_secondary(records: list[ExtractedRecord], warnings: list[dict[str, str]]) -> None:
    source_key = "private_elementary_middle_secondary"
    for page_number, table_number, table in pdf_tables(source_key):
        if page_number == 0 and table_number == 0:
            school_type = "小学校"
        elif page_number == 1 and table_number == 1:
            school_type = "中等教育学校"
        else:
            school_type = "中学校"
        for row in table:
            if len(row) < 4 or row[0] in {"学校名", ""}:
                continue
            postal = normalize_postal(row[1])
            if not postal:
                continue
            address = normalize_address(row[2])
            add_record(records, warnings, ExtractedRecord(
                suffix_name(row[0], school_type), school_type, "私立", postal, address, municipality_from_address(address),
                "", normalize_phone(row[3]), "", source_key, SOURCES[source_key], SOURCE_DATES[source_key], []
            ))


def extract_private_kindergarten(records: list[ExtractedRecord], warnings: list[dict[str, str]], exclusions: list[dict[str, str]], source_key: str) -> None:
    for _, _, table in pdf_tables(source_key):
        for row in table:
            if len(row) < 4 or row[0] in {"園名", ""}:
                continue
            row_text = compact(" ".join(row))
            postal = normalize_postal(row[1])
            if not postal:
                if "休園" in row_text:
                    exclusions.append({"name": compact(row[0]), "reason": "公式名簿で休園と記載されているため除外", "source": source_key})
                continue
            address = normalize_address(row[2])
            add_record(records, warnings, ExtractedRecord(
                suffix_name(row[0], "幼稚園"), "幼稚園", "私立", postal, address, municipality_from_address(address),
                "", normalize_phone(row[3]), "", source_key, SOURCES[source_key], SOURCE_DATES[source_key], []
            ))


def dedupe(records: list[ExtractedRecord], warnings: list[dict[str, str]]) -> list[ExtractedRecord]:
    seen: OrderedDict[tuple[str, str, str, str], ExtractedRecord] = OrderedDict()
    for record in records:
        key = (record.name, record.school_type, record.establishment, record.address)
        if key in seen:
            warnings.append({"level": "info", "type": "duplicate_removed", "name": record.name, "source": record.source_key})
            continue
        seen[key] = record
    return list(seen.values())


def sort_records(records: list[ExtractedRecord]) -> list[ExtractedRecord]:
    type_index = {name: i for i, name in enumerate(SCHOOL_TYPE_ORDER)}
    est_index = {name: i for i, name in enumerate(ESTABLISHMENT_ORDER)}
    muni_index = {name: i for i, name in enumerate(MUNICIPALITY_ORDER)}
    return sorted(records, key=lambda r: (
        muni_index.get(r.municipality, 999),
        est_index.get(r.establishment, 999),
        type_index.get(r.school_type, 999),
        r.postal_code,
        r.name,
    ))


def to_json_records(records: list[ExtractedRecord]) -> list[dict[str, object]]:
    output = []
    for idx, record in enumerate(records, 1):
        output.append({
            "id": f"aichi-{idx:04d}",
            "prefecture": "愛知県",
            "name": record.name,
            "name_kana": "",
            "postal_code": record.postal_code,
            "address": record.address,
            "municipality": record.municipality,
            "school_type": record.school_type,
            "establishment": record.establishment,
            "operator": record.operator,
            "phone": record.phone,
            "website": record.website,
            "source_name": SOURCE_NAMES[record.source_key],
            "source_url": record.source_url,
            "source_date": record.source_date,
            "verified_date": TODAY,
            "course": record.course,
        })
    return output


def validate(records: list[dict[str, object]]) -> list[str]:
    errors = []
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)):
        errors.append("duplicate ids")
    required = ["name", "school_type", "establishment", "postal_code", "address", "municipality", "source_url"]
    for record in records:
        for field in required:
            if not record[field]:
                errors.append(f"{record['id']} missing {field}")
        if record["postal_code"] and not re.fullmatch(r"\d{3}-\d{4}", str(record["postal_code"])):
            errors.append(f"{record['id']} bad postal_code")
        if record["phone"] and not re.fullmatch(r"0\d{1,4}-\d{1,4}-\d{3,4}", str(record["phone"])):
            errors.append(f"{record['id']} bad phone {record['phone']}")
        if record["website"] and not str(record["website"]).startswith("http"):
            errors.append(f"{record['id']} bad website")
    return errors


def write_manifest(records: list[dict[str, object]], warnings: list[dict[str, str]], exclusions: list[dict[str, str]]) -> None:
    by_type = Counter(str(r["school_type"]) for r in records)
    by_est = Counter(str(r["establishment"]) for r in records)
    by_muni = Counter(str(r["municipality"]) for r in records)
    warning_counts = Counter(w["type"] for w in warnings)
    lines = [
        "# 愛知県 学校データベース source manifest",
        "",
        f"- 生成日: {TODAY}",
        f"- 総収録件数: {len(records)}",
        "- 収録対象: 幼稚園、小学校、中学校、義務教育学校、高等学校、中等教育学校、特別支援学校",
        "- 設置区分: 国立、公立、私立",
        "- 自治体順: 愛知県庁の市町村一覧で用いられる市、郡内町村の行政順を基準にし、名古屋市は区順に展開。",
        "- data-source/: 使用していません。公式URLから変換時に直接取得します。",
        "",
        "## 使用一次資料",
    ]
    for key in [
        "public_index", "public_elementary", "public_middle_obligation", "public_high", "public_special", "public_other",
        "private_index", "private_high", "private_elementary_middle_secondary", "private_kindergarten_nagoya", "private_kindergarten_other",
    ]:
        date = SOURCE_DATES.get(key, "2025-09-11" if key == "public_index" else "2025-04-01")
        lines.append(f"- {SOURCE_NAMES[key]}（基準日/更新日: {date}）: {SOURCES[key]}")
    lines.extend([
        "",
        "## 件数",
        "",
        "### 校種別",
    ])
    for key in SCHOOL_TYPE_ORDER:
        lines.append(f"- {key}: {by_type.get(key, 0)}")
    lines.extend(["", "### 設置区分別"])
    for key in ESTABLISHMENT_ORDER:
        lines.append(f"- {key}: {by_est.get(key, 0)}")
    lines.extend(["", "### 自治体別"])
    for key in MUNICIPALITY_ORDER:
        if by_muni.get(key):
            lines.append(f"- {key}: {by_muni[key]}")
    for key, count in sorted(by_muni.items()):
        if key not in MUNICIPALITY_ORDER:
            lines.append(f"- {key}: {count}")
    lines.extend([
        "",
        "## 除外対象",
        "",
        "- 専修学校、各種学校、大学、短期大学、高等専門学校、保育所、認定こども園は共通方針により対象外。",
        f"- 公式資料上の休園等による除外: {len(exclusions)}件",
    ])
    for item in exclusions:
        lines.append(f"  - {item.get('name', '')}: {item.get('reason', '')}（{item.get('source', '')}）")
    lines.extend([
        "",
        "## 補正・補完",
        "",
        "- NFKC正規化、学校名中の不要空白除去、電話番号の括弧表記のハイフン化を実施。",
        "- 郵便番号補完: 0件（公式一覧の郵便番号を使用）",
        f"- 重複除去: {warning_counts.get('duplicate_removed', 0)}件",
        f"- 警告件数: {len(warnings)}件",
        "",
        "## 検証",
        "",
        "- JSON構文、必須項目、郵便番号形式、電話番号形式、URL形式、重複IDを変換スクリプト内で検証。",
    ])
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    records: list[ExtractedRecord] = []
    warnings: list[dict[str, str]] = []
    exclusions: list[dict[str, str]] = []

    extract_standard_xlsx(records, warnings, "public_elementary", "小学校", 1, 10, 11, 13)
    extract_standard_xlsx(records, warnings, "public_middle_obligation", "中学校", 1, 7, 8, 10)
    extract_standard_xlsx(records, warnings, "public_middle_obligation", "義務教育学校", 1, 11, 12, 14)
    extract_national_elementary_middle(records, warnings)
    extract_standard_xlsx(records, warnings, "public_high", "高等学校", 0, 9, 10, 12)
    extract_standard_xlsx(records, warnings, "public_special", "特別支援学校", 1, 4, 5, 7, type_col=0)
    extract_public_kindergarten_and_secondary(records, warnings, exclusions)
    extract_private_high(records, warnings)
    extract_private_elementary_middle_secondary(records, warnings)
    extract_private_kindergarten(records, warnings, exclusions, "private_kindergarten_nagoya")
    extract_private_kindergarten(records, warnings, exclusions, "private_kindergarten_other")

    records = sort_records(dedupe(records, warnings))
    output = to_json_records(records)
    errors = validate(output)
    if errors:
        raise SystemExit("validation failed:\n" + "\n".join(errors[:100]))

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    WARNINGS_PATH.write_text(json.dumps({
        "generated": TODAY,
        "total_records": len(output),
        "by_type": dict(Counter(str(r["school_type"]) for r in output)),
        "by_establishment": dict(Counter(str(r["establishment"]) for r in output)),
        "warnings": warnings,
        "exclusions": exclusions,
        "postal_supplements": [],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_manifest(output, warnings, exclusions)
    print(json.dumps({
        "total": len(output),
        "by_type": dict(Counter(str(r["school_type"]) for r in output)),
        "by_establishment": dict(Counter(str(r["establishment"]) for r in output)),
        "warnings": len(warnings),
        "exclusions": len(exclusions),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
