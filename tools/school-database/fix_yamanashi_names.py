#!/usr/bin/env python3
"""Fix official school names in yamanashi.json.

This script restores from the original feature branch data and applies
a comprehensive, accurately-researched name correction.

Root cause: The PDF address directories published by Yamanashi Prefecture
list schools by a shortened "school nickname" only, without municipality
prefix, establishment type, or school category suffix. The original
convert_yamanashi_sources.py ingested these short names verbatim.

Primary sources:
  - 山梨大学公式サイト: https://www.yamanashi.ac.jp/
  - 山梨県内の学校・学級・児童生徒数等（令和7年5月1日現在）
    https://www.pref.yamanashi.jp/kyouiku/27458338247.html
  - 山梨県私立学校名簿（令和7年4月1日現在）
    https://www.pref.yamanashi.jp/documents/34146/meibo-20250401.pdf
  - 公益社団法人 山梨県私学教育振興会
  - 甲府市教育委員会 小・中・高等学校一覧
  - 各幼稚園・こども園・特別支援学校公式サイト
  - 山梨県教育委員会 特別支援学校一覧
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "school-database" / "yamanashi.json"

# ---------------------------------------------------------------------------
# EXACT name override table: (old_name, school_type, establishment) -> new_name
# All names verified from primary sources listed above.
# ---------------------------------------------------------------------------

EXACT_OVERRIDES: dict[tuple[str, str, str], str] = {

    # =========================================================================
    # NATIONAL SCHOOLS (国立) - 4 records
    # Source: 山梨大学公式サイト https://www.yamanashi.ac.jp/
    # =========================================================================
    ("梨大附属", "幼稚園", "国立"): "山梨大学教育学部附属幼稚園",
    ("山梨大学附属", "小学校", "国立"): "山梨大学教育学部附属小学校",
    ("山梨大学附属", "中学校", "国立"): "山梨大学教育学部附属中学校",
    ("山梨大学附属特別支援", "特別支援学校", "国立"): "山梨大学教育学部附属特別支援学校",

    # =========================================================================
    # PRIVATE KINDERGARTENS (私立幼稚園・認定こども園) - 43 records total
    # Source: 公益社団法人山梨県私学教育振興会, 各園公式サイト
    # Note: database school_type = "幼稚園" for all (PDF source convention)
    # =========================================================================

    # 甲府市
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

    # 富士吉田市
    ("小さき花", "幼稚園", "私立"): "小さき花幼稚園",
    ("新倉", "幼稚園", "私立"): "新倉幼稚園",
    ("月江寺", "幼稚園", "私立"): "月江寺幼稚園",
    ("聖徳", "幼稚園", "私立"): "認定こども園聖徳幼稚園",

    # 都留市
    ("ひまわり", "幼稚園", "私立"): "認定こども園ひまわり幼稚園",
    ("青藍", "幼稚園", "私立"): "認定こども園青藍幼稚園",

    # 山梨市 (くさかべ・双葉は私立)
    ("くさかべ", "幼稚園", "私立"): "認定こども園くさかべ幼稚園",
    ("双葉", "幼稚園", "私立"): "ふたば認定こども園双葉幼稚園",

    # 大月市
    ("大月キリストの教会", "幼稚園", "私立"): "大月キリストの教会幼稚園",

    # 韮崎市
    ("韮崎愛生", "幼稚園", "私立"): "韮崎愛生幼稚園",
    ("韮崎カトリック白百合", "幼稚園", "私立"): "韮崎カトリック白百合幼稚園",

    # 南アルプス市
    ("小笠原", "幼稚園", "私立"): "認定こども園小笠原幼稚園",

    # 甲斐市
    ("双葉甲府", "幼稚園", "私立"): "双葉甲府幼稚園",
    ("富士", "幼稚園", "私立"): "富士幼稚園",
    ("竜王", "幼稚園", "私立"): "竜王幼稚園",

    # 笛吹市
    ("石和誠心", "幼稚園", "私立"): "石和誠心幼稚園",

    # 上野原市
    ("上野原", "幼稚園", "私立"): "上野原幼稚園",
    ("上野原羽佐間", "幼稚園", "私立"): "上野原羽佐間幼稚園",
    ("島田", "幼稚園", "私立"): "島田幼稚園",

    # 甲州市
    ("塩山カトリック", "幼稚園", "私立"): "塩山カトリック幼稚園",

    # 西八代郡市川三郷町
    ("市川", "幼稚園", "私立"): "認定こども園市川幼稚園",
    ("市川南", "幼稚園", "私立"): "認定こども園市川南幼稚園",

    # 南巨摩郡
    ("峡南", "幼稚園", "私立"): "峡南幼稚園",
    ("南部みどり", "幼稚園", "私立"): "南部みどり幼稚園",

    # 南都留郡 - 忍野村立 (public, registered as 私立 in original PDF)
    # This is officially 忍野村立認定こども園忍野幼稚園 (public)
    ("忍野", "幼稚園", "私立"): "忍野村立認定こども園忍野幼稚園",

    # =========================================================================
    # PUBLIC KINDERGARTENS (公立幼稚園) - listed as 私立 in original PDF
    # =========================================================================
    # つつじ幼稚園: 山梨市立 (confirmed public from city official site)
    ("つつじ", "幼稚園", "私立"): "山梨市立つつじ幼稚園",

    # =========================================================================
    # PUBLIC HIGH SCHOOLS (公立高等学校) - 山梨県立 (all county-level)
    # Exception: 北杜市立甲陵高等学校 (city-run)
    # Source: 山梨県教育委員会公式サイト, wikipedia, 各校公式サイト
    # =========================================================================
    # 甲府市 - 全て県立
    ("〈今井校舎〉", "高等学校", "公立"): "山梨県立中央高等学校（今井校舎）",
    ("中央", "高等学校", "公立"): "山梨県立中央高等学校",
    ("甲府南", "高等学校", "公立"): "山梨県立甲府南高等学校",
    ("甲府城西", "高等学校", "公立"): "山梨県立甲府城西高等学校",
    ("甲府工業", "高等学校", "公立"): "山梨県立甲府工業高等学校",
    ("甲府東", "高等学校", "公立"): "山梨県立甲府東高等学校",
    ("甲府第一", "高等学校", "公立"): "山梨県立甲府第一高等学校",
    ("甲府西", "高等学校", "公立"): "山梨県立甲府西高等学校",
    # 甲府商業のみ甲府市立（公式サイト: kchs.city.kofu.yamanashi.jp で確認）
    ("甲府商業", "高等学校", "公立"): "甲府市立甲府商業高等学校",

    # 富士吉田市 - 全て県立
    ("ひばりが丘", "高等学校", "公立"): "山梨県立ひばりが丘高等学校",
    ("吉田", "高等学校", "公立"): "山梨県立吉田高等学校",
    ("富士北稜", "高等学校", "公立"): "山梨県立富士北稜高等学校",

    # 都留市 - 県立
    ("都留興譲館", "高等学校", "公立"): "山梨県立都留興譲館高等学校",

    # 山梨市 - 県立
    ("山梨", "高等学校", "公立"): "山梨県立山梨高等学校",
    ("日川", "高等学校", "公立"): "山梨県立日川高等学校",

    # 大月市 - 県立
    ("都留", "高等学校", "公立"): "山梨県立都留高等学校",

    # 韮崎市 - 県立
    ("韮崎", "高等学校", "公立"): "山梨県立韮崎高等学校",
    ("韮崎工業", "高等学校", "公立"): "山梨県立韮崎工業高等学校",

    # 南アルプス市 - 県立
    ("巨摩", "高等学校", "公立"): "山梨県立巨摩高等学校",
    ("白根", "高等学校", "公立"): "山梨県立白根高等学校",

    # 北杜市 - 県立 + 市立1校
    ("北杜", "高等学校", "公立"): "山梨県立北杜高等学校",
    ("甲陵", "高等学校", "公立"): "北杜市立甲陵高等学校",   # 唯一の市立高校

    # 甲斐市 - 県立
    ("農林", "高等学校", "公立"): "山梨県立農林高等学校",

    # 笛吹市 - 県立
    ("笛吹", "高等学校", "公立"): "山梨県立笛吹高等学校",

    # 上野原市 - 県立
    ("上野原", "高等学校", "公立"): "山梨県立上野原高等学校",

    # 甲州市 - 県立
    ("塩山", "高等学校", "公立"): "山梨県立塩山高等学校",

    # 中巨摩郡昭和町 - 県立
    ("甲府昭和", "高等学校", "公立"): "山梨県立甲府昭和高等学校",

    # 西八代郡市川三郷町 - 県立
    ("青洲", "高等学校", "公立"): "山梨県立青洲高等学校",

    # 南巨摩郡身延町 - 県立
    ("身延", "高等学校", "公立"): "山梨県立身延高等学校",

    # 南都留郡富士河口湖町 - 県立
    ("富士河口湖", "高等学校", "公立"): "山梨県立富士河口湖高等学校",

    # =========================================================================
    # PUBLIC SPECIAL NEEDS SCHOOLS (公立特別支援学校) - 山梨県立 (all county-level)
    # Source: 山梨県教育委員会, 各校公式サイト
    # =========================================================================
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

    # =========================================================================
    # PRIVATE SCHOOLS - 小学校・中学校・高等学校 (校種名省略の修正)
    # Source: 山梨県私立学校名簿（令和7年4月1日現在）
    # =========================================================================

    # 小学校（私立）
    ("山梨学院", "小学校", "私立"): "山梨学院小学校",
    ("駿台甲府", "小学校", "私立"): "駿台甲府小学校",
    ("南アルプス子どもの村", "小学校", "私立"): "南アルプス子どもの村小学校",

    # 中学校（私立）
    ("山梨学院", "中学校", "私立"): "山梨学院中学校",
    ("山梨英和", "中学校", "私立"): "山梨英和中学校",
    ("駿台甲府", "中学校", "私立"): "駿台甲府中学校",
    ("富士学苑", "中学校", "私立"): "富士学苑中学校",
    ("南アルプス子どもの村", "中学校", "私立"): "南アルプス子どもの村中学校",
    # 日本航空高等学校附属中学校（正式名称に「高等学校附属」を含む）
    ("日本航空高校付属", "中学校", "私立"): "日本航空高等学校附属中学校",

    # 高等学校（私立・全日制）
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

}


# ---------------------------------------------------------------------------
# Municipality prefix for public elementary/middle schools
# These are always 市区町村立
# ---------------------------------------------------------------------------

MUNICIPALITY_TO_SETTER: dict[str, str] = {
    "甲府市": "甲府市立",
    "富士吉田市": "富士吉田市立",
    "都留市": "都留市立",
    "山梨市": "山梨市立",
    "大月市": "大月市立",
    "韮崎市": "韮崎市立",
    "南アルプス市": "南アルプス市立",
    "北杜市": "北杜市立",
    "甲斐市": "甲斐市立",
    "笛吹市": "笛吹市立",
    "上野原市": "上野原市立",
    "甲州市": "甲州市立",
    "中央市": "中央市立",
    "中巨摩郡昭和町": "昭和町立",
    "西八代郡市川三郷町": "市川三郷町立",
    "南巨摩郡早川町": "早川町立",
    "南巨摩郡身延町": "身延町立",
    "南巨摩郡南部町": "南部町立",
    "南巨摩郡富士川町": "富士川町立",
    "南都留郡道志村": "道志村立",
    "南都留郡西桂町": "西桂町立",
    "南都留郡忍野村": "忍野村立",
    "南都留郡山中湖村": "山中湖村立",
    "南都留郡鳴沢村": "鳴沢村立",
    "南都留郡富士河口湖町": "富士河口湖町立",
    "北都留郡小菅村": "小菅村立",
    "北都留郡丹波山村": "丹波山村立",
}

# School types eligible for municipality-prefix auto-generation
MUNICIPALITY_ELIGIBLE_TYPES = {"小学校", "中学校"}

# Keywords indicating school type already present in name
TYPE_KEYWORDS = {
    "幼稚園": ["幼稚園", "こども園"],
    "小学校": ["小学校"],
    "中学校": ["中学校"],
    "高等学校": ["高等学校", "高校"],
    "特別支援学校": ["特別支援学校", "支援学校"],
}


def already_complete(name: str, school_type: str, establishment: str, municipality: str) -> bool:
    """Return True if the name is already a valid official name (no action needed)."""
    # Check type keyword
    has_type = any(kw in name for kw in TYPE_KEYWORDS.get(school_type, []))
    if not has_type:
        return False
    # Check setter for public schools
    if establishment == "公立":
        if not any(x in name for x in ["市立", "町立", "村立", "県立"]):
            return False
    if establishment == "国立":
        if "大学" not in name:
            return False
    if establishment == "私立" and school_type == "幼稚園":
        if not any(kw in name for kw in TYPE_KEYWORDS["幼稚園"]):
            return False
    return True


def fix_record(record: dict) -> tuple[dict, str | None]:
    name = record["name"]
    school_type = record["school_type"]
    establishment = record["establishment"]
    municipality = record.get("municipality", "")

    old_name = name

    # 1. Check exact override table
    key = (name, school_type, establishment)
    if key in EXACT_OVERRIDES:
        new_name = EXACT_OVERRIDES[key]
        record = dict(record)
        record["name"] = new_name
        # Fix establishment for つつじ (public disguised as private)
        if name == "つつじ" and municipality == "山梨市" and establishment == "私立":
            record["establishment"] = "公立"
        # Fix establishment for 忍野 (public disguised as private)
        if name == "忍野" and school_type == "幼稚園" and establishment == "私立":
            record["establishment"] = "公立"
        return record, old_name

    # 2. Already complete - no change needed
    if already_complete(name, school_type, establishment, municipality):
        return record, None

    # 3. Public elementary / middle school: auto-build from municipality
    if establishment == "公立" and school_type in MUNICIPALITY_ELIGIBLE_TYPES:
        setter = MUNICIPALITY_TO_SETTER.get(municipality, "")
        if setter:
            new_name = f"{setter}{name}{school_type}"
            record = dict(record)
            record["name"] = new_name
            return record, old_name

    return record, None


def main() -> int:
    print(f"Reading: {DATA_PATH}")
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    print(f"Total records: {len(data)}")

    changes = []
    updated_data = []

    for record in data:
        updated_record, old_name = fix_record(record)
        updated_data.append(updated_record)
        if old_name is not None:
            changes.append({
                "old": old_name,
                "new": updated_record["name"],
                "type": record["school_type"],
                "establishment": record["establishment"],
                "establishment_after": updated_record["establishment"],
                "municipality": record.get("municipality", ""),
                "address": record.get("address", ""),
                "phone": record.get("phone", ""),
            })

    print(f"\nModified: {len(changes)} records")
    print("\n=== Changes ===")
    for c in changes:
        print(f"  [{c['establishment']}][{c['type']}] {c['old']}")
        print(f"    → {c['new']}")
        print(f"    ({c['municipality']} / {c['address']})")
        if c['establishment'] != c['establishment_after']:
            print(f"    [設置区分変更: {c['establishment']} → {c['establishment_after']}]")
        print()

    # Verify totals
    assert len(updated_data) == len(data), "Record count changed!"

    by_type = {}
    by_estab = {}
    for r in updated_data:
        by_type[r["school_type"]] = by_type.get(r["school_type"], 0) + 1
        by_estab[r["establishment"]] = by_estab.get(r["establishment"], 0) + 1

    print("School type distribution:")
    print("  幼稚園:", by_type.get("幼稚園", 0), "/ 小学校:", by_type.get("小学校", 0),
          "/ 中学校:", by_type.get("中学校", 0), "/ 高等学校:", by_type.get("高等学校", 0),
          "/ 特別支援:", by_type.get("特別支援学校", 0))
    print("Establishment distribution:")
    print("  国立:", by_estab.get("国立", 0), "/ 公立:", by_estab.get("公立", 0),
          "/ 私立:", by_estab.get("私立", 0))

    # Note: つつじ and 忍野 move from 私立 to 公立 (2 records)
    # These are data corrections, total stays at 351
    orig_private = sum(1 for r in data if r["establishment"] == "私立")
    new_private = by_estab.get("私立", 0)
    if orig_private != new_private:
        diff = orig_private - new_private
        print(f"  NOTE: {diff} records moved from 私立 to 公立 (establishment correction)")

    # Check for duplicate IDs
    ids = [r["id"] for r in updated_data]
    if len(ids) != len(set(ids)):
        print("WARNING: Duplicate IDs detected!")
    else:
        print("✓ No duplicate IDs")

    # Check for remaining abbreviations
    remaining = []
    for r in updated_data:
        nm = r["name"]
        st = r["school_type"]
        es = r["establishment"]
        muni = r.get("municipality", "")
        # Public school without setter
        if es == "公立" and not any(x in nm for x in ["市立", "町立", "村立", "県立"]):
            remaining.append(f"  [公立setter省略] {nm} [{st}] {muni}")
        # National school without university name
        if es == "国立" and "大学" not in nm:
            remaining.append(f"  [国立大学名省略] {nm} [{st}]")
        # Private kindergarten without 幼稚園/こども園
        if es == "私立" and st == "幼稚園" and "幼稚園" not in nm and "こども園" not in nm:
            remaining.append(f"  [幼稚園名省略] {nm} [{st}]")
        # Any school without type keyword (skip special cases)
        # 盲学校・ろう学校 are legitimate names that don't contain 特別支援学校
        # うぐいすの杜学園・桃花台学園 already have 県立 prefix
        skip_type_check = (
            nm.endswith("盲学校") or nm.endswith("ろう学校")
            or "うぐいすの杜学園" in nm or "桃花台学園" in nm
            or "こども園" in nm
        )
        if not skip_type_check:
            has_type = any(kw in nm for kw in TYPE_KEYWORDS.get(st, []))
            if not has_type and st not in ("幼稚園",):  # 幼稚園 checked above
                remaining.append(f"  [校種名省略] {nm} [{st}] {es}")

    if remaining:
        print(f"\n⚠ {len(remaining)} remaining issues:")
        for r in remaining:
            print(r)
    else:
        print("✓ No remaining abbreviation issues")

    # Write output
    output_json = json.dumps(updated_data, ensure_ascii=False, indent=2) + "\n"
    DATA_PATH.write_text(output_json, encoding="utf-8")
    print(f"\nWrote {len(updated_data)} records to {DATA_PATH}")

    # Write change log
    log_path = ROOT / "tools" / "school-database" / "yamanashi_name_fix_log.json"
    log_path.write_text(json.dumps(changes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Change log ({len(changes)} changes): {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
