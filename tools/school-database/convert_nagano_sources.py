#!/usr/bin/env python3
"""Build the Nagano school database from official source pages.

The script intentionally fetches only official prefectural and municipal
pages. It does not use private directories or search-result snippets.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "school-database" / "nagano.json"
WARNINGS_PATH = ROOT / "tools" / "school-database" / "nagano_conversion_warnings.json"
MANIFEST_PATH = ROOT / "docs" / "school-database" / "nagano" / "source-manifest.md"
TODAY = "2026-07-26"

SOURCES = {
    "public_kindergarten": "https://www.pref.nagano.lg.jp/kyoiku/kyoiku/link/yochien.html",
    "public_elementary_index": "https://www.pref.nagano.lg.jp/kyoiku/kyoiku/link/sho/index.html",
    "public_middle": "https://www.pref.nagano.lg.jp/kyoiku/kyoiku/link/chu.html",
    "public_high": "https://www.pref.nagano.lg.jp/kyoiku/kyoiku/link/ko.html",
    "public_special": "https://www.pref.nagano.lg.jp/kyoiku/tokubetsu-shien/link/tokubetsushien/index.html",
    "private_kindergarten": "https://www.pref.nagano.lg.jp/ken-manabi/kyoiku/shien/hoikujo/yochien/mebo.html",
    "private_elementary": "https://www.pref.nagano.lg.jp/ken-manabi/kyoiku/gakko/shochu/shiritsusho/mebo.html",
    "private_middle": "https://www.pref.nagano.lg.jp/ken-manabi/kyoiku/gakko/shochu/shiritsuchu/mebo.html",
    "private_obligation": "https://www.pref.nagano.lg.jp/ken-manabi/kyoiku/gakko/shochu/shiritsugimu/gimumeibo.html",
    "private_secondary": "https://www.pref.nagano.lg.jp/ken-manabi/kyoiku/gakko/shochu/shiritsuchutou/mebo.html",
    "private_high": "https://www.pref.nagano.lg.jp/ken-manabi/kyoiku/gakkoukou/koukou/koukou/mebo.html",
    "nagano_city": "https://www.city.nagano.nagano.jp/n601000/contents/p001572.html",
    "japan_post_iida_kanaekamiyama": "https://www.post.japanpost.jp/cgi-zip/zipcode.php?zip=3950806",
}

SOURCE_NAMES = {
    "public_kindergarten": "長野県教育委員会 幼稚園リンク",
    "public_elementary_index": "長野県教育委員会 小学校リンク",
    "public_middle": "長野県教育委員会 中学校リンク",
    "public_high": "長野県教育委員会 高等学校リンク",
    "public_special": "長野県教育委員会 特別支援学校リンク",
    "private_kindergarten": "長野県 私立幼稚園名簿（令和8年4月1日現在）",
    "private_elementary": "長野県 私立小学校名簿（令和8年4月1日現在）",
    "private_middle": "長野県 私立中学校名簿（令和8年4月1日現在）",
    "private_obligation": "長野県 私立義務教育学校名簿（令和8年4月1日現在）",
    "private_secondary": "長野県 私立中等教育学校名簿（令和8年4月1日現在）",
    "private_high": "長野県 私立高等学校名簿（令和8年4月1日現在）",
    "nagano_city": "長野市立小・中・高等学校一覧（2026年4月1日更新）",
    "japan_post_iida_kanaekamiyama": "日本郵便 郵便番号検索 長野県飯田市鼎上山",
}

SCHOOL_TYPE_ORDER = ["幼稚園", "小学校", "中学校", "義務教育学校", "高等学校", "中等教育学校", "特別支援学校"]
ESTABLISHMENT_ORDER = ["国立", "公立", "私立"]

TOWN_TO_DISTRICT = {
    "軽井沢町": "北佐久郡軽井沢町",
    "御代田町": "北佐久郡御代田町",
    "立科町": "北佐久郡立科町",
    "下諏訪町": "諏訪郡下諏訪町",
    "富士見町": "諏訪郡富士見町",
    "原村": "諏訪郡原村",
    "筑北村": "東筑摩郡筑北村",
    "麻績村": "東筑摩郡麻績村",
    "生坂村": "東筑摩郡生坂村",
    "山形村": "東筑摩郡山形村",
    "朝日村": "東筑摩郡朝日村",
}

JAPAN_POST_POSTAL_SUPPLEMENTS = {
    "長野県飯田市鼎上山1815": {
        "postal_code": "395-0806",
        "source_key": "japan_post_iida_kanaekamiyama",
        "reason": "長野県私立幼稚園名簿の郵便番号欄が空欄のため、日本郵便公式検索の長野県飯田市鼎上山（395-0806）で補完",
    }
}

DISTRICT_ELEMENTARY_ORDER = [
    "toshin-saku.html",
    "toshin-ueda.html",
    "nanshin-ina.html",
    "nanshin-ida.html",
    "chushin.html",
    "hokushin.html",
]


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


def clean_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[（(]別ウィンドウで外部サイトが開きます[）)]", "", text)
    text = re.sub(r"[（(]外部サイトへリンク[）)]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_name(value: str) -> str:
    text = clean_text(value)
    text = re.sub(r"\s+", "", text)
    return text


def normalize_phone(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = re.sub(r"\s+", "", text)
    text = text.replace("ー", "-").replace("−", "-").replace("―", "-")
    return text.strip()


def normalize_postal(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    match = re.search(r"(\d{3})-?(\d{4})", text)
    return f"{match.group(1)}-{match.group(2)}" if match else ""


def normalize_address(value: str, municipality_hint: str = "") -> str:
    address = clean_text(value)
    address = re.sub(r"^〒?\s*\d{3}-?\d{4}\s*", "", address)
    address = address.replace("長野県", "")
    address = re.sub(r"\s+", "", address)
    if municipality_hint and not address.startswith(municipality_hint):
        address = f"{municipality_hint}{address}"
    return f"長野県{address}" if address else ""


def normalize_municipality(value: str) -> str:
    return re.sub(r"\s+", "", clean_text(value))


def municipality_from_address(address: str) -> str:
    text = address.replace("長野県", "")
    match = re.match(r"([^郡市]+市)", text)
    if match:
        return normalize_municipality(match.group(1))
    match = re.match(r"([^郡]+郡[^町村]+[町村])", text)
    if match:
        return normalize_municipality(match.group(1))
    for town, full_name in TOWN_TO_DISTRICT.items():
        if text.startswith(town):
            return normalize_municipality(full_name)
    return ""


def establishment_from_label(label: str) -> str:
    label = clean_text(label)
    if "国" in label:
        return "国立"
    if "私" in label:
        return "私立"
    return "公立"


def fetch_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    return BeautifulSoup(response.text, "html.parser")


def table_rows(table) -> list[list[dict[str, object]]]:
    rows: list[list[dict[str, object]]] = []
    for tr in table.find_all("tr"):
        cells = []
        for cell in tr.find_all(["th", "td"]):
            links = [a.get("href", "") for a in cell.find_all("a") if a.get("href")]
            cells.append({"text": clean_text(cell.get_text(" ", strip=True)), "links": links})
        if cells:
            rows.append(cells)
    return rows


def first_http_link(cell: dict[str, object], base_url: str) -> str:
    for href in cell.get("links", []):
        absolute = urljoin(base_url, str(href))
        if absolute.startswith("http"):
            return absolute
    return ""


def extract_public_kindergarten(records: list[ExtractedRecord], exclusions: list[dict[str, str]]) -> None:
    url = SOURCES["public_kindergarten"]
    soup = fetch_soup(url)
    for row in table_rows(soup.find("table"))[1:]:
        if len(row) < 3:
            continue
        body = row[1]["text"]
        postal = normalize_postal(body)
        match = re.match(r"(.+?)[(（]〒\d{3}-?\d{4}[)）](.+)$", body)
        if not match:
            exclusions.append({"name": clean_name(body), "reason": "園名・所在地の複合セルを分解できなかったため除外", "source_url": url})
            continue
        name = clean_name(match.group(1))
        address = normalize_address(match.group(2))
        records.append(
            ExtractedRecord(name, "幼稚園", establishment_from_label(row[0]["text"]), postal, address,
                            municipality_from_address(address), "", normalize_phone(row[2]["text"]),
                            first_http_link(row[1], url), "public_kindergarten", url, TODAY, [])
        )


def extract_public_elementary(records: list[ExtractedRecord], exclusions: list[dict[str, str]], municipality_order: list[str]) -> None:
    index_url = SOURCES["public_elementary_index"]
    soup = fetch_soup(index_url)
    pages = [index_url]
    for href in DISTRICT_ELEMENTARY_ORDER:
        pages.append(urljoin(index_url, href))
    for url in pages:
        source_key = "public_elementary_index"
        soup = fetch_soup(url)
        for table in soup.find_all("table"):
            rows = table_rows(table)
            for row in rows[1:]:
                if len(row) < 5:
                    continue
                all_text = " ".join(str(c["text"]) for c in row)
                if "閉校" in all_text or not normalize_postal(row[2]["text"]):
                    exclusions_reason = "長野県教育委員会小学校リンク上で閉校注記のみが示され、現行校としての住所・電話番号がないため除外"
                    records_name = clean_name(row[1]["text"])
                    exclusions.append({"name": records_name, "reason": exclusions_reason, "source_url": url})
                    continue
                establishment = establishment_from_label(row[0]["text"])
                name = clean_name(row[1]["text"])
                postal = normalize_postal(row[2]["text"])
                address = normalize_address(row[3]["text"])
                municipality = municipality_from_address(address)
                if municipality and municipality not in municipality_order:
                    municipality_order.append(municipality)
                records.append(
                    ExtractedRecord(name, "小学校", establishment, postal, address, municipality, "",
                                    normalize_phone(row[4]["text"]), first_http_link(row[1], url),
                                    source_key, url, TODAY, [])
                )


def extract_public_middle(records: list[ExtractedRecord], exclusions: list[dict[str, str]], municipality_order: list[str]) -> None:
    url = SOURCES["public_middle"]
    soup = fetch_soup(url)
    for table in soup.find_all("table"):
        for row in table_rows(table)[1:]:
            if len(row) < 5:
                continue
            all_text = " ".join(str(c["text"]) for c in row)
            if "閉校" in all_text or not normalize_postal(row[2]["text"]):
                exclusions.append({"name": clean_name(row[1]["text"]), "reason": "長野県教育委員会中学校リンク上で閉校注記のみが示され、現行校としての住所・電話番号がないため除外", "source_url": url})
                continue
            name = clean_name(row[1]["text"])
            postal = normalize_postal(row[2]["text"])
            address = normalize_address(row[3]["text"])
            municipality = municipality_from_address(address)
            if municipality and municipality not in municipality_order:
                municipality_order.append(municipality)
            records.append(
                ExtractedRecord(name, "中学校", establishment_from_label(row[0]["text"]), postal, address,
                                municipality, "", normalize_phone(row[4]["text"]), first_http_link(row[1], url),
                                "public_middle", url, TODAY, [])
            )


def split_course(text: str) -> list[str]:
    value = clean_text(text)
    value = value.replace("全日制:", "全日制・").replace("定時制:", "定時制・")
    parts = re.split(r"[・、/]+", value)
    return [p.strip() for p in parts if p.strip() and "閉校" not in p]


def extract_public_high(records: list[ExtractedRecord], exclusions: list[dict[str, str]], municipality_order: list[str]) -> None:
    url = SOURCES["public_high"]
    soup = fetch_soup(url)
    for table in soup.find_all("table"):
        rows = table_rows(table)
        if not rows or len(rows[0]) < 5 or "学校名" not in rows[0][1]["text"]:
            continue
        for row in rows[1:]:
            if len(row) < 5:
                continue
            name = clean_name(row[1]["text"])
            all_text = " ".join(str(c["text"]) for c in row)
            postal = normalize_postal(row[3]["text"])
            if not postal or "閉校" in all_text:
                exclusions.append({"name": name, "reason": "長野県高等学校リンク上で閉校・統合先のみが示され、現行校としての住所・電話番号がないため除外", "source_url": url})
                continue
            address_text = clean_text(row[3]["text"])
            phone_text = clean_text(row[4]["text"])
            if "長野吉田高戸隠分校" in name and "(戸隠)" in phone_text:
                special_rows = [
                    ("長野吉田高等学校", "381-8570", "長野市吉田2-12-9", "026-241-6161"),
                    ("長野吉田高等学校戸隠分校", "381-4101", "長野市戸隠1491", "026-254-2158"),
                ]
                for special_name, special_postal, special_address, special_phone in special_rows:
                    address = normalize_address(special_address)
                    municipality = municipality_from_address(address)
                    if municipality and municipality not in municipality_order:
                        municipality_order.append(municipality)
                    records.append(
                        ExtractedRecord(special_name, "高等学校", "公立", special_postal, address, municipality, "",
                                        special_phone, first_http_link(row[1], url), "public_high", url, TODAY, split_course(row[2]["text"]))
                    )
                continue
            if "佐久平総合技術高等学校" in name and "(浅間)" in address_text and "(臼田)" in address_text:
                special_rows = [
                    ("佐久平総合技術高等学校浅間キャンパス", "385-0022", "佐久市岩村田991", "0267-67-4010"),
                    ("佐久平総合技術高等学校臼田キャンパス", "384-0301", "佐久市臼田751", "0267-82-2035"),
                ]
                for special_name, special_postal, special_address, special_phone in special_rows:
                    address = normalize_address(special_address)
                    municipality = municipality_from_address(address)
                    if municipality and municipality not in municipality_order:
                        municipality_order.append(municipality)
                    records.append(
                        ExtractedRecord(special_name, "高等学校", "公立", special_postal, address, municipality, "",
                                        special_phone, first_http_link(row[1], url), "public_high", url, TODAY, split_course(row[2]["text"]))
                    )
                continue
            address = normalize_address(row[3]["text"])
            municipality = municipality_from_address(address)
            if municipality and municipality not in municipality_order:
                municipality_order.append(municipality)
            records.append(
                ExtractedRecord(name, "高等学校", "公立", postal, address, municipality, "",
                                normalize_phone(row[4]["text"]), first_http_link(row[1], url),
                                "public_high", url, TODAY, split_course(row[2]["text"]))
            )


def extract_public_special(records: list[ExtractedRecord], municipality_order: list[str]) -> None:
    url = SOURCES["public_special"]
    soup = fetch_soup(url)
    for row in table_rows(soup.find("table"))[1:]:
        if len(row) < 4:
            continue
        name = clean_name(row[1]["text"])
        postal = normalize_postal(row[2]["text"])
        address = normalize_address(row[2]["text"])
        municipality = municipality_from_address(address)
        if municipality and municipality not in municipality_order:
            municipality_order.append(municipality)
        records.append(
            ExtractedRecord(name, "特別支援学校", establishment_from_label(row[0]["text"]), postal, address,
                            municipality, "", normalize_phone(row[3]["text"]), first_http_link(row[1], url),
                            "public_special", url, TODAY, [])
        )


def extract_private_kindergarten(records: list[ExtractedRecord], exclusions: list[dict[str, str]], municipality_order: list[str]) -> None:
    url = SOURCES["private_kindergarten"]
    soup = fetch_soup(url)
    current_municipality = ""
    for row in table_rows(soup.find("table"))[1:]:
        values = [str(c["text"]) for c in row]
        if len(values) < 6:
            continue
        if values[0]:
            current_municipality = normalize_municipality(values[0])
        name = clean_name(values[1])
        if "休園" in name or "休校" in name:
            exclusions.append({"name": name, "reason": "公式名簿に休園中または休校中と明記され、現行の送付先データとして扱わないため除外", "source_url": url})
            continue
        if "認定こども園" in name or "こども園" in name or "こども" in name:
            exclusions.append({"name": name, "reason": "共通方針で認定こども園を初版収録対象外としているため除外", "source_url": url})
            continue
        postal = normalize_postal(values[-3])
        address = normalize_address(values[-2], current_municipality)
        municipality = normalize_municipality(current_municipality or municipality_from_address(address))
        if municipality and municipality not in municipality_order:
            municipality_order.append(municipality)
        records.append(
            ExtractedRecord(name, "幼稚園", "私立", postal, address, municipality, values[3] if len(values) > 6 else values[2],
                            normalize_phone(values[-1]), "", "private_kindergarten", url, "2026-04-01", [])
        )


def extract_private_table(records: list[ExtractedRecord], source_key: str, school_type: str, municipality_order: list[str], exclusions: list[dict[str, str]]) -> None:
    url = SOURCES[source_key]
    soup = fetch_soup(url)
    for table in soup.find_all("table"):
        for row in table_rows(table)[1:]:
            values = [str(c["text"]) for c in row]
            if len(values) < 6:
                continue
            name = clean_name(values[0])
            if "休校" in " ".join(values):
                exclusions.append({"name": name, "reason": "公式名簿に休校中と明記され、現行の送付先データとして扱わないため除外", "source_url": url})
                continue
            postal_idx = next((i for i, value in enumerate(values) if normalize_postal(value)), -1)
            if postal_idx < 0 or postal_idx + 2 >= len(values):
                exclusions.append({"name": name, "reason": "郵便番号・所在地・電話番号の列を特定できなかったため除外", "source_url": url})
                continue
            postal = normalize_postal(values[postal_idx])
            address = normalize_address(values[postal_idx + 1])
            municipality = municipality_from_address(address)
            if municipality and municipality not in municipality_order:
                municipality_order.append(municipality)
            course = split_course(values[3]) if source_key == "private_high" and len(values) > 3 else []
            if school_type == "中等教育学校":
                course = ["前期課程", "後期課程"]
            records.append(
                ExtractedRecord(name, school_type, "私立", postal, address, municipality, values[1],
                                normalize_phone(values[postal_idx + 2]), "", source_key, url, "2026-04-01", course)
            )


def supplement_nagano_city_websites(records: list[ExtractedRecord], warnings: list[dict[str, str]]) -> int:
    url = SOURCES["nagano_city"]
    soup = fetch_soup(url)
    type_by_table = {0: "小学校", 1: "中学校", 2: "高等学校"}
    supplements = 0
    for index, table in enumerate(soup.find_all("table")[:3]):
        school_type = type_by_table[index]
        for row in table_rows(table)[1:]:
            if len(row) < 4:
                continue
            short_name = clean_name(row[0]["text"])
            phone = normalize_phone(row[1]["text"])
            postal = normalize_postal(row[2]["text"])
            website = first_http_link(row[0], url)
            for record in records:
                if record.school_type != school_type or record.municipality != "長野市":
                    continue
                if record.postal_code == postal and record.phone == phone and (short_name in record.name):
                    if website and not record.website:
                        record.website = website
                        supplements += 1
                    break
            else:
                warnings.append({"type": "nagano_city_supplement_unmatched", "name": short_name, "postal_code": postal, "phone": phone, "source_url": url})
    return supplements


def deduplicate(records: list[ExtractedRecord], corrections: list[dict[str, str]]) -> list[ExtractedRecord]:
    result: dict[tuple[str, str, str, str], ExtractedRecord] = {}
    for record in records:
        key = (record.name, record.school_type, record.address, record.phone)
        if key not in result:
            result[key] = record
            continue
        existing = result[key]
        merged = sorted(set(existing.course + record.course), key=lambda x: (SCHOOL_TYPE_ORDER.index(x) if x in SCHOOL_TYPE_ORDER else 999, x))
        if merged != existing.course:
            corrections.append({"name": record.name, "field": "course", "before": " / ".join(existing.course), "after": " / ".join(merged), "reason": "同一校が複数表に掲載されていたため課程を統合"})
            existing.course = merged
        if not existing.website and record.website:
            existing.website = record.website
    return list(result.values())


def supplement_postal_codes(records: list[ExtractedRecord], corrections: list[dict[str, str]]) -> int:
    count = 0
    for record in records:
        if record.postal_code:
            continue
        supplement = JAPAN_POST_POSTAL_SUPPLEMENTS.get(record.address)
        if not supplement:
            continue
        record.postal_code = supplement["postal_code"]
        corrections.append({
            "name": record.name,
            "field": "postal_code",
            "before": "",
            "after": record.postal_code,
            "reason": supplement["reason"],
            "source_url": SOURCES[supplement["source_key"]],
        })
        count += 1
    return count


def make_id(record: ExtractedRecord, index: int) -> str:
    return f"nagano-{index:04d}"


def build_records(records: list[ExtractedRecord], municipality_order: list[str]) -> list[dict[str, object]]:
    m_order = {name: index for index, name in enumerate(municipality_order)}

    def sort_key(record: ExtractedRecord) -> tuple[int, int, int, str]:
        return (
            m_order.get(record.municipality, 999),
            SCHOOL_TYPE_ORDER.index(record.school_type) if record.school_type in SCHOOL_TYPE_ORDER else 999,
            ESTABLISHMENT_ORDER.index(record.establishment) if record.establishment in ESTABLISHMENT_ORDER else 999,
            record.name,
        )

    items = sorted(records, key=sort_key)
    output = []
    for index, record in enumerate(items, 1):
        output.append({
            "id": make_id(record, index),
            "prefecture": "長野県",
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


def write_manifest(data: list[dict[str, object]], warnings: dict[str, object], municipality_order: list[str]) -> None:
    by_type = Counter(str(item["school_type"]) for item in data)
    by_est = Counter(str(item["establishment"]) for item in data)
    by_muni = Counter(str(item["municipality"]) for item in data)
    source_lines = "\n".join(f"- {SOURCE_NAMES[key]}: {url}" for key, url in SOURCES.items())
    type_lines = "\n".join(f"- {name}: {by_type.get(name, 0)}" for name in SCHOOL_TYPE_ORDER)
    est_lines = "\n".join(f"- {name}: {by_est.get(name, 0)}" for name in ESTABLISHMENT_ORDER)
    muni_lines = "\n".join(f"- {name}: {count}" for name, count in by_muni.items())
    exclusion_lines = "\n".join(
        f"- {item['name']}: {item['reason']}（{item['source_url']}）"
        for item in warnings["exclusions"]
    ) or "- なし"
    correction_lines = "\n".join(
        f"- {item['name']} / {item['field']}: `{item['before']}` -> `{item['after']}`。{item['reason']}"
        + (f"（{item['source_url']}）" if item.get("source_url") else "")
        for item in warnings["corrections"]
    ) or "- なし"
    postal_supplement_count = warnings["postal_code_supplements_from_japan_post"]

    body = f"""# 長野県学校データベース ソースマニフェスト

