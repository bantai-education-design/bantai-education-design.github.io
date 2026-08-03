#!/usr/bin/env python3
"""Pure content-building library for the per-prefecture "about this database"
SEO content (intro paragraph, population/education stats paragraph, feature
list, use-case list, FAQ). No file I/O — consumed by:
  - generate_prefecture_seo_content.py (renders the visible HTML section)
  - generate_seo_metadata.py (renders the matching FAQPage JSON-LD, so the
    structured data always matches what's visible on the page)

All numbers come from prefecture-metadata.json / prefecture-card-metadata.json
already in this repository; nothing is hand-typed or estimated. No evaluative
wording ("盛ん", "先進", "優れている" etc.) is used — only factual figures and
what the tool does, consistent with this project's "no unfounded official-
sounding claims" policy (see docs/school-database/education-profile-source-
manifest.md)."""

from __future__ import annotations

SCHOOL_TYPE_ORDER = [
    "幼稚園", "幼保連携型認定こども園", "小学校", "中学校",
    "義務教育学校", "高等学校", "中等教育学校", "特別支援学校",
]
SCHOOL_TYPE_UNIT = {
    "幼稚園": "園",
    "幼保連携型認定こども園": "園",
}


def format_number(n: int) -> str:
    return f"{n:,}"


def build_intro_paragraph(pref_name: str, meta: dict) -> str:
    total = meta["total"]
    municipality_count = meta["municipality_count"]
    school_type_count = meta["school_type_count"]
    type_counts = meta["school_type_counts"]
    est = meta["establishment_counts"]

    present_types = [t for t in SCHOOL_TYPE_ORDER if type_counts.get(t, 0) > 0]
    types_text = "、".join(present_types)

    est_parts = []
    if est.get("national", 0) > 0:
        est_parts.append(f"国立{format_number(est['national'])}校")
    est_parts.append(f"公立{format_number(est['public'])}校")
    est_parts.append(f"私立{format_number(est['private'])}校")
    if est.get("other", 0) > 0:
        est_parts.append(f"その他{format_number(est['other'])}校")
    est_text = "、".join(est_parts)

    return (
        f"{pref_name}学校データベースは、{pref_name}内{format_number(municipality_count)}"
        f"市区町村にある{types_text}（{school_type_count}種類の学校種）、合計"
        f"{format_number(total)}校・園の住所・電話番号情報を検索できるデータベースです。"
        f"設置区分別では{est_text}となっています。"
    )


def build_stats_paragraph(pref_name: str, card_pref: dict) -> str:
    population = card_pref["population"]
    education = card_pref["education_profile"]

    census_population = population["census_population"]
    census_age_3_17 = population["census_age_3_17"]
    share = population["share_of_census_population_percent"]
    reference_date_display = population["reference_date_display"]
    source_short_label = population["source_short_label"]

    intro = (
        f"{pref_name}の人口（日本国籍）は{format_number(census_population)}人、"
        f"このうち3〜17歳の学齢人口は{format_number(census_age_3_17)}人（{share}%）です"
        f"（出典：{source_short_label}、{reference_date_display}）。"
    )

    # child_population_shareが見出し指標の場合、直前の文と同じ割合の言い直しに
    # なるため、全国平均との比較のみを追記する（全く同じ文を重複させない）。
    if education["metric_id"] == "child_population_share":
        return f"{intro}全国平均は{education['national_average']}%です。"

    return f"{intro}{education['headline_text']}"


def build_features(pref_name: str, meta: dict) -> list[str]:
    municipality_count = meta["municipality_count"]
    return [
        "学校名・かな・住所・郵便番号・電話番号によるキーワード検索",
        f"{pref_name}内{format_number(municipality_count)}市区町村での絞り込み",
        "設置区分（国立・公立・私立）や学校種による絞り込み",
        "宛名データのコピー（校長先生宛て・園長先生宛てなど敬称を選択可能）",
        "Google Mapsでの所在地確認",
        "検索結果の宛先データをCSV形式でダウンロード",
    ]


def build_use_cases(pref_name: str) -> list[str]:
    return [
        f"{pref_name}内で転校・進学先の学校情報を調べたいとき",
        "学校・園への文書送付用の宛名を作成したいとき",
        f"{pref_name}の教育環境（学校数・校種構成）を把握したいとき",
    ]


def build_faq_items(pref_name: str, total: int, municipality_count: int, school_type_count: int) -> list[dict]:
    """Single source of truth for FAQ question/answer text — used for both
    the visible <details> markup and the FAQPage JSON-LD, so they always
    match exactly."""
    return [
        {
            "question": f"{pref_name}の学校は何件収録されていますか？",
            "answer": (
                f"{format_number(total)}校・園（{school_type_count}種類の学校種、"
                f"{format_number(municipality_count)}市区町村分）を収録しています。"
            ),
        },
        {
            "question": "どのようなデータをもとに作成されていますか？",
            "answer": (
                f"{pref_name}・市区町村の教育委員会や学校法人等の公式情報をもとに作成しています。"
                "詳細な出典はこのページ下部の「出典について」をご覧ください。"
            ),
        },
        {
            "question": "利用は無料ですか？会員登録は必要ですか？",
            "answer": "無料でご利用いただけます。会員登録やアプリのインストールも不要です。",
        },
        {
            "question": "スマートフォンやタブレットでも使えますか？",
            "answer": "はい、スマートフォンやタブレットのブラウザからもご利用いただけます。",
        },
        {
            "question": "学校名を正確に入力しないと検索できませんか？",
            "answer": "学校名の一部やかな、市区町村名、郵便番号、電話番号でも検索できます。",
        },
    ]


def build_content(pref_name: str, meta: dict, card_pref: dict) -> dict:
    total = meta["total"]
    municipality_count = meta["municipality_count"]
    school_type_count = meta["school_type_count"]
    return {
        "intro": build_intro_paragraph(pref_name, meta),
        "stats": build_stats_paragraph(pref_name, card_pref),
        "features": build_features(pref_name, meta),
        "use_cases": build_use_cases(pref_name),
        "faq": build_faq_items(pref_name, total, municipality_count, school_type_count),
    }
