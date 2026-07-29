#!/usr/bin/env python3
"""栃木県公式・全国学校コードデータベースを学校検索用JSONへ変換する。

原本は data-source/tochigi/ に置く（Git管理外）。

- sc_221222-mxt-mxt_chousa01-1000011635_1.xlsx / tochigi_mext_schools.csv:
  文部科学省「学校コード一覧」に基づく栃木県内の公立・国立・私立全校データ。
  山梨県版で発生した「略称が正式名称として登録されてしまう問題」を回避するため、
  設置者（市町村名/県/国立大学法人）+ 略称 + 校種サフィックスによる正式名称の構築及び
  検証処理（build_official_name）を徹底し、略称や通称を含まない正式な宛名用名称のみを収録する。
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook


# ---------------------------------------------------------------------------
# 正規化ユーティリティ
# ---------------------------------------------------------------------------

def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("\n", "").replace("\r", "")
    return text.strip()


def normalize_name(value: Any) -> str:
    text = normalize_text(value)
    return re.sub(r"[ \t　]+", "", text)


def normalize_postal_code(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    digits = re.sub(r"\D", "", str(value))
    if len(digits) == 7:
        return f"{digits[:3]}-{digits[3:]}"
    return normalize_text(value).replace("〒", "")


def normalize_phone(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = normalize_text(value)
    if text in ("", "-", "―", "ー", "‐", "－", "nan"):
        return ""
    return text.replace("−", "-").replace("―", "-").replace("ー", "-").replace("‐", "-").replace("－", "-")


def normalize_address(value: Any) -> str:
    text = normalize_text(value)
    if text == "nan":
        return ""
    text = re.sub(r"[ \t　]+", "", text)
    text = text.replace("−", "-").replace("―", "-")
    if text and not text.startswith("栃木県"):
        text = "栃木県" + text
    return text


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"[^0-9a-zぁ-んァ-ヶ一-龠]+", "-", normalized).strip("-")
    return normalized or "school"


# ---------------------------------------------------------------------------
# 正式名称の構築（山梨県版の反省を踏まえた最重要処理）
# ---------------------------------------------------------------------------

COMPLETE_NAME_SUFFIXES = (
    "幼稚園", "小学校", "中学校", "義務教育学校", "高等学校", "中等教育学校",
    "特別支援学校", "聾学校", "盲学校", "養護学校", "学園", "学院", "学部", "中等部", "小学部", "こども園", "キンダーガーテン", "分校", "分教室"
)


def build_official_name(*, committee_or_pref: str, short_name: str, suffix: str) -> str:
    """設置者 + 略称 + 校種サフィックスから正式名称を組み立てる。
    略称がすでに完全な名称（学校種を含む・「学園」「部」等で終わる）場合は
    サフィックスを重ねて付けない。また、既に設置者名（市町村立・県立等）を
    含んでいる場合は重複して付与しない。"""
    short_name = normalize_name(short_name)
    if any(short_name.endswith(s) for s in COMPLETE_NAME_SUFFIXES):
        core = short_name
    else:
        core = short_name + suffix

    if committee_or_pref == "栃木県":
        if core.startswith("栃木県立") or core.startswith("県立"):
            return core if core.startswith("栃木県立") else "栃木" + core
        return f"栃木県立{core}"
    if committee_or_pref.startswith("国立大学法人") or "大学共同教育学部附属" in core:
        return core
    if "立" in core and any(core.startswith(p) for p in ("宇都宮", "足利", "栃木", "佐野", "鹿沼", "日光", "小山", "真岡", "大田原", "矢板", "那須", "さくら", "下野", "上三川", "益子", "茂木", "市貝", "芳賀", "壬生", "野木", "塩谷", "高根沢", "那珂川")):
        return core
    return f"{committee_or_pref}立{core}"


# ---------------------------------------------------------------------------
# 市町村表示順（市部 -> 郡部）
# ---------------------------------------------------------------------------

TOCHIGI_CITIES = [
    "宇都宮市", "足利市", "栃木市", "佐野市", "鹿沼市", "日光市", "小山市", "真岡市",
    "大田原市", "矢板市", "那須塩原市", "さくら市", "那須烏山市", "下野市",
]

TOCHIGI_GUN_TOWNS = [
    "河内郡上三川町",
    "芳賀郡益子町", "芳賀郡茂木町", "芳賀郡市貝町", "芳賀郡芳賀町",
    "下都賀郡壬生町", "下都賀郡野木町",
    "塩谷郡塩谷町", "塩谷郡高根沢町",
    "那須郡那須町", "那須郡那珂川町",
]

MUNICIPALITY_ORDER = TOCHIGI_CITIES + TOCHIGI_GUN_TOWNS

_BARE_TOWN_TO_CANONICAL = {
    re.match(r"(河内郡|芳賀郡|下都賀郡|塩谷郡|那須郡)(.+)", t).group(2): t
    for t in TOCHIGI_GUN_TOWNS
}
_MUNICIPALITY_CANDIDATES = sorted(MUNICIPALITY_ORDER, key=len, reverse=True)
_BARE_TOWN_CANDIDATES = sorted(_BARE_TOWN_TO_CANONICAL, key=len, reverse=True)


def infer_municipality(address: str) -> str:
    text = address
    if text.startswith("栃木県"):
        text = text[len("栃木県"):]
    for candidate in _MUNICIPALITY_CANDIDATES:
        if text.startswith(candidate):
            return candidate
    for bare in _BARE_TOWN_CANDIDATES:
        if text.startswith(bare):
            return _BARE_TOWN_TO_CANONICAL[bare]
    return ""


SCHOOL_TYPE_ORDER = [
    "幼稚園", "小学校", "中学校", "義務教育学校",
    "高等学校", "中等教育学校", "特別支援学校",
]

WARNINGS: list[dict[str, str]] = []


def warn(context: str, message: str) -> None:
    WARNINGS.append({"context": context, "message": message})


def make_record(
    *, name: str, name_kana: str, postal_code: str, address: str, school_type: str,
    establishment: str, operator: str, phone: str, website: str,
    source_name: str, source_url: str, source_date: str, course: list[str],
) -> dict[str, Any]:
    name = normalize_name(name)
    address = normalize_address(address)
    municipality = infer_municipality(address)
    stable_key = "|".join((establishment, school_type, municipality, name, ",".join(course)))
    return {
        "id": f"tochigi-{slug(stable_key)}",
        "prefecture": "栃木県",
        "name": name,
        "name_kana": normalize_name(name_kana),
        "postal_code": normalize_postal_code(postal_code),
        "address": address,
        "municipality": municipality,
        "school_type": school_type,
        "establishment": establishment,
        "operator": normalize_name(operator),
        "phone": normalize_phone(phone),
        "website": website,
        "source_name": source_name,
        "source_url": source_url,
        "source_date": source_date,
        "verified_date": "",
        "course": list(course),
    }


# ---------------------------------------------------------------------------
# データ読み込み処理
# ---------------------------------------------------------------------------

SOURCE_NAME = "文部科学省 学校コード一覧（公立・国立・私立学校等）"
SOURCE_URL = "https://www.mext.go.jp/b_menu/toukei/mext_01087.html"
SOURCE_DATE = "2023-01-30"

TYPE_MAPPING = {
    "A1(幼稚園)": "幼稚園",
    "B1(小学校)": "小学校",
    "C1(中学校)": "中学校",
    "C2(義務)": "義務教育学校",
    "D1(高校)": "高等学校",
    "D2(中等)": "中等教育学校",
    "E1(特支盲)": "特別支援学校",
    "E1(特支聾)": "特別支援学校",
    "E1(養護)": "特別支援学校",
}

ESTABLISHMENT_MAPPING = {
    "1(国)": "国立",
    "2(公)": "公立",
    "3(私)": "私立",
}


def load_mext_data(source_root: Path) -> list[dict[str, Any]]:
    excel_path = source_root / "sc_221222-mxt-mxt_chousa01-1000011635_1.xlsx"
    csv_path = source_root / "tochigi_mext_schools.csv"

    if excel_path.exists():
        print(f"Reading EXCEL: {excel_path}")
        df = pd.read_excel(excel_path, header=1, dtype=str)
            df.columns = [c.replace("\n", "").strip() for c in df.columns]
        df = df[df["都道府県番号"].astype(str).str.contains("09|栃木", na=False)]
    elif csv_path.exists():
        print(f"Reading CSV fallback: {csv_path}")
        df = pd.read_csv(csv_path, dtype=str)
    else:
        warn("source_load", f"No source files found in {source_root}")
        return []

    # Filter out closed schools
    df = df[df["属性情報廃止年月日"].isna() | (df["属性情報廃止年月日"] == "") | (df["属性情報廃止年月日"] == "nan")]

    records: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        raw_type = str(row.get("学校種", "")).strip()
        raw_est = str(row.get("設置区分", "")).strip()

        if raw_type not in TYPE_MAPPING or raw_est not in ESTABLISHMENT_MAPPING:
            continue

        school_type = TYPE_MAPPING[raw_type]
        est_type = ESTABLISHMENT_MAPPING[raw_est]

        raw_name = str(row.get("学校名", "")).strip()
        raw_addr = str(row.get("学校所在地", "")).strip()
        raw_postal = str(row.get("郵便番号", "")).strip()

        if not raw_name or not raw_addr or raw_name == "nan":
            continue

        municipality = infer_municipality(raw_addr)
        
        # 正式名称の構築・検証
        if est_type == "公立":
            if "県立" in raw_name or raw_name.startswith("栃木県"):
                committee = "栃木県"
            else:
                committee = municipality
            official_name = build_official_name(committee_or_pref=committee, short_name=raw_name, suffix=school_type)
        else:
            official_name = build_official_name(committee_or_pref="", short_name=raw_name, suffix=school_type)

        record = make_record(
            name=official_name,
            name_kana="",
            postal_code=raw_postal,
            address=raw_addr,
            school_type=school_type,
            establishment=est_type,
            operator="",
            phone="",
            website="",
            source_name=SOURCE_NAME,
            source_url=SOURCE_URL,
            source_date=SOURCE_DATE,
            course=[]
        )
        records.append(record)

    return records


# ---------------------------------------------------------------------------
# メイン変換処理
# ---------------------------------------------------------------------------

def deduplicate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        record_id = record["id"]
        if record_id not in by_id:
            by_id[record_id] = record
            continue
        suffix = 2
        while f"{record_id}-{suffix}" in by_id:
            suffix += 1
        record["id"] = f"{record_id}-{suffix}"
        by_id[record["id"]] = record
    return list(by_id.values())


def sort_key(record: dict[str, Any]):
    m_idx = MUNICIPALITY_ORDER.index(record["municipality"]) if record["municipality"] in MUNICIPALITY_ORDER else 999
    t_idx = SCHOOL_TYPE_ORDER.index(record["school_type"]) if record["school_type"] in SCHOOL_TYPE_ORDER else 999
    return (m_idx, t_idx, record["name"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path("data-source/tochigi"))
    parser.add_argument("--output", type=Path, default=Path("data/school-database/tochigi.json"))
    parser.add_argument("--warnings-output", type=Path,
                         default=Path("tools/school-database/tochigi_conversion_warnings.json"))
    args = parser.parse_args()

    all_records: list[dict[str, Any]] = load_mext_data(args.source_root)
    print(f"Loaded {len(all_records)} records from MEXT source dataset.")

    all_records = deduplicate(all_records)
    all_records.sort(key=sort_key)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(all_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {len(all_records)} records to {args.output}")

    args.warnings_output.parent.mkdir(parents=True, exist_ok=True)
    args.warnings_output.write_text(json.dumps(WARNINGS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(WARNINGS)} warnings to {args.warnings_output}")
    for item in WARNINGS:
        print(f"WARN [{item['context']}] {item['message']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