## 収録範囲

- 都道府県: 長野県
- 総収録件数: {len(data)}
- 対象校種: 幼稚園、小学校、中学校、義務教育学校、高等学校、中等教育学校、特別支援学校
- 設置区分: 国立、公立、私立
- 除外対象: 認定こども園、保育所、専修学校、各種学校、大学、短大、高専、公式資料で休校中・閉校済みと明記された学校

## 使用一次資料

{source_lines}

## 基準日

- 私立小学校・中学校・義務教育学校・中等教育学校・高等学校・幼稚園: 令和8年4月1日現在の長野県公式名簿
- 長野市立小・中・高等学校一覧: 2026年4月1日更新
- 長野県教育委員会リンクページ: 2026年7月26日に公式掲載内容を確認

## 集計

### 校種別

{type_lines}

### 設置区分別

{est_lines}

### 自治体別

{muni_lines}

## 行政順

検索画面の行政順は、長野県教育委員会の小学校リンクに掲載されている地区別ページ順（東信佐久、東信上田、南信上伊那・諏訪、南信飯伊、中信、北信）と各公式表内の出現順を基準にした。小学校一覧に現れない自治体は、その他の長野県公式表に出現した順で末尾に追加した。

## 除外記録

{exclusion_lines}

## 補正記録

{correction_lines}

