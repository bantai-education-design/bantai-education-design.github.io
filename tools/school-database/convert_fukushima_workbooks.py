#!/usr/bin/env python3
"""福島県公式PDF/CSV名簿を学校検索用JSONへ変換する。

原本は data-source/fukushima/2025/ に置く（Git管理外）。

千葉県版・神奈川県版と異なり、福島県教育委員会の公開資料はExcelではなく
PDF（市町村立小学校・中学校・義務教育学校・市町村立特別支援学校）と
CSV（県立高等学校・県立中学校・県立特別支援学校・分校・校舎）が中心。
私立学校名簿（高等学校・中学校/小学校・幼稚園）もPDFのみで、基準日は
令和7年5月1日（県立・市町村立は令和8年4月1日）と1年古い。専修学校・
各種学校は他県版と同様に初版対象外とする。

学校種の扱い:
  - 県立高等学校・特別支援学校・中学校は1つのCSV
    「県立学校連絡先一覧」にまとまっている。カテゴリ見出し（１）〜（４）で
    高等学校/中学校/分校/校舎・協力校を判別し、校名に「支援」を含む行は
    特別支援学校として扱う。
  - 分校は見出し行（住所欄が空）で親校名を保持し、以降の番号付き行に
    「親校名+分校名」で連結する。ただし校名列に既に「学校」を含む場合は
    その校名を単独の正式名称として扱う（親名を連結しない）。
  - 「休校中」の分校（浪江高等学校津島校）は除外する。
  - 国立 福島大学附属特別支援学校は原本PDFが自由記述形式のため、
    このスクリプト内に直接値を保持する（1校のみの例外的な手当て）。
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


def normalize_phone_simple(value: Any) -> str:
    """既に「024-523-1366」のような半角形式の電話番号を整形する（市町村立PDF用）。
    「024-557-0135・1614」のように内線・複数番号が「・」等で併記されている場合は
    代表番号（先頭の番号）のみを採用する。"""
    if value is None:
        return ""
    text = normalize_text(value)
    if text in ("", "-", "―", "ー"):
        return ""
    text = text.replace("−", "-").replace("―", "-").replace("ー", "-")
    text = re.sub(r"[（(]代[）)]|㈹", "", text)
    text = re.split(r"[・/]", text)[0]
    digits_and_dash = re.sub(r"[^\d-]", "", text)
    return digits_and_dash


def normalize_address(value: Any) -> str:
    text = normalize_text(value)
    text = text.replace("−", "-").replace("―", "-")
    if text and not text.startswith("福島県"):
        text = "福島県" + text
    return text


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"[^0-9a-zぁ-んァ-ヶ一-龠]+", "-", normalized).strip("-")
    return normalized or "school"


# ---------------------------------------------------------------------------
# 市町村表示順（県北 -> 県中 -> 県南 -> 会津 -> 南会津 -> 相双 -> いわき、
# 福島県の広域振興局区分に準拠）
# ---------------------------------------------------------------------------

KENPOKU = [
    "福島市", "二本松市", "伊達市", "本宮市",
    "伊達郡桑折町", "伊達郡国見町", "伊達郡川俣町", "安達郡大玉村",
]
KENCHU = [
    "郡山市", "須賀川市", "田村市",
    "岩瀬郡鏡石町", "岩瀬郡天栄村",
    "石川郡石川町", "石川郡玉川村", "石川郡平田村", "石川郡浅川町", "石川郡古殿町",
    "田村郡三春町", "田村郡小野町",
]
KENNAN = [
    "白河市",
    "西白河郡西郷村", "西白河郡泉崎村", "西白河郡中島村", "西白河郡矢吹町",
    "東白川郡棚倉町", "東白川郡矢祭町", "東白川郡塙町", "東白川郡鮫川村",
]
AIZU = [
    "会津若松市", "喜多方市",
    "耶麻郡北塩原村", "耶麻郡西会津町", "耶麻郡磐梯町", "耶麻郡猪苗代町",
    "河沼郡会津坂下町", "河沼郡湯川村", "河沼郡柳津町",
    "大沼郡三島町", "大沼郡金山町", "大沼郡昭和村", "大沼郡会津美里町",
]
MINAMI_AIZU = [
    "南会津郡下郷町", "南会津郡檜枝岐村", "南会津郡只見町", "南会津郡南会津町",
]
SOSO = [
    "相馬市", "南相馬市",
    "相馬郡新地町", "相馬郡飯舘村",
    "双葉郡広野町", "双葉郡楢葉町", "双葉郡富岡町", "双葉郡川内村",
    "双葉郡大熊町", "双葉郡双葉町", "双葉郡浪江町", "双葉郡葛尾村",
]
IWAKI = ["いわき市"]

MUNICIPALITY_ORDER = KENPOKU + KENCHU + KENNAN + AIZU + MINAMI_AIZU + SOSO + IWAKI

_BARE_TOWN_TO_CANONICAL = {
    re.match(r"(伊達郡|安達郡|岩瀬郡|石川郡|田村郡|西白河郡|東白川郡|耶麻郡|河沼郡|大沼郡|南会津郡|相馬郡|双葉郡)(.+)", t).group(2): t
    for t in MUNICIPALITY_ORDER if re.match(r"(伊達郡|安達郡|岩瀬郡|石川郡|田村郡|西白河郡|東白川郡|耶麻郡|河沼郡|大沼郡|南会津郡|相馬郡|双葉郡)(.+)", t)
}
_MUNICIPALITY_CANDIDATES = sorted(MUNICIPALITY_ORDER, key=len, reverse=True)
_BARE_TOWN_CANDIDATES = sorted(_BARE_TOWN_TO_CANONICAL, key=len, reverse=True)

# 南相馬市の行政区（原町区・鹿島区・小高区）は市町村フィルターとしては
# 南相馬市に統合する（政令指定都市ではないため区単位の分割は行わない）。
WARD_STRIP_RE = re.compile(r"(南相馬市)(原町区|鹿島区|小高区)")


def infer_municipality(address: str) -> str:
    text = address
    if text.startswith("福島県"):
        text = text[len("福島県"):]
    text = WARD_STRIP_RE.sub(r"\1", text)
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


def is_suspended_notice(*values: Any) -> bool:
    for value in values:
        text = re.sub(r"[ \t　]+", "", normalize_text(value))
        if any(keyword in text for keyword in ("休園", "休校", "休止", "休部")):
            return True
    return False


class WarningLog:
    def __init__(self) -> None:
        self.items: list[dict[str, str]] = []

    def add(self, context: str, message: str) -> None:
        self.items.append({"context": context, "message": message})


WARNINGS = WarningLog()


def make_record(
    *, name: str, name_kana: str = "", postal_code: str, address: str, school_type: str,
    establishment: str, operator: str, phone: str, website: str,
    source_name: str, source_url: str, source_date: str, course: list[str] | None = None,
) -> dict[str, Any]:
    name = normalize_name(name)
    address = normalize_address(address)
    municipality = infer_municipality(address)
    course = course or []
    stable_key = "|".join((establishment, school_type, municipality, name, ",".join(course)))
    return {
        "id": f"fukushima-{slug(stable_key)}",
        "prefecture": "福島県",
        "name": name,
        "name_kana": normalize_name(name_kana),
        "postal_code": normalize_postal_code(postal_code),
        "address": address,
        "municipality": municipality,
        "school_type": school_type,
        "establishment": establishment,
        "operator": normalize_name(operator),
        "phone": phone,
        "website": website,
        "source_name": source_name,
        "source_url": source_url,
        "source_date": source_date,
        "verified_date": "",
        "course": list(course),
    }


# ---------------------------------------------------------------------------
# 市町村立PDF読み込み（小学校・中学校・義務教育学校・市町村立特別支援学校）
# 表構造は共通: [番号, 学校名, 郵便番号, 所在地, 電話番号]
# ---------------------------------------------------------------------------

MUNICIPAL_SOURCE_DATE = "2026-04-01"
MUNICIPAL_SOURCE_URL = "https://www.pref.fukushima.lg.jp/site/edu/sityousongakkol.html"


def read_municipal_pdf(path: Path, *, school_type: str, source_name: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 5:
                        continue
                    number, name, postal, address, phone = row[0], row[1], row[2], row[3], row[4]
                    name = normalize_name(name)
                    if not name or name in ("学　校　名", "学校名"):
                        continue
                    address = normalize_text(address)
                    if not address:
                        continue
                    if is_suspended_notice(phone):
                        WARNINGS.add("suspended", f"休園・休校中のため除外: {name}（{path.name}）")
                        continue
                    address = normalize_address(address)
                    municipality = infer_municipality(address)
                    record = make_record(
                        name=name,
                        postal_code=postal,
                        address=address,
                        school_type=school_type,
                        establishment="公立",
                        operator=municipality,
                        phone=normalize_phone_simple(phone),
                        website="",
                        source_name=source_name,
                        source_url=MUNICIPAL_SOURCE_URL,
                        source_date=MUNICIPAL_SOURCE_DATE,
                    )
                    records.append(record)
    return records


MUNICIPAL_FILE_SPECS = [
    dict(file="r8_shityouson_shou.pdf", school_type="小学校",
         source_name="福島県市町村立学校一覧 小学校（令和8年4月1日現在）"),
    dict(file="r8_shityouson_chu.pdf", school_type="中学校",
         source_name="福島県市町村立学校一覧 中学校（令和8年4月1日現在）"),
    dict(file="r8_shityouson_gimukyoiku.pdf", school_type="義務教育学校",
         source_name="福島県市町村立学校一覧 義務教育学校（令和8年4月1日現在）"),
    dict(file="r8_shiritsuritsu_tokubetsushien.pdf", school_type="特別支援学校",
         source_name="福島県市町村立特別支援学校一覧（令和8年4月1日現在）"),
]


# ---------------------------------------------------------------------------
# 県立学校連絡先一覧CSV読み込み（高等学校・中学校・特別支援学校・分校・校舎）
# ---------------------------------------------------------------------------

PREF_CSV_SOURCE_NAME = "福島県立学校等一覧（令和8年4月1日現在）"
PREF_CSV_SOURCE_URL = "https://www.pref.fukushima.lg.jp/site/edu/kenritu.html"
PREF_CSV_SOURCE_DATE = "2026-04-01"

AREA_CODE_PATTERN = re.compile(r"^\d{2,4}$")


def build_phone(area_code_cell: Any, phone_cell: Any) -> str:
    area = normalize_text(area_code_cell)
    local = normalize_text(phone_cell)
    local = re.sub(r"[（(]代[）)]|㈹", "", local)
    if not AREA_CODE_PATTERN.fullmatch(area) or not local:
        return ""
    area_full = f"0{area}"
    local = local.replace("－", "-").replace("―", "-")
    if not re.fullmatch(r"\d{2,4}-\d{3,4}", local):
        return ""
    return f"{area_full}-{local}"


def read_prefectural_csv(path: Path) -> list[dict[str, Any]]:
    data = path.read_bytes().decode("cp932")
    lines = data.splitlines()
    rows = [line.split(",") for line in lines]

    records: list[dict[str, Any]] = []
    category = ""
    current_parent = ""       # カテゴリ（３）の見出し行（親校名のみ）用
    current_parent_full = ""  # カテゴリ（１）の直近の番号付き行（正式校名）用、無番号の校舎行に連結する
    current_parent_is_tokubetsu = False

    for row in rows:
        cells = [c.strip() for c in row] + [""] * (7 - len(row))
        col0, col1, col2, col3, col4, col5, col6 = cells[:7]

        if col0.startswith("（") or "県立学校連絡先一覧" in col0:
            if any(k in col0 for k in ("高等学校", "中学校", "分校", "校舎")):
                category = col0
                current_parent = ""
                current_parent_full = ""
                current_parent_is_tokubetsu = False
            continue
        if col1 in ("学　校　名", "学校名（協力校）"):
            continue
        if not col1:
            continue

        number, name, postal, address = col0, col1, col2, col3

        if category == "（３）県立学校の分校":
            if not address:
                # 見出し行（親校名のみ）: 以降の番号行に連結する
                current_parent = name
                continue
            if "学校" in name:
                full_name = name
                current_parent = ""
            else:
                full_name = f"{current_parent}{name}" if current_parent else name
        elif category == "（１）県立高等学校・特別支援学校" and not number and address:
            # 番号なし行 = 直前の学校の校舎（例:「（四倉校舎）」「小野校舎」）
            annex = re.sub(r"^[（(]|[）)]$", "", name)
            full_name = f"{current_parent_full}{annex}" if current_parent_full else name
        else:
            full_name = name

        if not address:
            continue

        if is_suspended_notice(col4, col5):
            WARNINGS.add("suspended", f"休校中のため除外: {full_name}（県立学校連絡先一覧）")
            continue

        is_tokubetsu = "支援" in name or (current_parent and "支援" in current_parent)

        if category == "（１）県立高等学校・特別支援学校":
            if number:
                if is_tokubetsu:
                    school_type = "特別支援学校"
                    if not full_name.endswith("学校"):
                        full_name = full_name + "学校"
                else:
                    school_type = "高等学校"
                    if not full_name.endswith("高等学校"):
                        full_name = full_name + "高等学校"
                current_parent_full = full_name
                current_parent_is_tokubetsu = is_tokubetsu
            else:
                school_type = "特別支援学校" if current_parent_is_tokubetsu else "高等学校"
        elif category == "（２）県立中学校":
            school_type = "中学校"
        elif category == "（３）県立学校の分校":
            school_type = "特別支援学校" if is_tokubetsu else "高等学校"
        elif category == "（４）県立学校の校舎及び協力校":
            school_type = "特別支援学校" if is_tokubetsu else "高等学校"
            base_match = re.match(r"^([^（(]+)([（(].+[）)])$", full_name)
            if base_match:
                base, paren = base_match.groups()
                if not base.endswith("学校"):
                    full_name = base + "学校" + paren
        else:
            WARNINGS.add("unknown-category", f"未分類のカテゴリ行をスキップ: {row}")
            continue

        phone = build_phone(col4, col5)

        record = make_record(
            name=full_name,
            postal_code=postal,
            address=address,
            school_type=school_type,
            establishment="公立",
            operator="福島県",
            phone=phone,
            website="",
            source_name=PREF_CSV_SOURCE_NAME,
            source_url=PREF_CSV_SOURCE_URL,
            source_date=PREF_CSV_SOURCE_DATE,
        )
        records.append(record)

    return records


# ---------------------------------------------------------------------------
# 国立 福島大学附属特別支援学校（原本PDFが自由記述形式のため直接記載する例外）
# ---------------------------------------------------------------------------

def national_special_needs_school() -> dict[str, Any]:
    return make_record(
        name="福島大学附属特別支援学校",
        postal_code="960-8164",
        address="福島市八木田字並柳71",
        school_type="特別支援学校",
        establishment="国立",
        operator="国立大学法人福島大学",
        phone="024-546-0535",
        website="https://www.ash.fukushima-u.ac.jp/index",
        source_name="福島県特別支援学校一覧（令和8年4月1日現在）",
        source_url="https://www.pref.fukushima.lg.jp/site/edu/tokubetsushien03.html",
        source_date="2026-04-01",
    )


# ---------------------------------------------------------------------------
# 私立学校PDF読み込み（高等学校・中学校/小学校・幼稚園）
# ---------------------------------------------------------------------------

PRIVATE_SOURCE_DATE = "2025-05-01"
PRIVATE_SOURCE_URL = "https://www.pref.fukushima.lg.jp/sec/01135b/shigaku13.html"

CORPORATE_NUMBER_RE = re.compile(r"^\d{13}$")
PHONE_LINE_RE = re.compile(r"^0\d{1,4}[-‐]\d{1,4}[-‐]\d{3,4}$")


def parse_name_operator_cell(cell: str) -> tuple[str, str]:
    lines = [normalize_text(x) for x in cell.split("\n") if normalize_text(x)]
    if not lines:
        return "", ""
    name = lines[0]
    rest = lines[1:]
    operator_parts = [
        line for line in rest
        if not CORPORATE_NUMBER_RE.match(line) and not PHONE_LINE_RE.match(line)
    ]
    operator = "".join(operator_parts)
    return name, operator


def parse_location_cell(cell: str) -> tuple[str, str, str]:
    lines = [normalize_text(x) for x in cell.split("\n") if normalize_text(x)]
    postal = ""
    address = ""
    phone = ""
    for line in lines:
        if line.startswith("〒") and not postal:
            postal = line.replace("〒", "")
            continue
        if PHONE_LINE_RE.match(line.replace("‐", "-")) and not phone:
            phone = line.replace("‐", "-")
            continue
        if not postal and re.match(r"^\d{3}-?\d{4}$", line):
            postal = line
            continue
        if not address and not line.startswith("0"):
            address = line
    return postal, address, phone


def read_private_5col_pdf(path: Path, *, school_type: str, source_name: str) -> list[dict[str, Any]]:
    """高等学校・中学校/小学校の私立名簿（5列: 番号,学校名等,校長等,定員,所在地等）。"""
    records: list[dict[str, Any]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 5:
                        continue
                    number_cell = normalize_text(row[0])
                    if not re.match(r"^\d+$", number_cell):
                        continue
                    name_cell = row[1] or ""
                    location_cell = row[4] or ""
                    name, operator = parse_name_operator_cell(name_cell)
                    if not name:
                        continue
                    postal, address, phone = parse_location_cell(location_cell)
                    if not address:
                        WARNINGS.add("private-parse", f"住所未検出のためスキップ: {name}（{path.name}）")
                        continue
                    record = make_record(
                        name=name,
                        postal_code=postal,
                        address=address,
                        school_type=school_type,
                        establishment="私立",
                        operator=operator,
                        phone=phone,
                        website="",
                        source_name=source_name,
                        source_url=PRIVATE_SOURCE_URL,
                        source_date=PRIVATE_SOURCE_DATE,
                    )
                    records.append(record)
    return records


def read_private_chu_shou_pdf(path: Path) -> list[dict[str, Any]]:
    """中学校・小学校が1ファイルに混在する私立名簿。番号帯（4001〜/5001〜等）や
    学校名末尾（中学校/小学校）で校種を判定する。"""
    records: list[dict[str, Any]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 5:
                        continue
                    number_cell = normalize_text(row[0])
                    if not re.match(r"^\d+$", number_cell):
                        continue
                    name_cell = row[1] or ""
                    location_cell = row[4] or ""
                    name, operator = parse_name_operator_cell(name_cell)
                    if not name:
                        continue
                    if name.endswith("小学校"):
                        school_type = "小学校"
                    elif name.endswith("中学校"):
                        school_type = "中学校"
                    else:
                        WARNINGS.add("private-parse", f"校種未判定のためスキップ: {name}（{path.name}）")
                        continue
                    postal, address, phone = parse_location_cell(location_cell)
                    if not address:
                        WARNINGS.add("private-parse", f"住所未検出のためスキップ: {name}（{path.name}）")
                        continue
                    record = make_record(
                        name=name,
                        postal_code=postal,
                        address=address,
                        school_type=school_type,
                        establishment="私立",
                        operator=operator,
                        phone=phone,
                        website="",
                        source_name="福島県私立学校名簿 中学校・小学校（令和7年5月1日現在）",
                        source_url=PRIVATE_SOURCE_URL,
                        source_date=PRIVATE_SOURCE_DATE,
                    )
                    records.append(record)
    return records


def read_private_youchien_pdf(path: Path) -> list[dict[str, Any]]:
    """幼稚園の私立名簿（7列: 番号,区分,園名等,園長,認可年月日,定員,所在地等）。"""
    records: list[dict[str, Any]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 7:
                        continue
                    number_cell = normalize_text(row[0])
                    if not re.match(r"^\d+$", number_cell):
                        continue
                    name_cell = row[2] or ""
                    location_cell = row[6] or ""
                    name, operator = parse_name_operator_cell(name_cell)
                    if not name:
                        continue
                    postal, address, phone = parse_location_cell(location_cell)
                    if not address:
                        WARNINGS.add("private-parse", f"住所未検出のためスキップ: {name}（{path.name}）")
                        continue
                    record = make_record(
                        name=name,
                        postal_code=postal,
                        address=address,
                        school_type="幼稚園",
                        establishment="私立",
                        operator=operator,
                        phone=phone,
                        website="",
                        source_name="福島県私立学校名簿 幼稚園（令和7年5月1日現在）",
                        source_url=PRIVATE_SOURCE_URL,
                        source_date=PRIVATE_SOURCE_DATE,
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
    parser.add_argument("--source-root", type=Path, default=Path("data-source/fukushima/2025"))
    parser.add_argument("--output", type=Path, default=Path("data/school-database/fukushima.json"))
    parser.add_argument("--warnings-output", type=Path,
                         default=Path("tools/school-database/fukushima_conversion_warnings.json"))
    args = parser.parse_args()

    all_records: list[dict[str, Any]] = []

    for spec in MUNICIPAL_FILE_SPECS:
        path = args.source_root / spec["file"]
        if not path.exists():
            WARNINGS.add("municipal", f"SKIP missing: {path}")
            continue
        records = read_municipal_pdf(path, school_type=spec["school_type"], source_name=spec["source_name"])
        print(f"{spec['file']}: {len(records)} records")
        all_records.extend(records)

    pref_csv_path = args.source_root / "r8_kenritsu_gakkou_ichiran.csv"
    if pref_csv_path.exists():
        pref_records = read_prefectural_csv(pref_csv_path)
        print(f"{pref_csv_path.name}: {len(pref_records)} records")
        all_records.extend(pref_records)
    else:
        WARNINGS.add("prefectural", f"SKIP missing: {pref_csv_path}")

    all_records.append(national_special_needs_school())

    koukou_path = args.source_root / "r7_shiritsu_koukou.pdf"
    if koukou_path.exists():
        records = read_private_5col_pdf(
            koukou_path, school_type="高等学校",
            source_name="福島県私立学校名簿 高等学校（令和7年5月1日現在）",
        )
        print(f"{koukou_path.name}: {len(records)} records")
        all_records.extend(records)
    else:
        WARNINGS.add("private", f"SKIP missing: {koukou_path}")

    chu_shou_path = args.source_root / "r7_shiritsu_chu_shou.pdf"
    if chu_shou_path.exists():
        records = read_private_chu_shou_pdf(chu_shou_path)
        print(f"{chu_shou_path.name}: {len(records)} records")
        all_records.extend(records)
    else:
        WARNINGS.add("private", f"SKIP missing: {chu_shou_path}")

    youchien_path = args.source_root / "r7_shiritsu_youchien.pdf"
    if youchien_path.exists():
        records = read_private_youchien_pdf(youchien_path)
        print(f"{youchien_path.name}: {len(records)} records")
        all_records.extend(records)
    else:
        WARNINGS.add("private", f"SKIP missing: {youchien_path}")

    all_records = deduplicate(all_records)
    all_records.sort(key=sort_key)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(all_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {len(all_records)} records to {args.output}")

    args.warnings_output.parent.mkdir(parents=True, exist_ok=True)
    args.warnings_output.write_text(
        json.dumps(WARNINGS.items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(WARNINGS.items)} warnings to {args.warnings_output}")
    for item in WARNINGS.items[:50]:
        print(f"WARN [{item['context']}] {item['message']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
