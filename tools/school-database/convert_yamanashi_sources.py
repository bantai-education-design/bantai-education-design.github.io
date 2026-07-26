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

# ---------------------------------------------------------------------------
# 正式名称変換テーブル
# ---------------------------------------------------------------------------
# 山梨県の学校住所録PDFは校名列が略称で記載されているため（例:「伊勢」「梨大附属」
# 「いづみ」等）、PDF抽出後に正式名称へ変換する。
# キー: (PDF抽出名, school_type, establishment)
# 値: 宛名として使用可能な正式名称
# 根拠:山梨大学公式サイト/山梨県教育委員会/各園公式サイト/山梨県私学教育振興会
OFFICIAL_NAME_MAP: dict[tuple[str, str, str], str] = {
    # 国立（山梨大学附属）
    ("梨大附属", "幼稚園", "国立"): "山梨大学教育学部附属幼稚園",
    ("山梨大学附属", "小学校", "国立"): "山梨大学教育学部附属小学校",
    ("山梨大学附属", "中学校", "国立"): "山梨大学教育学部附属中学校",
    ("山梨大学附属特別支援", "特別支援学校", "国立"): "山梨大学教育学部附属特別支援学校",
    # 私立幼稚園・認定こども園
    ("いづみ", "幼稚園", "私立"): "いづみ幼稚園",
    ("しらゆり", "幼稚園", "私立"): "しらゆり幼稚園",
    ("みたま", "幼稚園", "私立"): "みたま幼稚園",
    ("博愛", "幼稚園", "私立"): "博愛幼稚園",
    ("城北", "幼稚園", "私立"): "城北幼稚園",
    ("塩部", "幼稚園", "私立"): "認定こども園塩部幼稚園",
    ("山梨学院", "幼稚園", "私立"): "山梨学院幼稚園",
    ("慶明", "幼稚園", "私立"): "慶明幼稚園",
    ("朝日", "幼稚園", "私立"): "認定こども園朝日幼稚園",
    ("永照寺", "幼稚園", "私立"): "認定こども園永照寺幼稚園",
    ("琢美", "幼稚園", "私立"): "琢美幼稚園",
    ("相生", "幼稚園", "私立"): "認定こども園相生幼稚園",
    ("相生南", "幼稚園", "私立"): "相生南幼稚園",
    ("聖愛", "幼稚園", "私立"): "認定こども園聖愛幼稚園",
    ("貢川", "幼稚園", "私立"): "認定こども園貢川幼稚園",
    ("貢川進徳", "幼稚園", "私立"): "認定こども園貢川進徳幼稚園",
    ("小さき花", "幼稚園", "私立"): "小さき花幼稚園",
    ("新倉", "幼稚園", "私立"): "新倉幼稚園",
    ("月江寺", "幼稚園", "私立"): "月江寺幼稚園",
    ("聖徳", "幼稚園", "私立"): "認定こども園聖徳幼稚園",
    ("ひまわり", "幼稚園", "私立"): "認定こども園ひまわり幼稚園",
    ("青藍", "幼稚園", "私立"): "認定こども園青藍幼稚園",
    ("くさかべ", "幼稚園", "私立"): "認定こども園くさかべ幼稚園",
    ("双葉", "幼稚園", "私立"): "ふたば認定こども園双葉幼稚園",
    ("大月キリストの教会", "幼稚園", "私立"): "大月キリストの教会幼稚園",
    ("韮崎愛生", "幼稚園", "私立"): "韮崎愛生幼稚園",
    ("韮崎カトリック白百合", "幼稚園", "私立"): "韮崎カトリック白百合幼稚園",
    ("小笠原", "幼稚園", "私立"): "認定こども園小笠原幼稚園",
    ("双葉甲府", "幼稚園", "私立"): "双葉甲府幼稚園",
    ("富士", "幼稚園", "私立"): "富士幼稚園",
    ("竜王", "幼稚園", "私立"): "竜王幼稚園",
    ("石和誠心", "幼稚園", "私立"): "石和誠心幼稚園",
    ("上野原", "幼稚園", "私立"): "上野原幼稚園",
    ("上野原羽佐間", "幼稚園", "私立"): "上野原羽佐間幼稚園",
    ("島田", "幼稚園", "私立"): "島田幼稚園",
    ("塩山カトリック", "幼稚園", "私立"): "塩山カトリック幼稚園",
    ("市川", "幼稚園", "私立"): "認定こども園市川幼稚園",
    ("市川南", "幼稚園", "私立"): "認定こども園市川南幼稚園",
    ("峡南", "幼稚園", "私立"): "峡南幼稚園",
    ("南部みどり", "幼稚園", "私立"): "南部みどり幼稚園",
    ("忍野", "幼稚園", "私立"): "忍野村立認定こども園忍野幼稚園",  # 公立だが PDF では私立扱い
    # 私立小学校・中学校・高等学校（校種省略の補完）
    ("山梨学院", "小学校", "私立"): "山梨学院小学校",
    ("駿台甲府", "小学校", "私立"): "駿台甲府小学校",
    ("南アルプス子どもの村", "小学校", "私立"): "南アルプス子どもの村小学校",
    ("山梨学院", "中学校", "私立"): "山梨学院中学校",
    ("山梨英和", "中学校", "私立"): "山梨英和中学校",
    ("駿台甲府", "中学校", "私立"): "駿台甲府中学校",
    ("富士学苑", "中学校", "私立"): "富士学苑中学校",
    ("南アルプス子どもの村", "中学校", "私立"): "南アルプス子どもの村中学校",
    ("日本航空高校付属", "中学校", "私立"): "日本航空高等学校附属中学校",
    ("山梨学院", "高等学校", "私立"): "山梨学院高等学校",
    ("山梨英和", "高等学校", "私立"): "山梨英和高等学校",
    ("東海大学付属甲府", "高等学校", "私立"): "東海大学付属甲府高等学校",
    ("甲斐清和", "高等学校", "私立"): "甲斐清和高等学校",
    ("駿台甲府", "高等学校", "私立"): "駿台甲府高等学校",
    ("富士学苑", "高等学校", "私立"): "富士学苑高等学校",
    ("自然学園", "高等学校", "私立"): "自然学園高等学校",
    ("帝京第三", "高等学校", "私立"): "帝京第三高等学校",
    ("日本航空", "高等学校", "私立"): "日本航空高等学校",
    ("日本大学明誠", "高等学校", "私立"): "日本大学明誠高等学校",
    ("身延山", "高等学校", "私立"): "身延山高等学校",
    # 公立高等学校（山梨県立が原則。市立は甲府商業と北杜市立甲陵の2枚のみ）
    # 場所：公式サイト kchs.city.kofu.yamanashi.jp, city.hokuto.yamanashi.jp
    ("中央", "高等学校", "公立"): "山梨県立中央高等学校",
    ("甲府南", "高等学校", "公立"): "山梨県立甲府南高等学校",
    ("甲府商業", "高等学校", "公立"): "甲府市立甲府商業高等学校",  # 甲府市立（山梨県立ではない）
    ("甲府城西", "高等学校", "公立"): "山梨県立甲府城西高等学校",
    ("甲府工業", "高等学校", "公立"): "山梨県立甲府工業高等学校",
    ("甲府東", "高等学校", "公立"): "山梨県立甲府東高等学校",
    ("甲府第一", "高等学校", "公立"): "山梨県立甲府第一高等学校",
    ("甲府西", "高等学校", "公立"): "山梨県立甲府西高等学校",
    ("ひばりが丘", "高等学校", "公立"): "山梨県立ひばりが丘高等学校",
    ("吉田", "高等学校", "公立"): "山梨県立吉田高等学校",
    ("富士北稜", "高等学校", "公立"): "山梨県立富士北稜高等学校",
    ("都留興譲館", "高等学校", "公立"): "山梨県立都留興譲館高等学校",
    ("山梨", "高等学校", "公立"): "山梨県立山梨高等学校",
    ("日川", "高等学校", "公立"): "山梨県立日川高等学校",
    ("都留", "高等学校", "公立"): "山梨県立都留高等学校",
    ("韮崎", "高等学校", "公立"): "山梨県立韮崎高等学校",
    ("韮崎工業", "高等学校", "公立"): "山梨県立韮崎工業高等学校",
    ("巨摩", "高等学校", "公立"): "山梨県立巨摩高等学校",
    ("白根", "高等学校", "公立"): "山梨県立白根高等学校",
    ("北杜", "高等学校", "公立"): "山梨県立北杜高等学校",
    ("甲陵", "高等学校", "公立"): "北杜市立甲陵高等学校",
    ("農林", "高等学校", "公立"): "山梨県立農林高等学校",
    ("笛吹", "高等学校", "公立"): "山梨県立笛吹高等学校",
    ("上野原", "高等学校", "公立"): "山梨県立上野原高等学校",
    ("塩山", "高等学校", "公立"): "山梨県立塩山高等学校",
    ("甲府昭和", "高等学校", "公立"): "山梨県立甲府昭和高等学校",
    ("青洲", "高等学校", "公立"): "山梨県立青洲高等学校",
    ("身延", "高等学校", "公立"): "山梨県立身延高等学校",
    ("富士河口湖", "高等学校", "公立"): "山梨県立富士河口湖高等学校",
    # 公立特別支援学校（山梨県立）
    ("かえで支援", "特別支援学校", "公立"): "山梨県立かえで支援学校",
    ("富士見支援", "特別支援学校", "公立"): "山梨県立富士見支援学校",
    ("うぐいすの杜学園", "特別支援学校", "公立"): "山梨県立特別支援学校うぐいすの杜学園",
    ("特別支援学校うぐいすの杜学園", "特別支援学校", "公立"): "山梨県立特別支援学校うぐいすの杜学園",
    ("甲府支援", "特別支援学校", "公立"): "山梨県立甲府支援学校",
    ("盲", "特別支援学校", "公立"): "山梨県立盲学校",
    ("ろう", "特別支援学校", "公立"): "山梨県立ろう学校",
    ("やまびこ支援", "特別支援学校", "公立"): "山梨県立やまびこ支援学校",
    ("あけぼの支援", "特別支援学校", "公立"): "山梨県立あけぼの支援学校",
    ("わかば支援", "特別支援学校", "公立"): "山梨県立わかば支援学校",
    ("桃花台学園", "特別支援学校", "公立"): "山梨県立高等支援学校桃花台学園",
    ("高等支援学校桃花台学園", "特別支援学校", "公立"): "山梨県立高等支援学校桃花台学園",
    ("ふじざくら支援", "特別支援学校", "公立"): "山梨県立ふじざくら支援学校",
}