## 郵便番号補完

- 日本郵便データによる郵便番号補完: {postal_supplement_count}件
- 長野県または長野市の公式資料に郵便番号が掲載されたレコードは、その掲載値を使用した。
- 郵便番号が空欄だった私立幼稚園1件（ビバ・チャイルド）は、日本郵便公式検索「長野県飯田市鼎上山」の結果（395-0806）で補完した。

## 長野県特有の処理

- 国立学校は、長野県教育委員会のリンクページに掲載された信州大学附属の幼稚園・小学校・中学校・特別支援学校を収録した。
- 私立高等学校名簿の「長野女子 【休校中】」は休校中の注記に基づき除外した。
- 私立幼稚園名簿に掲載されている認定こども園は、既存全国学校データベースの共通方針に合わせて除外した。
- 同一法人・同一所在地でも、私立小学校と私立中学校は別レコードとして扱った。
- 電話番号中の余分な空白、全角記号、郵便番号表記はNFKC正規化後に整形した。

## 検証メモ

- `data-source/` はローカル作業用であり、この実装では作成・コミットしていない。
- 公式HP URLは長野県公式リンクページおよび長野市公式一覧の学校名リンクから取得できた範囲のみ登録した。
"""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(body, encoding="utf-8")


def main() -> int:
    records: list[ExtractedRecord] = []
    exclusions: list[dict[str, str]] = []
    corrections: list[dict[str, str]] = []
    additional_warnings: list[dict[str, str]] = []
    municipality_order: list[str] = []

    extract_public_kindergarten(records, exclusions)
    extract_public_elementary(records, exclusions, municipality_order)
    extract_public_middle(records, exclusions, municipality_order)
    extract_public_high(records, exclusions, municipality_order)
    extract_public_special(records, municipality_order)
    extract_private_kindergarten(records, exclusions, municipality_order)
    extract_private_table(records, "private_elementary", "小学校", municipality_order, exclusions)
    extract_private_table(records, "private_middle", "中学校", municipality_order, exclusions)
    extract_private_table(records, "private_obligation", "義務教育学校", municipality_order, exclusions)
    extract_private_table(records, "private_secondary", "中等教育学校", municipality_order, exclusions)
    extract_private_table(records, "private_high", "高等学校", municipality_order, exclusions)

    website_supplements = supplement_nagano_city_websites(records, additional_warnings)
    postal_supplements = supplement_postal_codes(records, corrections)
    deduped = deduplicate(records, corrections)
    data = build_records(deduped, municipality_order)

    warnings: dict[str, object] = {
        "generated_at": TODAY,
        "total_records": len(data),
        "website_supplements_from_nagano_city": website_supplements,
        "postal_code_supplements_from_japan_post": postal_supplements,
        "exclusions": exclusions,
        "corrections": corrections,
        "warnings": additional_warnings,
        "municipality_order": municipality_order,
        "counts": {
            "by_type": dict(Counter(str(item["school_type"]) for item in data)),
            "by_establishment": dict(Counter(str(item["establishment"]) for item in data)),
            "by_municipality": dict(Counter(str(item["municipality"]) for item in data)),
        },
    }

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    WARNINGS_PATH.write_text(json.dumps(warnings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_manifest(data, warnings, municipality_order)

    print(f"wrote {DATA_PATH} ({len(data)} records)")
    print("校種別:", json.dumps(warnings["counts"]["by_type"], ensure_ascii=False, sort_keys=True))
    print("設置区分別:", json.dumps(warnings["counts"]["by_establishment"], ensure_ascii=False, sort_keys=True))
    print(f"除外: {len(exclusions)} / 補正: {len(corrections)} / 郵便番号補完: {postal_supplements} / 長野市HP補完: {website_supplements}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
