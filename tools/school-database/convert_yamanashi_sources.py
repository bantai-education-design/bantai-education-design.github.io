#!/usr/bin/env python3
"""山梨県公式PDF住所録を学校検索用JSONへ変換する。

原本は data-source/yamanashi/2025/ に置く（Git管理外）。千葉県版・神奈川県版と異なり、
山梨県は学校名簿がExcelではなくPDF（表形式）で公開されているため pdfplumber で
テーブル抽出する。

- r7_13_shogakko_address.pdf : 小学校（国・公・私立）住所録 令和7年5月1日現在
- r7_14_chugakko_address.pdf : 中学校（国・公・私立）住所録 令和7年5月1日現在
- r7_15_koukou_tokushi_address.pdf : 高等学校（公・私立）・特別支援学校 住所録
- r7_16_youchien_address.pdf : 幼稚園（私立中心）住所録
- shiritsu_gakkou_meibo.pdf : 私立学校名簿（令和7年4月1日現在、設置者・課程の確認用）

公立/私立/国立の判定は、住所録PDFに設置区分の列が無いため、私立学校名簿PDFに
掲載されている学校名（既知リスト）との突合、および「山梨大学附属」を国立とする
ルールで行う。高等学校の課程（全日制/定時制/通信制）は、名称に付く
「（定時制）」「（専攻科：…）」等の注記と、住所録内の別建て通信制一覧、
私立学校名簿の課程別一覧を突き合わせて判定する。
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
# 正規化ユーティリティ（千葉県版・神奈川県版と共通の設計）
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
    digits = re.sub(r"\D", "", str(value))
    if len(digits) == 7:
        return f"{digits[:3]}-{digits[3:]}"
    return normalize_text(value).replace("〒", "")


def normalize_phone(value: Any) -> str:
    if value is None:
        return ""
    text = normalize_text(value)
    if text in ("", "-", "―", "ー", "‐"):
        return ""
    text = text.replace("−", "-").replace("―", "-").replace("ー", "-").replace("‐", "-")
    return text


def normalize_address(value: Any) -> str:
    text = normalize_text(value)
    text = re.sub(r"[ \t　]+", "", text)
    text = text.replace("−", "-").replace("―", "-")
    if text and not text.startswith("山梨県"):
        text = "山梨県" + text
    return text


PAGE_MARKER_RE = re.compile(r"^\D*\d+/\d+\D*$")


def is_plausible_address(raw_value: Any) -> bool:
    """PDFの表抽出でページフッター（例:「幼稚園1/2」）がセルに混入した行を除外する。"""
    text = normalize_text(raw_value)
    if not text:
        return False
    if PAGE_MARKER_RE.match(text):
        return False
    return True


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"[^0-9a-zぁ-んァ-ヶ一-龠]+", "-", normalized).strip("-")
    return normalized or "school"


# ---------------------------------------------------------------------------
# 市町村表示順（市部 -> 郡部）
# ---------------------------------------------------------------------------

YAMANASHI_CITIES = [
    "甲府市", "富士吉田市", "都留市", "山梨市", "大月市", "韮崎市",
    "南アルプス市", "北杜市", "甲斐市", "笛吹市", "上野原市", "甲州市", "中央市",
]

YAMANASHI_GUN_TOWNS = [
    "中巨摩郡昭和町",
    "西八代郡市川三郷町",
    "南巨摩郡早川町", "南巨摩郡身延町", "南巨摩郡南部町", "南巨摩郡富士川町",
    "南都留郡道志村", "南都留郡西桂町", "南都留郡忍野村", "南都留郡山中湖村",
    "南都留郡鳴沢村", "南都留郡富士河口湖町",
    "北都留郡小菅村", "北都留郡丹波山村",
]

MUNICIPALITY_ORDER = YAMANASHI_CITIES + YAMANASHI_GUN_TOWNS

_BARE_TOWN_TO_CANONICAL = {
    re.match(r"(中巨摩郡|西八代郡|南巨摩郡|南都留郡|北都留郡)(.+)", t).group(2): t
    for t in YAMANASHI_GUN_TOWNS
}
_MUNICIPALITY_CANDIDATES = sorted(MUNICIPALITY_ORDER, key=len, reverse=True)
_BARE_TOWN_CANDIDATES = sorted(_BARE_TOWN_TO_CANONICAL, key=len, reverse=True)


def infer_municipality(address: str) -> str:
    text = address
    if text.startswith("山梨県"):
        text = text[len("山梨県"):]
    for candidate in _MUNICIPALITY_CANDIDATES:
        if text.startswith(candidate):
            return candidate
    for bare in _BARE_TOWN_CANDIDATES:
        if text.startswith(bare):
            return _BARE_TOWN_TO_CANONICAL[bare]
    return ""


SCHOOL_TYPE_ORDER = ["幼稚園", "小学校", "中学校", "高等学校", "特別支援学校"]

# 私立学校名簿PDF（shiritsu_gakkou_meibo.pdf）に掲載されている学校名から判定した
# 設置者区分。住所録PDFには設置区分の列が無いため、この既知リストとの突合で
# 私立・国立を判定する（それ以外は公立）。
NATIONAL_NAME_FRAGMENTS = ("山梨大学附属", "梨大附属")

PRIVATE_ELEMENTARY_NAMES = {"駿台甲府", "山梨学院", "南アルプス子どもの村", "素和美"}
PRIVATE_JUNIOR_HIGH_NAMES = {
    "山梨英和", "駿台甲府", "山梨学院", "日本航空高校付属", "日本航空高等学校付属",
    "富士学苑", "南アルプス子どもの村", "素和美",
}
PRIVATE_HIGH_SCHOOL_NAMES = {
    "山梨英和", "身延山", "甲斐清和", "駿台甲府", "山梨学院", "東海大学付属甲府",
    "日本航空", "日本大学明誠", "帝京第三", "富士学苑", "自然学園",
}
# 私立学校名簿PDFの「高等学校（広域通信制課程）」一覧に掲載されている学校名。
PRIVATE_HIGH_SCHOOL_CORRESPONDENCE_COURSE_NAMES = {
    "日本航空", "駿台甲府", "自然学園", "甲斐清和", "山梨学院", "山梨英和", "帝京第三",
}

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
        "id": f"yamanashi-{slug(stable_key)}",
        "prefecture": "山梨県",
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
# PDFテーブル抽出の共通処理
# ---------------------------------------------------------------------------

def extract_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    rows.append([normalize_text(c) for c in row])
    return rows


def is_data_row(row: list[str]) -> bool:
    if not row or not row[0]:
        return False
    if normalize_name(row[0]) in ("学校名", "幼稚園"):
        return False
    return True


# ---------------------------------------------------------------------------
# 小学校・中学校（住所録PDF、設置区分なし）
# ---------------------------------------------------------------------------

def classify_elementary_junior(name: str, school_type: str) -> str:
    known = PRIVATE_ELEMENTARY_NAMES if school_type == "小学校" else PRIVATE_JUNIOR_HIGH_NAMES
    if any(frag in name for frag in NATIONAL_NAME_FRAGMENTS):
        return "国立"
    if name in known:
        return "私立"
    return "公立"


def read_elementary_or_junior(
    path: Path, *, school_type: str, source_name: str, source_url: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in extract_rows(path):
        if not is_data_row(row):
            continue
        name = normalize_name(row[0])
        address = row[1] if len(row) > 1 else ""
        postal = row[2] if len(row) > 2 else ""
        phone = row[3] if len(row) > 3 else ""
        if not is_plausible_address(address):
            continue  # 所在地が空欄の行（閉校・注記のみの行）は除外
        if "分校" in name or "分教室" in name:
            # 本校と同一住所・電話のことが多く、初版では本校のみを収録する。
            warn("elementary_junior", f"分校のため収録対象外: {name}（{path.name}）")
            continue
        establishment = classify_elementary_junior(name, school_type)
        records.append(make_record(
            name=name, name_kana="", postal_code=postal, address=address,
            school_type=school_type, establishment=establishment, operator="",
            phone=phone, website="", source_name=source_name, source_url=source_url,
            source_date="2025-05-01", course=[],
        ))
    return records


# ---------------------------------------------------------------------------
# 高等学校・特別支援学校（住所録PDF、公私立混在・通信制は別建て一覧）
# ---------------------------------------------------------------------------

COURSE_SUFFIX_RE = re.compile(r"(.+?)[（(](定時制|専攻科[：:][^）)]*|通信制)[）)]$")


def classify_high_school(name: str) -> str:
    if any(frag in name for frag in NATIONAL_NAME_FRAGMENTS):
        return "国立"
    if name in PRIVATE_HIGH_SCHOOL_NAMES:
        return "私立"
    return "公立"


def read_koukou_tokushi(path: Path, source_url: str) -> list[dict[str, Any]]:
    rows = extract_rows(path)
    high_records: dict[str, dict[str, Any]] = {}
    tokushi_records: list[dict[str, Any]] = []
    correspondence_names: set[str] = set()

    section = "high_main"
    for row in rows:
        if not row or not row[0]:
            continue
        raw_name = normalize_name(row[0])
        if raw_name in ("学校名",):
            continue
        address = row[1] if len(row) > 1 else ""
        postal = row[2] if len(row) > 2 else ""
        phone = row[3] if len(row) > 3 else ""

        # セクション切り替え判定: 特別支援学校の校名は「支援」を含む
        if "支援" in raw_name or raw_name in ("盲", "ろう"):
            section = "tokushi"

        if section == "high_main":
            match = COURSE_SUFFIX_RE.match(raw_name)
            base_name = match.group(1) if match else raw_name
            suffix = match.group(2) if match else ""

            if suffix.startswith("専攻科"):
                # 専攻科は本校と同一学校のため別レコード化しない。
                continue

            if not is_plausible_address(address):
                # 通信制サブリストの2巡目のように所在地が省略される行は
                # 直前に処理した本体テーブルの通信制一覧とみなす。
                correspondence_names.add(base_name)
                continue

            establishment = classify_high_school(base_name)
            key = f"{establishment}|{base_name}"
            if key not in high_records:
                high_records[key] = make_record(
                    name=base_name, name_kana="", postal_code=postal, address=address,
                    school_type="高等学校", establishment=establishment, operator="",
                    phone=phone, website="", source_name="山梨県内の学校・学級・児童生徒数等 住所録【高校・通信・特別支援】（令和7年5月1日現在）",
                    source_url=source_url, source_date="2025-05-01", course=["全日制"],
                )
            if suffix == "定時制" and "定時制" not in high_records[key]["course"]:
                high_records[key]["course"].append("定時制")
        else:
            if not is_plausible_address(address):
                continue
            if "分校" in raw_name or "（" in raw_name and "分校" in raw_name:
                warn("tokushi", f"分校のため収録対象外: {raw_name}")
                continue
            establishment = "国立" if any(f in raw_name for f in NATIONAL_NAME_FRAGMENTS) else "公立"
            tokushi_records.append(make_record(
                name=raw_name, name_kana="", postal_code=postal, address=address,
                school_type="特別支援学校", establishment=establishment, operator="",
                phone=phone, website="",
                source_name="山梨県内の学校・学級・児童生徒数等 住所録【高校・通信・特別支援】（令和7年5月1日現在）",
                source_url=source_url, source_date="2025-05-01", course=[],
            ))

    for base_name in correspondence_names:
        for key, record in high_records.items():
            if key.endswith(f"|{base_name}") and "通信制" not in record["course"]:
                record["course"].append("通信制")

    # 私立学校名簿PDFで確認済みの通信制課程で、住所録の別建て一覧には
    # 反映されていなかったもの（帝京第三高校: 令和7年1月認可）を補正する。
    for key, record in high_records.items():
        if record["name"] in PRIVATE_HIGH_SCHOOL_CORRESPONDENCE_COURSE_NAMES and "通信制" not in record["course"]:
            record["course"].append("通信制")
            warn("course_override", f"{record['name']}: 私立学校名簿の通信制認可情報により課程を補正")

    return list(high_records.values()) + tokushi_records


# ---------------------------------------------------------------------------
# 幼稚園（住所録PDF、私立中心）
# ---------------------------------------------------------------------------

def read_youchien(path: Path, source_url: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in extract_rows(path):
        if not row or not row[0]:
            continue
        name = normalize_name(row[0])
        if name in ("幼稚園",):
            continue
        address = row[1] if len(row) > 1 else ""
        postal = row[2] if len(row) > 2 else ""
        phone = row[3] if len(row) > 3 else ""
        if not is_plausible_address(address):
            warn("youchien", f"所在地未掲載（閉園等）のため収録対象外: {name}")
            continue
        establishment = "国立" if any(f in name for f in NATIONAL_NAME_FRAGMENTS) else "私立"
        records.append(make_record(
            name=name, name_kana="", postal_code=postal, address=address,
            school_type="幼稚園", establishment=establishment, operator="",
            phone=phone, website="",
            source_name="山梨県内の学校・学級・児童生徒数等 住所録【幼稚園】（令和7年5月1日現在）",
            source_url=source_url, source_date="2025-05-01", course=[],
        ))
    return records


# ---------------------------------------------------------------------------
# 私立学校名簿PDFのみに掲載され、住所録PDFには収録されていない学校の補完
# （手作業で確認済みの値。理由は docs/school-database/yamanashi/source-manifest.md 参照）
# ---------------------------------------------------------------------------

MANUAL_ADDITIONS = [
    dict(
        name="素和美小学校", school_type="小学校", establishment="私立",
        operator="学校法人素和美国際教育学院", postal_code="401-0302",
        address="南都留郡富士河口湖町小立5703", phone="0555-72-3031",
        source_name="山梨県私立学校名簿（令和7年4月1日現在）",
        source_url="https://www.pref.yamanashi.jp/documents/34146/meibo-20250401.pdf",
        source_date="2025-04-01",
    ),
    dict(
        name="素和美中学校", school_type="中学校", establishment="私立",
        operator="学校法人素和美国際教育学院", postal_code="401-0302",
        address="南都留郡富士河口湖町小立5703", phone="0555-72-3031",
        source_name="山梨県私立学校名簿（令和7年4月1日現在）",
        source_url="https://www.pref.yamanashi.jp/documents/34146/meibo-20250401.pdf",
        source_date="2025-04-01",
    ),
]


def build_manual_additions() -> list[dict[str, Any]]:
    records = []
    for item in MANUAL_ADDITIONS:
        records.append(make_record(
            name=item["name"], name_kana="", postal_code=item["postal_code"],
            address=item["address"], school_type=item["school_type"],
            establishment=item["establishment"], operator=item["operator"],
            phone=item["phone"], website="", source_name=item["source_name"],
            source_url=item["source_url"], source_date=item["source_date"], course=[],
        ))
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
    parser.add_argument("--source-root", type=Path, default=Path("data-source/yamanashi/2025"))
    parser.add_argument("--output", type=Path, default=Path("data/school-database/yamanashi.json"))
    parser.add_argument("--warnings-output", type=Path,
                         default=Path("tools/school-database/yamanashi_conversion_warnings.json"))
    args = parser.parse_args()

    stat_base_url = "https://www.pref.yamanashi.jp/kyouiku/27458338247.html"

    all_records: list[dict[str, Any]] = []

    shogakko_path = args.source_root / "r7_13_shogakko_address.pdf"
    records = read_elementary_or_junior(
        shogakko_path, school_type="小学校",
        source_name="山梨県内の学校・学級・児童生徒数等 住所録【小学校】（令和7年5月1日現在）",
        source_url=stat_base_url,
    )
    print(f"{shogakko_path.name}: {len(records)} records")
    all_records.extend(records)

    chugakko_path = args.source_root / "r7_14_chugakko_address.pdf"
    records = read_elementary_or_junior(
        chugakko_path, school_type="中学校",
        source_name="山梨県内の学校・学級・児童生徒数等 住所録【中学校】（令和7年5月1日現在）",
        source_url=stat_base_url,
    )
    print(f"{chugakko_path.name}: {len(records)} records")
    all_records.extend(records)

    koukou_path = args.source_root / "r7_15_koukou_tokushi_address.pdf"
    records = read_koukou_tokushi(koukou_path, stat_base_url)
    print(f"{koukou_path.name}: {len(records)} records")
    all_records.extend(records)

    youchien_path = args.source_root / "r7_16_youchien_address.pdf"
    records = read_youchien(youchien_path, stat_base_url)
    print(f"{youchien_path.name}: {len(records)} records")
    all_records.extend(records)

    manual = build_manual_additions()
    print(f"manual additions: {len(manual)} records")
    all_records.extend(manual)

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