_OFFICIAL_NAME_MUNI_PREFIX: dict[str, str] = {
    "甲府市": "甲府市立", "富士吉田市": "富士吉田市立", "都留市": "都留市立",
    "山梨市": "山梨市立", "大月市": "大月市立", "韮崎市": "韮崎市立",
    "南アルプス市": "南アルプス市立", "北杜市": "北杜市立", "甲斐市": "甲斐市立",
    "笛吹市": "笛吹市立", "上野原市": "上野原市立", "甲州市": "甲州市立",
    "中央市": "中央市立", "中巨摩郡昭和町": "昭和町立",
    "西八代郡市川三郷町": "市川三郷町立", "南巨摩郡早川町": "早川町立",
    "南巨摩郡身延町": "身延町立", "南巨摩郡南部町": "南部町立",
    "南巨摩郡富士川町": "富士川町立", "南都留郡道志村": "道志村立",
    "南都留郡西桂町": "西桂町立", "南都留郡忍野村": "忍野村立",
    "南都留郡山中湖村": "山中湖村立", "南都留郡鳴沢村": "鳴沢村立",
    "南都留郡富士河口湖町": "富士河口湖町立",
    "北都留郡小菅村": "小菅村立", "北都留郡丹波山村": "丹波山村立",
}


def apply_official_name(
    name: str, school_type: str, establishment: str, municipality: str
) -> tuple[str, str]:
    """PDF抽出した略称を正式名称へ変換し (name, establishment) を返す。"""
    key = (name, school_type, establishment)
    if key in OFFICIAL_NAME_MAP:
        official = OFFICIAL_NAME_MAP[key]
        # 忍野幼稚園は公立（設置区分補正）
        new_estab = "公立" if name == "忍野" and school_type == "幼稚園" else establishment
        return official, new_estab
    # 公立小学校・中学校: 自治体名＋校種を付加
    if establishment == "公立" and school_type in ("小学校", "中学校"):
        prefix = _OFFICIAL_NAME_MUNI_PREFIX.get(municipality, "")
        if prefix:
            return f"{prefix}{name}{school_type}", establishment
    return name, establishment


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
    # 略称を正式名称に変換（設置区分も必要に応じて補正）
    name, establishment = apply_official_name(name, school_type, establishment, municipality)
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
