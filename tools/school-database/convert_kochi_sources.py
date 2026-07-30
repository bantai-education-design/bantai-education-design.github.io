#!/usr/bin/env python3
"""高知県学校データベース変換スクリプト

原本: 文部科学省「学校コード一覧（全国公立・国立・私立学校等）」
      sc_20260529-mxt_chousa01-000011635_1.xlsx（2026-05-29版）

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
    if text and not text.startswith("高知県"):
        text = "高知県" + text
    return text


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"[^0-9a-zぁ-んァ-ヶ一-龠]+", "-", normalized).strip("-")
    return normalized or "school"


# ---------------------------------------------------------------------------
# 高知県 市区町村一覧（行政表示順）
# ---------------------------------------------------------------------------

FUKUI_CITIES = [
    "あわら市", "勝山市", "坂井市", "大野市", "小浜市", "敦賀市", "高知市", "越前市", "鯖江市"
]

FUKUI_GUN_TOWNS = [
    "三方上中郡若狭町", "三方郡美浜町", "三方郡美浜町河原市", "丹生郡越前町", "今立郡池田町", "南条郡南越前町", "吉田郡永平寺町", "吉田郡永平寺町市", "吉田郡永平寺町東古市", "大飯郡おおい町", "大飯郡高浜町"
]

MUNICIPALITY_ORDER = FUKUI_CITIES + FUKUI_GUN_TOWNS

# 郡名なし → 正式名称へのマッピング（分詞が重なる村名・町名の解決）
_BARE_TO_CANONICAL: dict[str, str] = {}
for full in FUKUI_GUN_TOWNS:
    m = re.match(r"^.+郡(.+)$", full)
    if m:
        bare = m.group(1)
        # 同じ bare 名が複数の郡に存在しないことを前提（高知県は問題なし）
        _BARE_TO_CANONICAL[bare] = full

_MUNI_CANDIDATES = sorted(MUNICIPALITY_ORDER, key=len, reverse=True)
_BARE_CANDIDATES = sorted(_BARE_TO_CANONICAL, key=len, reverse=True)


import re
def infer_municipality(address: str) -> str:
    text = address
    for pref_name in ["富山県", "徳島県", "愛媛県", "高知県", "高知県", "石川県", "滋賀県", "岐阜県", "三重県", "兵庫県", "岡山県", "山口県", "広島県", "鳥取県", "島根県"]:
        if text.startswith(pref_name):
            text = text[len(pref_name):]
    m = re.match(r'^([^郡]+市|[^郡]+区|.+?郡.+?[町村]|.+?[町村])', text)
    if m:
        return m.group(1)
    return ""

def infer_municipality_dummy(address: str) -> str:
    text = address
    if text.startswith("高知県"):
        text = text[len("高知県"):]
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
    for cand in FUKUI_CITIES:
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

_FUKUI_MUNI_NAMES = {re.sub(r"^.+郡", "", m) for m in MUNICIPALITY_ORDER}
_FUKUI_MUNI_NAMES.update(FUKUI_CITIES)


def build_official_name(*, establishment: str, raw_name: str,
                        municipality: str, school_type: str) -> str:
    """正式名称を構築する。略称排除を最優先とする。

    重要なケース:
    1. 既に校種サフィックスで終わる名称はそのまま（重複防止）
    2. MEXT名称が「○○市立△△高等学校」のように設置者を含む場合は
       「高知県立」を重ねて付けない（市立商業高等学校等）
    3. 分校名（「〜山形校」「〜金山校」等）は「立」を含む完全な固有名称
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
    # 例: 「山形市立商業高等学校」「高知県立致道館中学校」
    # 「高知県立村山特別支援学校山形校」（分校も含む）
    if re.search(r'[都道府県市区町村]立', raw_name):
        # 分校名「〜○○校」で且つ校種サフィックスなし → 校種付けず分校名をそのまま
        if re.search(r'校$', raw_name) and not already_complete:
            return raw_name  # 「〜山形校」「〜金山校」等、校種は不要
        return raw_name if already_complete else raw_name + school_type

    # 公立: 県立か市町村立かを判定
    is_pref_level = school_type in ("高等学校", "中等教育学校", "特別支援学校")

    if is_pref_level:
        core = f"高知県立{raw_name}"
        return core if already_complete else core + school_type

    # 市町村立（幼稚園・小・中・義務教育）
    bare_muni = re.sub(r"^.+郡", "", municipality)  # 郡名なし

    # raw_name がすでに自治体名を含む場合
    for mname in _FUKUI_MUNI_NAMES:
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
        "id": f"kochi-{slug(stable_key)}",
        "prefecture": "高知県",
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
    import pandas as pd
    files = ['sc_20260529-mxt_chousa01-000011635_1.xlsx', 'sc_20260529-mxt_chousa01-000011635_3.xlsx', 'sc_20260529-mxt_chousa01-000011635_5.xlsx']
    df_list = []
    for f in files:
        file_p = Path('data-source/tochigi') / f
        if file_p.exists():
            print(f'Reading: {file_p}')
            df = pd.read_excel(file_p, header=1, dtype=str)
            df.columns = [c.replace("\n", "").strip() for c in df.columns]
            df_list.append(df)
    
    if not df_list:
        warn("source_load", "MEXT Excel not found")
        return []
        
    df = pd.concat(df_list, ignore_index=True)

    yama = df[df["都道府県番号"] == "39(高知)"].copy()


    # 廃止校を除外
    
    col_name = "属性情報廃止年月日" if "属性情報廃止年月日" in yama.columns else "廃止年月日" if "廃止年月日" in yama.columns else None
    if col_name:
        active = yama[yama[col_name].isna() | (yama[col_name] == "nan")]
    else:
        active = yama
    

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
    parser.add_argument("--output", type=Path, default=Path("data/school-database/kochi.json"))
    parser.add_argument("--warnings-output", type=Path,
                        default=Path("tools/school-database/kochi_conversion_warnings.json"))
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