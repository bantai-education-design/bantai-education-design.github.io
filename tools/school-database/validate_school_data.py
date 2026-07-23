#!/usr/bin/env python3
"""Ban.Tai 学校データベースJSONの基本検証。

使用例:
    python tools/school-database/validate_school_data.py data/school-database/saitama.json --prefecture 埼玉県
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "school_name",
    "school_type",
    "establishment_type",
    "municipality",
    "postal_code",
    "address",
)

ALLOWED_TYPES = {
    "幼稚園",
    "小学校",
    "中学校",
    "義務教育学校",
    "高等学校",
    "中等教育学校",
    "特別支援学校",
}
ALLOWED_ESTABLISHMENTS = {"公立", "私立", "国立"}
POSTAL_CODE_PATTERN = re.compile(r"^\d{3}-\d{4}$")


def load_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, list):
        raise ValueError("JSONのルートは配列である必要があります。")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError("配列内の各要素はオブジェクトである必要があります。")
    return value


def validate(records: list[dict[str, Any]], prefecture: str) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_exact: set[tuple[str, str, str]] = set()

    for index, record in enumerate(records, start=1):
        label = f"{index}件目"

        for field in REQUIRED_FIELDS:
            if not str(record.get(field, "")).strip():
                errors.append(f"{label}: 必須項目 `{field}` が空欄です。")

        record_id = str(record.get("id", "")).strip()
        if record_id:
            if record_id in seen_ids:
                errors.append(f"{label}: id `{record_id}` が重複しています。")
            seen_ids.add(record_id)

        school_type = str(record.get("school_type", "")).strip()
        if school_type and school_type not in ALLOWED_TYPES:
            errors.append(f"{label}: 未定義の校種 `{school_type}` です。")

        establishment = str(record.get("establishment_type", "")).strip()
        if establishment and establishment not in ALLOWED_ESTABLISHMENTS:
            errors.append(f"{label}: 未定義の設置区分 `{establishment}` です。")

        postal_code = str(record.get("postal_code", "")).strip()
        if postal_code and not POSTAL_CODE_PATTERN.fullmatch(postal_code):
            errors.append(f"{label}: 郵便番号 `{postal_code}` の形式が不正です。")

        address = str(record.get("address", "")).strip()
        if address and not address.startswith(prefecture):
            errors.append(f"{label}: 住所が `{prefecture}` で始まっていません。")

        exact_key = (
            str(record.get("school_name", "")).strip(),
            address,
            str(record.get("phone", "")).strip(),
        )
        if all(exact_key):
            if exact_key in seen_exact:
                errors.append(f"{label}: 学校名・住所・電話番号が完全一致する重複です。")
            seen_exact.add(exact_key)

    return errors


def print_summary(records: list[dict[str, Any]]) -> None:
    by_type = Counter(str(item.get("school_type", "未設定")) for item in records)
    by_establishment = Counter(
        str(item.get("establishment_type", "未設定")) for item in records
    )
    print(f"総件数: {len(records):,}")
    print("校種別:")
    for name, count in sorted(by_type.items()):
        print(f"  {name}: {count:,}")
    print("設置区分別:")
    for name, count in sorted(by_establishment.items()):
        print(f"  {name}: {count:,}")


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
    errors = validate(records, args.prefecture)
    if errors:
        print(f"\n検証エラー: {len(errors)}件", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("\n基本検証に合格しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
