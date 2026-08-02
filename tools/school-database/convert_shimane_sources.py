#!/usr/bin/env python3
"""島根県学校データベース変換スクリプト

原本: 文部科学省「学校コード一覧（全国公立・国立・私立学校等）」
      sc_20260529-mxt_chousa01-000011635_3.xlsx（2026-05-29版）

山梨県版での略称問題、茨城・栃木県版での build_official_name による
正式名称の構築ルールを踏襲する。

設置区分 + 自治体名 + 学校名 + 校種サフィックスの組み立てで宛名用の
正式名称を担保する。
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# テキスト正規化ユーティリティ
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
    if value is None:
        return ""
    s = str(value)
    if s in ("nan", "", "None"):
        return ""
    digits = re.sub(r"\D", "", s)
    if len(digits) == 7:
        return f"{digits[:3]}-{digits[3:]}"
    return normalize_text(value)


def normalize_phone(value: Any) -> str:
    if value is None:
        return ""
    text = normalize_text(value)
    if text in ("", "-", "―", "ー", "nan"):
        return ""
    return re.sub(r"[−―ー‐－]", "-", text)


def normalize_address(value: Any) -> str:
    text = normalize_text(value)
    if text in ("nan", ""):
        return ""
    text = re.sub(r"[ \t　]+", "", text)
    text = re.sub(r"[−―ー]", "-", text)
    if text and not text.startswith("島根県"):
        text = "島根県" + text
    return text


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"[^0-9a-zぁ-んァ-ヶ一-龠]+", "-", normalized).strip("-")
    return normalized or "school"


# ---------------------------------------------------------------------------
# 島根県 市区町村一覧（行政表示順）
# ---------------------------------------------------------------------------

SHIMANE_CITIES = [
    "松江市", "浜田市", "出雲市", "益田市", "大田市", "安来市",
    "江津市", "雲南市"
]

SHIMANE_GUN_TOWNS = [
    "仁多郡奥出雲町", "飯石郡飯南町", "邑智郡川本町", "邑智郡美郷町", "邑智郡邑南町", "鹿足郡津和野町",
    "鹿足郡吉賀町", "隠岐郡海士町", "隠岐郡西ノ島町", "隠岐郡知夫村", "隠岐郡隠岐の島町"
]

MUNICIPALITY_ORDER = SHIMANE_CITIES + SHIMANE_GUN_TOWNS

# 郡名なし → 正式名称へのマッピング（分詞が重なる村名・町名の解決）
_BARE_TO_CANONICAL: dict[str, str] = {}
for full in SHIMANE_GUN_TOWNS:
    m = re.match(r"^.+郡(.+)$", full)
    if m:
        bare = m.group(1)
        # 同じ bare 名が複数の郡に存在しないことを前提（島根県は問題なし）
        _BARE_TO_CANONICAL[bare] = full

_MUNI_CANDIDATES = sorted(MUNICIPALITY_ORDER, key=len, reverse=True)
_BARE_CANDIDATES = sorted(_BARE_TO_CANONICAL, key=len, reverse=True)


def infer_municipality(address: str) -> str:
    text = address
    if text.startswith("島根県"):
        text = text[len("島根県"):]
    # First pass: try full canonical names (including 郡+町村) in descending length order
    for cand in _MUNI_CANDIDATES:
        if text.startswith(cand):
            return cand
    # Second pass: for 郡部 try matching bare town/village part
    # IMPORTANT: try longer bare names first to avoid 北村山郡大石田町 → 北村 false match
    for bare in _BARE_CANDIDATES:
        if text.startswith(bare):
            return _BARE_TO_CANONICAL[bare]
    # Third pass: for 市 names try direct match (already covered above, but just in case)
    for cand in SHIMANE_CITIES:
        if text.startswith(cand):
            return cand
    return ""


SCHOOL_TYPE_ORDER = [
    "幼稚園", "小学校", "中学校", "義務教育学校",
    "高等学校", "中等教育学校", "特別支援学校",
]

WARNINGS: list[dict[str, str]] = []


def warn(context: str, message: str) -> None:
    WARNINGS.append({"context": context, "message": message})


# ---------------------------------------------------------------------------
# 正式名称構築（山梨・茨城・栃木版の反省を踏まえた核心処理）
# ---------------------------------------------------------------------------

COMPLETE_NAME_SUFFIXES = (
    "幼稚園", "小学校", "中学校", "義務教育学校", "高等学校", "中等教育学校",
    "特別支援学校", "聾学校", "盲学校", "養護学校", "学園", "学院", "学部",
    "中等部", "小学部", "こども園", "キンダーガーテン", "分校", "分教室",
)

_SHIMANE_MUNI_NAMES = {re.sub(r"^.+郡", "", m) for m in MUNICIPALITY_ORDER}
_SHIMANE_MUNI_NAMES.update(SHIMANE_CITIES)


def build_official_name(*, establishment: str, raw_name: str,
                        municipality: str, school_type: str) -> str:
    """正式名称を構築する。略称排除を最優先とする。

    重要なケース:
    1. 既に校種サフィックスで終わる名称はそのまま（重複防止）
    2. MEXT名称が「○○市立△△高等学校」のように設置者を含む場合は
       「島根県立」を重ねて付けない（市立商業高等学校等）
    3. 分校名（「〜○○校」等）は「立」を含む完全な固有名称
       → 校種サフィックスを追加しない
    """
    raw_name = normalize_name(raw_name)

    # 既に完全な名称（校種サフィックスあり）の場合はサフィックス重複を防ぐ
    already_complete = any(raw_name.endswith(s) for s in COMPLETE_NAME_SUFFIXES)

    if establishment == "国立":
        # 国立はすでに「○○大学附属××学校」形式で正式名称
        return raw_name if already_complete else raw_name + school_type

    if establishment == "私立":
        # 私立は法人固有名称をそのまま使用
        return raw_name if already_complete else raw_name + school_type

    # 公立
    # ----- 既に設置者表現（○立）を含む場合はそのまま返す -----
    # 例: 「○○市立商業高等学校」「島根県立○○中学校」
    # 「島根県立○○特別支援学校○○校」（分校も含む）
    if re.search(r'[都道府県市区町村]立', raw_name):
        # 分校名「〜○○校」で且つ校種サフィックスなし → 校種付けず分校名をそのまま
        if re.search(r'校$', raw_name) and not already_complete:
            return raw_name  # 「〜○○校」等、校種は不要
        return raw_name if already_complete else raw_name + school_type

    # 公立: 県立か市町村立かを判定
    is_pref_level = school_type in ("高等学校", "中等教育学校", "特別支援学校")

    if is_pref_level:
        core = f"島根県立{raw_name}"
        return core if already_complete else core + school_type

    # 市町村立（幼稚園・小・中・義務教育）
    bare_muni = re.sub(r"^.+郡", "", municipality)  # 郡名なし

    # raw_name がすでに自治体名を含む場合
    for mname in _SHIMANE_MUNI_NAMES:
        if raw_name.startswith(mname + "立") or raw_name.startswith(mname):
            return raw_name if already_complete else raw_name + school_type

    # 通常の組み立て（自治体名 + 立 + 学校名 + 校種）
    core = f"{bare_muni}立{raw_name}"
    return core if already_complete else core + school_type


# ---------------------------------------------------------------------------
# レコード生成
# ---------------------------------------------------------------------------

SOURCE_NAME = "文部科学省 学校コード一覧（公立・国立・私立学校等）"
SOURCE_URL = "https://www.mext.go.jp/b_menu/toukei/mext_01087.html"
SOURCE_DATE = "2026-05-29"

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


def make_record(
    *, name: str, name_kana: str, postal_code: str, address: str,
    school_type: str, establishment: str, operator: str, phone: str,
    website: str, source_name: str, source_url: str, source_date: str,
    course: list[str],
) -> dict[str, Any]:
    name = normalize_name(name)
    address = normalize_address(address)
    municipality = infer_municipality(address)
    stable_key = "|".join((establishment, school_type, municipality, name, ",".join(course)))
    return {
        "id": f"shimane-{slug(stable_key)}",
        "prefecture": "島根県",
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
# データ読み込み
# ---------------------------------------------------------------------------

def load_mext_data(source_root: Path) -> list[dict[str, Any]]:
    # Find latest MEXT file in source_root or tochigi dir
    candidates = [
        source_root / "sc_20260529-mxt_chousa01-000011635_3.xlsx",
        Path("data-source/tochigi") / "sc_20260529-mxt_chousa01-000011635_3.xlsx",
    ]
    excel_path = None
    for c in candidates:
        if c.exists():
            excel_path = c
            break

    if excel_path is None:
        warn("source_load", "MEXT Excel not found")
        return []

    print(f"Reading: {excel_path}")
    df = pd.read_excel(excel_path, header=1, dtype=str)
    df.columns = [c.replace("\n", "").strip() for c in df.columns]

    yama = df[df["都道府県番号"].fillna("").str.startswith("32(")].copy()

    # 廃止校を除外
    active = yama[yama["属性情報廃止年月日"].isna() | (yama["属性情報廃止年月日"] == "nan")]

    records: list[dict[str, Any]] = []
    skipped = 0
    for idx, row in active.iterrows():
        raw_type = str(row.get("学校種", "")).strip()
        raw_est = str(row.get("設置区分", "")).strip()

        if raw_type not in TYPE_MAPPING:
            skipped += 1
            continue
        if raw_est not in ESTABLISHMENT_MAPPING:
            skipped += 1
            continue

        school_type = TYPE_MAPPING[raw_type]
        est_type = ESTABLISHMENT_MAPPING[raw_est]

        raw_name = normalize_name(str(row.get("学校名", "")))
        raw_addr = normalize_address(str(row.get("学校所在地", "")))
        raw_postal = str(row.get("郵便番号", ""))

        if not raw_name or raw_name == "nan" or not raw_addr:
            warn(f"row_{idx}", f"Empty name or address: name={raw_name}")
            continue

        municipality = infer_municipality(raw_addr)
        if not municipality:
            warn(f"row_{idx}", f"Could not infer municipality from: {raw_addr}")

        official_name = build_official_name(
            establishment=est_type,
            raw_name=raw_name,
            municipality=municipality,
            school_type=school_type,
        )

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
            course=[],
        )
        records.append(record)

    print(f"Loaded {len(records)} records (skipped {skipped} out-of-scope)")
    return records


# ---------------------------------------------------------------------------
# 重複排除とソート
# ---------------------------------------------------------------------------

def deduplicate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        rid = record["id"]
        if rid not in by_id:
            by_id[rid] = record
            continue
        suffix = 2
        while f"{rid}-{suffix}" in by_id:
            suffix += 1
        record["id"] = f"{rid}-{suffix}"
        by_id[record["id"]] = record
    return list(by_id.values())


def sort_key(record: dict[str, Any]):
    m_idx = MUNICIPALITY_ORDER.index(record["municipality"]) if record["municipality"] in MUNICIPALITY_ORDER else 999
    t_idx = SCHOOL_TYPE_ORDER.index(record["school_type"]) if record["school_type"] in SCHOOL_TYPE_ORDER else 999
    return (m_idx, t_idx, record["name"])


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path("data-source/tochigi"))
    parser.add_argument("--output", type=Path, default=Path("data/school-database/shimane.json"))
    parser.add_argument("--warnings-output", type=Path,
                        default=Path("tools/school-database/shimane_conversion_warnings.json"))
    args = parser.parse_args()

    all_records = load_mext_data(args.source_root)
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
