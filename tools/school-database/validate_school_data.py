#!/usr/bin/env python3
"""Ban.Tai 学校データベースJSONの基本検証。

使用例:
    python tools/school-database/validate_school_data.py data/school-database/saitama.json --prefecture 埼玉県
    python tools/school-database/validate_school_data.py data/school-database/chiba.json --prefecture 千葉県

埼玉県版・東京都版は school_name/establishment_type、千葉県版は name/establishment
というフィールド名を使うため、FIELD_ALIASES で両対応する（既存データの読み込みは変更しない）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# 論理フィールド名 -> 実際のJSONキー候補（先に見つかったものを使用）
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "name": ("school_name", "name"),
    "school_type": ("school_type",),
    "establishment": ("establishment_type", "establishment"),
    "municipality": ("municipality",),
    "postal_code": ("postal_code",),
    "address": ("address",),
    "phone": ("phone",),
    "course": ("course",),
}

REQUIRED_LOGICAL_FIELDS = (
    "name",
    "school_type",
    "establishment",
    "municipality",
    "postal_code",
    "address",
)

ALLOWED_TYPES = {
    "幼稚園",
    "幼保連携型認定こども園",
    "小学校",
    "中学校",
    "義務教育学校",
    "高等学校",
    "中等教育学校",
    "特別支援学校",
}
ALLOWED_ESTABLISHMENTS = {"公立", "私立", "国立"}
POSTAL_CODE_PATTERN = re.compile(r"^\d{3}-\d{4}$")
PHONE_PATTERN = re.compile(r"^0\d{1,4}-\d{1,4}-\d{3,4}$")

# 千葉県版: 令和7→8年度の変更一覧（r8-gakkouichiran-2）で廃止・統合・休園が確定した学校名。
# これらがデータセットに残っていないかを確認する。
CHIBA_ABOLISHED_NAMES = {
    "横芝光町立日吉小学校", "横芝光町立上堺小学校",
    "勝浦市立興津小学校", "勝浦市立豊浜小学校", "勝浦市立総野小学校",
    "館山市立房南小学校", "館山市立神余小学校",
    "館山市立那古小学校", "館山市立船形小学校",
    "富津市立佐貫小学校", "富津市立環小学校",
    "茂原市立早野中学校", "富津市立大貫小学校",
    "市川市立新浜幼稚園", "市川市立信篤幼稚園", "野田市立関宿南部幼稚園",
    "佐倉市立佐倉幼稚園", "八街市立川上幼稚園", "袖ケ浦市立中川幼稚園",
    "八街市立朝陽幼稚園",
}

# 同上: 新設が確定した学校名。データセットに含まれているかを確認する。
CHIBA_NEW_SCHOOL_NAMES = {
    "八千代市立みどりが丘第二小学校",
    "館山市立まなびの杜房南小学校",
    "館山市立まなびの杜房南小学校神余分校",
    "館山市立那古船形小学校",
}

CHIBA_WARD_NAMES = {
    "千葉市中央区", "千葉市花見川区", "千葉市稲毛区",
    "千葉市若葉区", "千葉市緑区", "千葉市美浜区",
}

# 千葉県版: 原本(私立高等学校・中等教育学校（後期）名簿)に課程別で複数の電話番号が
# 正式に併記されている学校。1レコード内で "番号A / 番号B" 形式(courseの順序に対応)で
# 保持することを許容し、電話番号の形式検証では例外として扱う。
CHIBA_KNOWN_MULTI_PHONE = {
    "鴨川令徳高校": {
        "original_notation": "（全）04-7092-0267 （通）04-7099-0101",
        "reason": "全日制・通信制の2課程を1校で運営しており、原本が課程ごとに別番号を正式併記しているため。",
        "json_format": "04-7092-0267 / 04-7099-0101",
        "validation_treatment": "PHONE_PATTERNの単一番号チェックを免除し、許容リストとして扱う。",
    },
}
MULTI_PHONE_PATTERN = re.compile(r"^0\d{1,4}-\d{1,4}-\d{3,4}( / 0\d{1,4}-\d{1,4}-\d{3,4})+$")


def get_field(record: dict[str, Any], logical_name: str) -> str:
    for key in FIELD_ALIASES.get(logical_name, (logical_name,)):
        if key in record:
            value = record.get(key)
            if value:
                return str(value).strip()
    return ""


def load_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, list):
        raise ValueError("JSONのルートは配列である必要があります。")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError("配列内の各要素はオブジェクトである必要があります。")
    return value


def validate(records: list[dict[str, Any]], prefecture: str) -> tuple[list[str], list[str]]:
    """(errors, warnings) を返す。errors は検証失敗(exit 1)、warnings は参考情報のみ。"""
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    seen_exact: set[tuple[str, str, str]] = set()

    for index, record in enumerate(records, start=1):
        label = f"{index}件目"

        for logical_field in REQUIRED_LOGICAL_FIELDS:
            if not get_field(record, logical_field):
                errors.append(f"{label}: 必須項目 `{logical_field}` が空欄です。")

        record_id = str(record.get("id", "")).strip()
        if record_id:
            if record_id in seen_ids:
                errors.append(f"{label}: id `{record_id}` が重複しています。")
            seen_ids.add(record_id)

        school_type = get_field(record, "school_type")
        if school_type and school_type not in ALLOWED_TYPES:
            errors.append(f"{label}: 未定義の校種 `{school_type}` です。")

        establishment = get_field(record, "establishment")
        if establishment and establishment not in ALLOWED_ESTABLISHMENTS:
            errors.append(f"{label}: 未定義の設置区分 `{establishment}` です。")

        postal_code = get_field(record, "postal_code")
        if postal_code and not POSTAL_CODE_PATTERN.fullmatch(postal_code):
            errors.append(f"{label}: 郵便番号 `{postal_code}` の形式が不正です。")

        name = get_field(record, "name")
        phone = get_field(record, "phone")
        if phone and not PHONE_PATTERN.fullmatch(phone):
            known = CHIBA_KNOWN_MULTI_PHONE.get(name) if prefecture == "千葉県" else None
            if known and MULTI_PHONE_PATTERN.fullmatch(phone) and phone == known["json_format"]:
                warnings.append(
                    f"{label}: 電話番号複数併記の許容例外 `{name}` "
                    f"| 原本表記: {known['original_notation']} "
                    f"| 理由: {known['reason']} "
                    f"| JSON保存形式: {phone} "
                    f"| 検証上の扱い: {known['validation_treatment']}"
                )
            else:
                warnings.append(f"{label}: 電話番号 `{phone}` の形式を確認してください。")

        address = get_field(record, "address")
        if address and not address.startswith(prefecture):
            errors.append(f"{label}: 住所が `{prefecture}` で始まっていません。")

        municipality = get_field(record, "municipality")
        if prefecture == "千葉県" and municipality == "千葉市":
            errors.append(f"{label}: 市町村名が区まで含まれていません（`千葉市`のみ）。")
        if prefecture == "神奈川県" and municipality in ("横浜市", "川崎市", "相模原市"):
            errors.append(f"{label}: 市町村名が区まで含まれていません（`{municipality}`のみ）。")

        # school_type も含めて完全一致を判定する。同一住所・同一電話番号の建物に
        # 小学校の分校と中学校の分校が同居するなど、校種が異なれば別レコードとして正当。
        exact_key = (name, address, phone, school_type)
        if all(exact_key[:3]):
            if exact_key in seen_exact:
                errors.append(f"{label}: 学校名・住所・電話番号・校種が完全一致する重複です。")
            seen_exact.add(exact_key)

        if prefecture == "千葉県":
            # 注意: 公立「幼稚園」シートには、法的には幼稚園型認定こども園（school_type=幼稚園が正）と
            # 幼保連携型認定こども園（別シート・school_type=幼保連携型認定こども園）が混在する。
            # 名称に「こども園」を含むかどうかでは判別できないため、誤分類チェックはシート単位の
            # 抽出結果の整合性（school_type別件数が原本のシート行数と一致するか）で代替する。
            if school_type == "中等教育学校" and establishment == "私立":
                course = record.get("course") or []
                if set(course) != {"前期課程", "後期課程"}:
                    errors.append(f"{label}: 私立中等教育学校 `{name}` の course が前期・後期の統合になっていません（course={course}）。")
            if name in CHIBA_ABOLISHED_NAMES:
                errors.append(f"{label}: 廃止・統合済みのはずの `{name}` がデータに残存しています。")

    if prefecture == "千葉県":
        names = {get_field(r, "name") for r in records}
        for new_name in CHIBA_NEW_SCHOOL_NAMES:
            if new_name not in names:
                errors.append(f"新設校 `{new_name}` がデータセットに収録されていません。")

        high_school_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for record in records:
            if get_field(record, "school_type") != "高等学校":
                continue
            key = (get_field(record, "municipality"), get_field(record, "name"))
            high_school_groups.setdefault(key, []).append(record)
        for (municipality, name), group in high_school_groups.items():
            if len(group) > 1:
                warnings.append(
                    f"高等学校 `{name}`（{municipality}）が複数課程で分割されたまま残っています"
                    f"（{len(group)}件・自動統合できなかった可能性）。"
                )

        secondary = [r for r in records if get_field(r, "school_type") == "中等教育学校"]
        by_est = Counter(get_field(r, "establishment") for r in secondary)
        if by_est.get("私立", 0) != 2:
            warnings.append(f"私立中等教育学校の件数が想定(2件: 時任学園・三育学院)と異なります（{by_est.get('私立', 0)}件）。")

        no_source = [r for r in records if not str(r.get("source_url", "")).strip()]
        if no_source:
            warnings.append(f"出典URL(source_url)が空欄のレコードが{len(no_source)}件あります（原本不明の疑いがないか確認）。")

    return errors, warnings


def print_summary(records: list[dict[str, Any]]) -> None:
    by_type = Counter(get_field(item, "school_type") or "未設定" for item in records)
    by_establishment = Counter(get_field(item, "establishment") or "未設定" for item in records)
    by_type_est = Counter(
        (get_field(item, "school_type") or "未設定", get_field(item, "establishment") or "未設定")
        for item in records
    )
    print(f"総件数: {len(records):,}")
    print("校種別:")
    for name, count in sorted(by_type.items()):
        print(f"  {name}: {count:,}")
    print("設置区分別:")
    for name, count in sorted(by_establishment.items()):
        print(f"  {name}: {count:,}")
    print("校種×設置区分別:")
    for (t, e), count in sorted(by_type_est.items()):
        print(f"  {t} / {e}: {count:,}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--prefecture", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        records = load_records(args.json_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"読み込みエラー: {exc}", file=sys.stderr)
        return 2

    print_summary(records)
    errors, warnings = validate(records, args.prefecture)

    if warnings:
        print(f"\n警告: {len(warnings)}件")
        for warning in warnings:
            print(f"- {warning}")

    if errors:
        print(f"\n検証エラー: {len(errors)}件", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("\n基本検証に合格しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
