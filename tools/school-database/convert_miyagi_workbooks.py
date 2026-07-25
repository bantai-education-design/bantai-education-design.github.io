#!/usr/bin/env python3
"""宮城県公式HTML/PDF名簿を学校検索用JSONへ変換する。

原本は data-source/miyagi/2025/ に置く（Git管理外）。

福島県版と異なり、宮城県教育委員会は公立小学校・中学校・義務教育学校・高等学校・
特別支援学校の名簿をダウンロードファイルではなくHTMLページに直接テーブルとして
掲載している（仙台市立を除く）。仙台市立学校は仙台市教育委員会のページに別途
HTMLテーブルで掲載されている。私立学校（幼稚園・小中高・特別支援）はPDF
（1ファイル26ページ、複数校種混在）。

学校種の扱い:
  - 県立高等学校・特別支援学校は koukou.html にまとまっている（学区ごとに
    forward-fillされた表と、国立→県立の順で1テーブルに混在する特別支援学校表）。
  - 仙台市立の高等学校・中等教育学校・幼稚園・特別支援学校は固定順4テーブルの
    ページから取得する（県のkoukou.htmlにある「市立学校名」表は仙台青陵中等教育
    学校1件のみで仙台市のページと重複するため使用しない）。
  - 私立名簿PDFは学校種ごとにページが分かれ、番号なし行は前の学校の続き
    （学科・定員の複数行）または休園判定用の市町村・休園見出し行。
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


PAREN_AREA_CODE_RE = re.compile(r"^(\d{2,4})\((\d{2,4})\)(\d{3,4})$")


def normalize_phone(value: Any, *, default_area_code: str | None = None) -> str:
    """「0224(25)3259」形式や、市外局番なしの「222-6279」形式(default_area_code指定時に補完)を
    「0224-25-3259」形式へ正規化する。"""
    if value is None:
        return ""
    text = normalize_text(value)
    if text in ("", "-", "―", "ー"):
        return ""
    text = text.replace("−", "-").replace("―", "-").replace("ー", "-")
    match = PAREN_AREA_CODE_RE.match(text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    if re.fullmatch(r"\d{2,4}-\d{2,4}-\d{3,4}", text):
        return text
    if default_area_code and re.fullmatch(r"\d{2,4}-\d{3,4}", text):
        return f"{default_area_code}-{text}"
    return text


def normalize_address(value: Any, *, prefix: str = "") -> str:
    text = normalize_text(value)
    text = text.replace("−", "-").replace("―", "-")
    text = text.replace("〒", "")
    text = re.sub(r"^\d{3}-?\d{4}", "", text)
    if prefix and text:
        # 「仙台市若林区」を付与する際、原本の住所欄が既に「若林区荒井三丁目...」の
        # ように区名から始まっている場合、単純に連結すると「仙台市若林区若林区…」と
        # 区名が重複してしまう。prefixの末尾から順に一致する部分を探し、
        # 未一致の先頭部分だけを付け足す。
        for i in range(len(prefix) + 1):
            if text.startswith(prefix[i:]):
                text = prefix[:i] + text
                break
    if text and not text.startswith("宮城県"):
        text = "宮城県" + text
    return text


def split_postal_and_address(value: Any) -> tuple[str, str]:
    """「〒981-0943青葉区国見六丁目52-1」のように郵便番号と住所が区切り文字なしで
    連結されたセルから、先頭の郵便番号(7桁)を分離する。"""
    text = normalize_text(value).replace("〒", "")
    match = re.match(r"^(\d{3})-?(\d{4})(.*)$", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}", match.group(3)
    return "", text


def strip_annotations(value: Any) -> str:
    """「（グーグルサイトへリンク）」「（公式サイトへリンク）」等の注記を除去する。"""
    text = normalize_text(value)
    text = re.sub(r"[（(][^（）()]*リンク[^（）()]*[）)]", "", text)
    return text.strip()


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"[^0-9a-zぁ-んァ-ヶ一-龠]+", "-", normalized).strip("-")
    return normalized or "school"


# ---------------------------------------------------------------------------
# 市町村表示順（仙台市各区 -> 県内主要市 -> 郡部、宮城県の一般的な地域区分に準拠）
# ---------------------------------------------------------------------------

SENDAI_WARDS = ["仙台市青葉区", "仙台市宮城野区", "仙台市若林区", "仙台市太白区", "仙台市泉区"]
CITIES = [
    "石巻市", "塩竈市", "気仙沼市", "白石市", "名取市", "角田市", "多賀城市",
    "岩沼市", "富谷市", "大崎市", "登米市", "栗原市", "東松島市",
]
GUN_TOWNS = [
    "刈田郡蔵王町", "刈田郡七ヶ宿町",
    "柴田郡大河原町", "柴田郡村田町", "柴田郡柴田町", "柴田郡川崎町",
    "伊具郡丸森町",
    "亘理郡亘理町", "亘理郡山元町",
    "宮城郡松島町", "宮城郡七ヶ浜町", "宮城郡利府町",
    "黒川郡大和町", "黒川郡大郷町", "黒川郡大衡村",
    "加美郡色麻町", "加美郡加美町",
    "遠田郡涌谷町", "遠田郡美里町",
    "牡鹿郡女川町",
    "本吉郡南三陸町",
]

MUNICIPALITY_ORDER = SENDAI_WARDS + CITIES + GUN_TOWNS

_BARE_TOWN_TO_CANONICAL = {
    re.match(r"(刈田郡|柴田郡|伊具郡|亘理郡|宮城郡|黒川郡|加美郡|遠田郡|牡鹿郡|本吉郡)(.+)", t).group(2): t
    for t in GUN_TOWNS
}
_MUNICIPALITY_CANDIDATES = sorted(MUNICIPALITY_ORDER, key=len, reverse=True)
_BARE_TOWN_CANDIDATES = sorted(_BARE_TOWN_TO_CANONICAL, key=len, reverse=True)


def infer_municipality(address: str) -> str:
    text = address
    if text.startswith("宮城県"):
        text = text[len("宮城県"):]
    for candidate in _MUNICIPALITY_CANDIDATES:
        if text.startswith(candidate):
            return candidate
    for bare in _BARE_TOWN_CANDIDATES:
        if text.startswith(bare):
            return _BARE_TOWN_TO_CANONICAL[bare]
    if text.startswith("仙台市"):
        return "仙台市"
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
        "id": f"miyagi-{slug(stable_key)}",
        "prefecture": "宮城県",
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
# 県公式ページ（小学校・中学校・義務教育学校）: forward-fillされた5列テーブル
# [所在地(市町村,forward-fill), 学校名(ふりがな), 電話番号, 郵便番号, 住所]
# ---------------------------------------------------------------------------

PREF_SOURCE_DATE = "2025-05-01"

NAME_READING_RE = re.compile(r"^(.*?)[（(]([^（）()]*)[）)]\s*$")


def parse_name_reading(raw: str) -> tuple[str, str]:
    text = normalize_text(raw)
    match = NAME_READING_RE.match(text)
    if match:
        name, reading = match.groups()
        # 「（グーグルサイトへリンク）」等は読みではない
        if "リンク" in reading or "サイト" in reading:
            return strip_annotations(text), ""
        return name.strip(), reading.strip()
    return text, ""


DUAL_COURSE_PHONE_RE = re.compile(r"^前期課程[（(]小[）)](.+?)後期課程[（(]中[）)](.+)$")


def parse_dual_course_phone(text: str) -> tuple[str, list[str]]:
    """義務教育学校で前期課程・後期課程の電話番号が区切りなく併記されている場合、
    「電話番号A / 電話番号B」形式（千葉県版の複数電話番号表記と同じ形式）に変換する。"""
    match = DUAL_COURSE_PHONE_RE.match(normalize_text(text))
    if not match:
        return normalize_phone(text), []
    phone_a = normalize_phone(match.group(1))
    phone_b = normalize_phone(match.group(2))
    return f"{phone_a} / {phone_b}", ["前期課程", "後期課程"]


def read_pref_simple_table_page(
    path: Path, *, school_type: str, source_name: str, source_url: str,
) -> list[dict[str, Any]]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    records: list[dict[str, Any]] = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        current_muni = ""
        for row in rows[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            # ごく一部の行に末尾の空セルが余分に付いている（原本のHTML入力ミス）ため、
            # 末尾の空セルを除去してから列数で判定する。除去しないと5セル扱いになり
            # 市町村欄がずれて学校名や電話番号が誤って市町村名として読まれてしまう。
            while cells and cells[-1] == "":
                cells.pop()
            # 所在地(市町村)列はrowspanで結合されているため、同じ市町村が続く行は
            # 4セルしか持たない（1セル目から既にname_cell）。5セルの行だけ市町村を更新する。
            if len(cells) >= 5:
                muni_cell, name_cell, phone_cell, postal_cell, address_cell = cells[:5]
                if muni_cell:
                    current_muni = muni_cell
            elif len(cells) == 4:
                name_cell, phone_cell, postal_cell, address_cell = cells[:4]
            else:
                continue
            if not name_cell:
                continue

            name, reading = parse_name_reading(name_cell)
            if is_suspended_notice(phone_cell):
                WARNINGS.add("suspended", f"休校中のため除外: {name}（{path.name}）")
                continue

            address = normalize_address(address_cell)
            phone, course = parse_dual_course_phone(phone_cell)
            record = make_record(
                name=name,
                name_kana=reading,
                postal_code=postal_cell,
                address=address,
                school_type=school_type,
                establishment="公立",
                operator=current_muni,
                phone=phone,
                website="",
                source_name=source_name,
                source_url=source_url,
                source_date=PREF_SOURCE_DATE,
                course=course,
            )
            records.append(record)
    return records


PREF_SIMPLE_PAGES = [
    dict(file="es.html", school_type="小学校",
         source_name="宮城県公立小学校一覧（仙台市立を除く、令和7年5月1日現在）",
         source_url="https://www.pref.miyagi.jp/site/kyouiku/es.html"),
    dict(file="lss.html", school_type="中学校",
         source_name="宮城県公立中学校一覧（仙台市立を除く、令和7年5月1日現在）",
         source_url="https://www.pref.miyagi.jp/site/kyouiku/lss.html"),
    dict(file="lss2.html", school_type="義務教育学校",
         source_name="宮城県公立義務教育学校一覧（仙台市立を除く、令和7年5月1日現在）",
         source_url="https://www.pref.miyagi.jp/site/kyouiku/lss2.html"),
]


# ---------------------------------------------------------------------------
# 県公式ページ（高等学校・特別支援学校）: koukou.html
# table0 = 県立高等学校（学区forward-fill、市立学校名は仙台市ページと重複するため未使用）
# table2 = 特別支援学校（国立→県立の順で1テーブルに混在、ヘッダー再掲行で区切り）
# ---------------------------------------------------------------------------

KOUKOU_SOURCE_NAME_HS = "宮城県立高等学校一覧（令和7年5月1日現在）"
KOUKOU_SOURCE_NAME_SN = "宮城県特別支援学校一覧（国立・県立、令和7年5月1日現在）"
KOUKOU_SOURCE_URL = "https://www.pref.miyagi.jp/site/kyouiku/koukou.html"


def read_pref_koukou_page(path: Path) -> list[dict[str, Any]]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    tables = soup.find_all("table")
    records: list[dict[str, Any]] = []

    # table0: 県立高等学校（学区列はrowspan結合のため4セルの行が続く）
    hs_table = tables[0]
    for row in hs_table.find_all("tr")[1:]:
        cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
        while cells and cells[-1] == "":
            cells.pop()
        if len(cells) >= 5:
            name_cell, phone_cell, postal_cell, address_cell = cells[1:5]
        elif len(cells) == 4:
            name_cell, phone_cell, postal_cell, address_cell = cells[:4]
        else:
            continue
        name_cell = strip_annotations(name_cell)
        if not name_cell:
            continue
        if not name_cell.startswith("宮城県"):
            # 「仙台工業高等学校」等、宮城県名を冠さない行は仙台市立高等学校で、
            # 仙台市の公式ページ（sendai_koukou_chuto_youchien_tokushi.html）と
            # 重複するためスキップする。
            continue
        if is_suspended_notice(phone_cell):
            WARNINGS.add("suspended", f"休校中のため除外: {name_cell}（{path.name}）")
            continue
        course = []
        m = re.search(r"[（(]([^（）()]*(?:全日制|定時制|通信制)[^（）()]*)[）)]", name_cell)
        if m:
            course = [c for c in re.split(r"[・,、]", m.group(1)) if c]
            name_cell = name_cell[: m.start()].strip()
        record = make_record(
            name=name_cell,
            postal_code=postal_cell,
            address=address_cell,
            school_type="高等学校",
            establishment="公立",
            operator="宮城県",
            phone=normalize_phone(phone_cell),
            website="",
            source_name=KOUKOU_SOURCE_NAME_HS,
            source_url=KOUKOU_SOURCE_URL,
            source_date=PREF_SOURCE_DATE,
            course=course,
        )
        records.append(record)

    # table2: 特別支援学校（国立ブロック→ヘッダー再掲→県立ブロック→
    # 「市立学校名」ヘッダー→市立ブロックの順。市立分は仙台市の公式ページと
    # 重複するためスキップする）
    sn_table = tables[2]
    rows = sn_table.find_all("tr")
    establishment = "国立"
    skip_group = False
    for row in rows:
        cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
        if not cells:
            continue
        if cells[0] == "国立学校名":
            establishment = "国立"
            skip_group = False
            continue
        if cells[0] == "県立学校名":
            establishment = "公立"
            skip_group = False
            continue
        if cells[0] == "市立学校名":
            skip_group = True
            continue
        if skip_group:
            continue
        if len(cells) < 4:
            continue
        name_cell, phone_cell, postal_cell, address_cell = cells[:4]
        name_cell = strip_annotations(name_cell)
        if not name_cell:
            continue
        operator = "国立大学法人宮城教育大学" if establishment == "国立" else "宮城県"
        record = make_record(
            name=name_cell,
            postal_code=postal_cell,
            address=address_cell,
            school_type="特別支援学校",
            establishment=establishment,
            operator=operator,
            phone=normalize_phone(phone_cell),
            website="",
            source_name=KOUKOU_SOURCE_NAME_SN,
            source_url=KOUKOU_SOURCE_URL,
            source_date=PREF_SOURCE_DATE,
        )
        records.append(record)
    return records


# ---------------------------------------------------------------------------
# 仙台市立小・中学校（区ごとのページ、電話番号は市外局番なし=022を補完）
# ---------------------------------------------------------------------------

SENDAI_SOURCE_DATE = "2026-07-13"
SENDAI_WARD_PAGES = [
    dict(file="sendai_aobaku-02.html", ward="仙台市青葉区"),
    dict(file="sendai_miyagino-02.html", ward="仙台市宮城野区"),
    dict(file="sendai_wakabayashi-03.html", ward="仙台市若林区"),
    dict(file="sendai_taihaku-04.html", ward="仙台市太白区"),
    dict(file="sendai_izumi-03.html", ward="仙台市泉区"),
]


# 病院内学級の分校名は原本で「同東北大学病院分校」（「同」＝直前行の略）と表記され
# 親校名を機械的に復元できないため、東北大学病院公式サイトで確認した正式名称に
# 個別対応する（青葉区ページのみに出現する2件の例外）。
SENDAI_BRANCH_NAME_OVERRIDES = {
    ("小学校", "同東北大学病院分校"): "木町通小学校東北大学病院分校",
    ("中学校", "同東北大学病院分校"): "第二中学校東北大学病院分校",
}


def read_sendai_ward_page(path: Path, *, ward: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    records: list[dict[str, Any]] = []
    source_url = f"https://www.city.sendai.jp/shogakuchose/kurashi/manabu/kyoiku/inkai/kanren/shiritsu/{path.stem.replace('sendai_', '')}.html"

    tables = soup.find_all("table")
    # 区ページは常に [0]=小学校, [1]=中学校 の2テーブル構成（校名の接尾辞では
    # 判定できない「同東北大学病院分校」のような分校名があるため、テーブル位置で判定する）。
    for table_index, table in enumerate(tables[:2]):
        school_type = "小学校" if table_index == 0 else "中学校"
        for row in table.find_all("tr")[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) < 3:
                continue
            name_cell, phone_cell, address_cell = cells[:3]
            if not name_cell:
                continue
            override = SENDAI_BRANCH_NAME_OVERRIDES.get((school_type, name_cell))
            if override:
                name_cell = override
            if not name_cell.startswith("仙台市立"):
                name_cell = "仙台市立" + name_cell
            postal, address_rest = split_postal_and_address(address_cell)
            record = make_record(
                name=name_cell,
                postal_code=postal,
                address=normalize_address(address_rest, prefix=ward),
                school_type=school_type,
                establishment="公立",
                operator="仙台市",
                phone=normalize_phone(phone_cell, default_area_code="022"),
                website="",
                source_name=f"仙台市立小・中学校所在地一覧（{ward}）",
                source_url=source_url,
                source_date=SENDAI_SOURCE_DATE,
            )
            records.append(record)
    return records


# ---------------------------------------------------------------------------
# 仙台市立 高等学校・中等教育学校・幼稚園・特別支援学校（固定順4テーブル）
# ---------------------------------------------------------------------------

SENDAI_HCTY_SOURCE_URL = "https://www.city.sendai.jp/shogakuchose/kurashi/manabu/kyoiku/inkai/kanren/shiritsu/koukou_chuto_turutoku_youtien.html"
SENDAI_HCTY_CATEGORIES = [
    ("高等学校", "仙台市立高等学校一覧"),
    ("中等教育学校", "仙台市立中等教育学校一覧"),
    ("幼稚園", "仙台市立幼稚園一覧"),
    ("特別支援学校", "仙台市立特別支援学校一覧"),
]


def read_sendai_koukou_chuto_youchien_tokushi(path: Path) -> list[dict[str, Any]]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    tables = soup.find_all("table")
    records: list[dict[str, Any]] = []

    for table, (school_type, source_name) in zip(tables, SENDAI_HCTY_CATEGORIES):
        for row in table.find_all("tr")[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) < 3:
                continue
            name_cell, phone_cell, address_cell = cells[:3]
            name_cell = strip_annotations(name_cell)
            if not name_cell:
                continue
            course = []
            m = re.search(r"[（(](全日制|定時制|通信制)[）)]", name_cell)
            if m:
                course = [m.group(1)]
                name_cell = name_cell[: m.start()].strip()
            if not name_cell.startswith("仙台市立"):
                name_cell = "仙台市立" + name_cell
            postal, address_rest = split_postal_and_address(address_cell)
            record = make_record(
                name=name_cell,
                postal_code=postal,
                address=normalize_address(address_rest, prefix="仙台市"),
                school_type=school_type,
                establishment="公立",
                operator="仙台市",
                phone=normalize_phone(phone_cell),
                website="",
                source_name=source_name,
                source_url=SENDAI_HCTY_SOURCE_URL,
                source_date=SENDAI_SOURCE_DATE,
                course=course,
            )
            records.append(record)
    return records


# ---------------------------------------------------------------------------
# 私立学校名簿PDF（1ファイル、校種ごとにページが分かれる）
# ---------------------------------------------------------------------------

PRIVATE_SOURCE_DATE = "2025-05-01"
PRIVATE_SOURCE_URL = "https://www.pref.miyagi.jp/documents/6697/r7_meibo.pdf"
PRIVATE_SOURCE_NAME = "宮城県私立学校名簿（令和7年5月1日現在）"

CATEGORY_MARKER_HS = {"全日制", "通信制", "特別支援学校"}


def read_private_koukou_tokubetsu(path: Path, page_index: int) -> list[dict[str, Any]]:
    """高等学校・特別支援学校ページ（学科・定員が複数行にまたがる13列表）。"""
    records: list[dict[str, Any]] = []
    with pdfplumber.open(path) as pdf:
        table = pdf.pages[page_index].extract_tables()[0]

    category = "全日制"
    current: dict[str, Any] | None = None
    for row in table[1:]:
        col0 = normalize_text(row[0]) if row[0] else ""
        col1 = row[1] if len(row) > 1 else None
        rest_none = all(c is None for c in row[2:]) if len(row) > 2 else True

        # カテゴリ見出し行はcol0にカテゴリ名そのものが入り、col1以降は全てNone
        # （「学校名」列は空で、「番号」列にあたる先頭セルに見出しが入る特殊な形）。
        if col0 in CATEGORY_MARKER_HS and col1 is None and rest_none:
            category = col0
            current = None
            continue

        if col0:
            if current:
                records.append(current)
            name = normalize_name(row[1])
            operator = normalize_name(row[2]) if row[2] else ""
            postal = normalize_text(row[8]) if len(row) > 8 else ""
            address = normalize_text(row[9]) if len(row) > 9 else ""
            phone = normalize_text(row[10]) if len(row) > 10 else ""
            school_type = "特別支援学校" if category == "特別支援学校" else "高等学校"
            course = []
            gakka = normalize_text(row[5]) if len(row) > 5 else ""
            if gakka:
                course.append(gakka)
            if is_suspended_notice(phone):
                WARNINGS.add("suspended", f"休校中のため除外: {name}（{path.name} p{page_index+1}）")
                current = None
                continue
            current = make_record(
                name=name,
                postal_code=postal,
                address=address,
                school_type=school_type,
                establishment="私立",
                operator=operator,
                phone=normalize_phone(phone),
                website="",
                source_name=f"{PRIVATE_SOURCE_NAME} 高等学校・特別支援学校",
                source_url=PRIVATE_SOURCE_URL,
                source_date=PRIVATE_SOURCE_DATE,
                course=course,
            )
        else:
            if current is not None:
                gakka = normalize_text(row[5]) if len(row) > 5 else ""
                if gakka and gakka not in current["course"]:
                    current["course"].append(gakka)
    if current:
        records.append(current)
    return records


def read_private_chu_shou(path: Path, page_index: int) -> list[dict[str, Any]]:
    """中学校・小学校ページ（12列表、1行1校で完結）。"""
    records: list[dict[str, Any]] = []
    with pdfplumber.open(path) as pdf:
        table = pdf.pages[page_index].extract_tables()[0]

    category = "中学校"
    for row in table[1:]:
        col0 = normalize_text(row[0]) if row[0] else ""
        col1 = row[1] if len(row) > 1 else None
        rest_none = all(c is None for c in row[2:]) if len(row) > 2 else True

        if col0 in ("中学校", "小学校") and col1 is None and rest_none:
            category = col0
            continue
        if not col0:
            continue

        name = normalize_name(row[1])
        operator = normalize_name(row[2]) if row[2] else ""
        postal = normalize_text(row[7]) if len(row) > 7 else ""
        address = normalize_text(row[8]) if len(row) > 8 else ""
        phone = normalize_text(row[9]) if len(row) > 9 else ""
        if is_suspended_notice(phone):
            WARNINGS.add("suspended", f"休校中のため除外: {name}（{path.name} p{page_index+1}）")
            continue
        record = make_record(
            name=name,
            postal_code=postal,
            address=address,
            school_type=category,
            establishment="私立",
            operator=operator,
            phone=normalize_phone(phone),
            website="",
            source_name=f"{PRIVATE_SOURCE_NAME} 中学校・小学校",
            source_url=PRIVATE_SOURCE_URL,
            source_date=PRIVATE_SOURCE_DATE,
        )
        records.append(record)
    return records


def read_private_youchien(path: Path, page_indices: list[int]) -> list[dict[str, Any]]:
    """幼稚園ページ（市町村forward-fill + 休園見出し以降を除外）。"""
    records: list[dict[str, Any]] = []
    with pdfplumber.open(path) as pdf:
        for page_index in page_indices:
            table = pdf.pages[page_index].extract_tables()[0]
            in_suspended = False
            for row in table[1:]:
                col0 = normalize_text(row[0]) if row[0] else ""
                rest_none = all(c is None for c in row[1:]) if len(row) > 1 else True

                if col0 and rest_none:
                    in_suspended = col0 == "休園"
                    continue
                if not col0 or not col0.isdigit():
                    continue
                if in_suspended:
                    continue

                name = normalize_name(row[2]) if len(row) > 2 else ""
                if not name:
                    continue
                operator = normalize_name(row[4]) if len(row) > 4 else ""
                postal = normalize_text(row[8]) if len(row) > 8 else ""
                address = normalize_text(row[9]) if len(row) > 9 else ""
                phone = normalize_text(row[10]) if len(row) > 10 else ""
                if is_suspended_notice(phone):
                    WARNINGS.add("suspended", f"休園中のため除外: {name}（{path.name} p{page_index+1}）")
                    continue
                record = make_record(
                    name=name,
                    postal_code=postal,
                    address=address,
                    school_type="幼稚園",
                    establishment="私立",
                    operator=operator,
                    phone=normalize_phone(phone),
                    website="",
                    source_name=f"{PRIVATE_SOURCE_NAME} 幼稚園",
                    source_url=PRIVATE_SOURCE_URL,
                    source_date=PRIVATE_SOURCE_DATE,
                )
                records.append(record)
    return records


# ---------------------------------------------------------------------------
# メイン変換処理
# ---------------------------------------------------------------------------

def merge_same_school_courses(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """私立高等学校名簿で、同一校が「全日制」「通信制」等の課程ごとに別行
    （同一名称・住所・電話番号）で掲載されている場合、1レコードに統合し
    courseへ両方の値を保持する。"""
    merged: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    ordered_keys: list[tuple[str, str, str, str, str]] = []
    for record in records:
        key = (record["name"], record["address"], record["phone"], record["school_type"], record["establishment"])
        if key not in merged:
            merged[key] = record
            ordered_keys.append(key)
            continue
        existing = merged[key]
        for c in record["course"]:
            if c not in existing["course"]:
                existing["course"].append(c)
    return [merged[k] for k in ordered_keys]


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
    parser.add_argument("--source-root", type=Path, default=Path("data-source/miyagi/2025"))
    parser.add_argument("--output", type=Path, default=Path("data/school-database/miyagi.json"))
    parser.add_argument("--warnings-output", type=Path,
                         default=Path("tools/school-database/miyagi_conversion_warnings.json"))
    args = parser.parse_args()

    all_records: list[dict[str, Any]] = []

    for spec in PREF_SIMPLE_PAGES:
        path = args.source_root / spec["file"]
        if not path.exists():
            WARNINGS.add("pref", f"SKIP missing: {path}")
            continue
        records = read_pref_simple_table_page(
            path, school_type=spec["school_type"], source_name=spec["source_name"], source_url=spec["source_url"],
        )
        print(f"{spec['file']}: {len(records)} records")
        all_records.extend(records)

    koukou_path = args.source_root / "koukou.html"
    if koukou_path.exists():
        records = read_pref_koukou_page(koukou_path)
        print(f"{koukou_path.name}: {len(records)} records")
        all_records.extend(records)
    else:
        WARNINGS.add("pref", f"SKIP missing: {koukou_path}")

    for spec in SENDAI_WARD_PAGES:
        path = args.source_root / spec["file"]
        if not path.exists():
            WARNINGS.add("sendai", f"SKIP missing: {path}")
            continue
        records = read_sendai_ward_page(path, ward=spec["ward"])
        print(f"{spec['file']}: {len(records)} records")
        all_records.extend(records)

    sendai_hcty_path = args.source_root / "sendai_koukou_chuto_youchien_tokushi.html"
    if sendai_hcty_path.exists():
        records = read_sendai_koukou_chuto_youchien_tokushi(sendai_hcty_path)
        print(f"{sendai_hcty_path.name}: {len(records)} records")
        all_records.extend(records)
    else:
        WARNINGS.add("sendai", f"SKIP missing: {sendai_hcty_path}")

    private_path = args.source_root / "r7_shiritsu_meibo.pdf"
    if private_path.exists():
        records = read_private_koukou_tokubetsu(private_path, 5)
        print(f"{private_path.name} p6 (koukou/tokubetsu): {len(records)} records")
        all_records.extend(records)

        records = read_private_chu_shou(private_path, 6)
        print(f"{private_path.name} p7 (chu/shou): {len(records)} records")
        all_records.extend(records)

        records = read_private_youchien(private_path, [7, 8, 9, 10])
        print(f"{private_path.name} p8-11 (youchien): {len(records)} records")
        all_records.extend(records)
    else:
        WARNINGS.add("private", f"SKIP missing: {private_path}")

    before_merge = len(all_records)
    all_records = merge_same_school_courses(all_records)
    if len(all_records) != before_merge:
        print(f"Merged {before_merge - len(all_records)} same-school multi-course duplicate rows")
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
    for item in WARNINGS.items[:80]:
        print(f"WARN [{item['context']}] {item['message']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
