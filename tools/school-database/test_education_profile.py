#!/usr/bin/env python3
"""Validate the 都道府県教育統計 data, its integration into
prefecture-card-metadata.json, and its rendering wiring.

This is explicitly NOT a ranking of educational quality: no ordinal rank
("全国◯位" etc.) is ever displayed, and no comparative/value-judgment
adjectives ("高い/低い/多い/少ない" etc.) appear in any headline. Every
statistic must be independently recomputable from data already in this
repository (see generate_education_profile.py,
build_education_external_stats.py, and
docs/school-database/education-profile-source-manifest.md). No estimates,
no dummy values, no unsourced claims, no rank display."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE_JSON = ROOT / "data" / "school-database" / "prefecture-education-profile.json"
PREFECTURE_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-metadata.json"
CARD_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
EXTERNAL_STATS_JSON = ROOT / "data" / "school-database" / "prefecture-education-external-stats.json"
RENDERER_JS = ROOT / "assets" / "js" / "school-database" / "prefecture-card-renderer.js"
CSS_PATH = ROOT / "assets" / "css" / "school-database.css"
INDEX_HTML = ROOT / "tools" / "school-database" / "index.html"

PROHIBITED_TERMS = (
    "公式ランキング", "認定", "日本一", "都道府県章",
    # 価値判断・比較の程度を示す形容表現（順位表示の代替として使わない）。
    "高く", "高い", "低く", "低い", "多く", "多い", "少なく", "少ない",
)
RANK_PATTERN = re.compile(r"全国\d+位")

# Previously, 9 prefectures had a per-school `municipality` field that was
# entirely empty in data/school-database/{slug}.json (a data-pipeline bug in
# their convert_*_sources.py scripts, since fixed). That data-quality issue
# is now resolved for all 47 prefectures, so no slug is expected to be
# excluded from the depopulated_school_ratio join anymore.
KNOWN_EMPTY_MUNICIPALITY_SLUGS: set[str] = set()


def round1(value: float) -> float:
    return round(value, 1)


def test_prefecture_education_profile_json() -> None:
    payload = json.loads(PROFILE_JSON.read_text(encoding="utf-8"))
    prefectures = payload["prefectures"]
    assert len(prefectures) == 47, f"expected 47 prefectures, got {len(prefectures)}"
    assert payload["schema_version"] == 3, "順位表示を廃止したv3データではありません"

    codes = [p["prefecture_code"] for p in prefectures]
    assert len(set(codes)) == 47, "prefecture_code に重複があります"

    assert payload["education_profile_policy"]["no_dummy_values"] is True
    assert payload["education_profile_policy"]["no_estimates"] is True
    assert payload["education_profile_policy"]["not_an_official_ranking"] is True
    assert payload["education_profile_policy"]["not_an_educational_quality_ranking"] is True
    assert payload["education_profile_policy"]["no_rank_display"] is True

    metric_ids = {m["id"] for m in payload["methodology"]["metrics"]}
    assert metric_ids == {
        "private_school_ratio", "special_needs_school_ratio", "kindergarten_ratio",
        "child_population_share", "school_density", "student_teacher_ratio",
        "waiting_children_count", "depopulated_school_ratio", "ict_teaching_capability",
    }, f"想定と異なる指標セットです: {metric_ids}"
    cap = payload["methodology"]["cap_per_metric"]

    metric_assignment_counts: dict[str, int] = {}
    headline_texts = []
    for p in prefectures:
        assert p["available"] is True, f"{p['prefecture_name']}: available が true ではありません"
        assert p["metric_id"] in metric_ids, f"{p['prefecture_name']}: 未定義のmetric_id {p['metric_id']!r}"
        assert p["metric_label"], f"{p['prefecture_name']}: metric_label が空です"
        assert p["headline_text"], f"{p['prefecture_name']}: headline_text が空です"
        assert p["source_short_label"], f"{p['prefecture_name']}: source_short_label が空です"
        assert p["statistic_name"] == p["source_short_label"], (
            f"{p['prefecture_name']}: statistic_name が source_short_label と一致しません"
        )
        assert p["reference_date_display"], f"{p['prefecture_name']}: reference_date_display が空です"
        assert "not_a_ranking_note" not in p, (
            f"{p['prefecture_name']}: not_a_ranking_noteが残っています"
            "（注記はポータル1箇所に集約したためカード単位のデータからは削除済みのはず）"
        )
        assert p["value"] is not None, f"{p['prefecture_name']}: value が欠損しています"

        # 順位表示・タイ表記が完全に廃止されていること。
        assert not RANK_PATTERN.search(p["headline_text"]), (
            f"{p['prefecture_name']}: 見出し文に「全国◯位」の順位表示が残っています"
        )
        assert "位タイ" not in p["headline_text"], (
            f"{p['prefecture_name']}: 見出し文に「◯位タイ」表記が残っています"
        )
        assert "rank" not in p, f"{p['prefecture_name']}: rankフィールドが残っています"
        assert "tier" not in p, f"{p['prefecture_name']}: tierフィールドが残っています"

        for prohibited in PROHIBITED_TERMS:
            assert prohibited not in p["headline_text"], (
                f"{p['prefecture_name']}: 見出し文に禁止表現「{prohibited}」が含まれています"
            )

        # 全国平均を示す場合は数値の併記のみとし、上回る/下回るという
        # 比較の断定表現を伴わないこと。
        if p["national_average"] is not None:
            assert "全国平均" in p["headline_text"], (
                f"{p['prefecture_name']}: national_averageがあるのに見出し文に「全国平均」の記載がありません"
            )
            for comparison_word in ("上回", "下回", "超え", "満た"):
                assert comparison_word not in p["headline_text"], (
                    f"{p['prefecture_name']}: 見出し文に比較の断定表現「{comparison_word}」が含まれています"
                )

        metric_assignment_counts[p["metric_id"]] = metric_assignment_counts.get(p["metric_id"], 0) + 1
        headline_texts.append(p["headline_text"])

    for metric_id, count in metric_assignment_counts.items():
        assert count <= cap, f"{metric_id}: 指標割当が上限{cap}件を超えています（{count}件）"

    assert len(set(headline_texts)) > 1, "全県で同一の見出し文になっています"


def test_metric_values_and_averages_recomputable_from_source() -> None:
    """各指標の値・全国平均を、生データ（prefecture-metadata.json /
    prefecture-card-metadata.json / prefecture-education-external-stats.json）
    から独立に再計算し、一致することを確認する。"""
    profile_payload = json.loads(PROFILE_JSON.read_text(encoding="utf-8"))
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    external_payload = json.loads(EXTERNAL_STATS_JSON.read_text(encoding="utf-8"))

    meta_by_slug = {m["slug"]: m for m in prefecture_metadata}
    card_by_slug = {p["prefecture_code"]: p for p in card_payload["prefectures"]}
    external_by_slug = {p["prefecture_code"]: p for p in external_payload["prefectures"]}

    # 全県全指標の生値を再計算し、保存済みnational_averageの再現性も検証する。
    all_values: dict[str, dict[str, float]] = {
        "private_school_ratio": {}, "special_needs_school_ratio": {}, "kindergarten_ratio": {},
        "child_population_share": {}, "school_density": {}, "student_teacher_ratio": {},
        "waiting_children_count": {}, "depopulated_school_ratio": {}, "ict_teaching_capability": {},
    }
    for slug, meta in meta_by_slug.items():
        total = meta["total"]
        card_pref = card_by_slug[slug]
        external = external_by_slug[slug]
        if total > 0:
            all_values["private_school_ratio"][slug] = round1(meta["establishment_counts"]["private"] / total * 100)
            all_values["special_needs_school_ratio"][slug] = round1(meta["school_type_counts"].get("特別支援学校", 0) / total * 100)
            all_values["kindergarten_ratio"][slug] = round1(meta["school_type_counts"].get("幼稚園", 0) / total * 100)
            if meta["municipality_count"] > 0:
                all_values["school_density"][slug] = round1(total / meta["municipality_count"])
        population = card_pref.get("population")
        if population and population.get("available") is True:
            all_values["child_population_share"][slug] = round1(population["share_of_census_population_percent"])
        all_values["student_teacher_ratio"][slug] = external["student_teacher_ratio"]
        all_values["waiting_children_count"][slug] = external["waiting_children_count"]
        if external["depopulated_school_ratio"] is not None:
            all_values["depopulated_school_ratio"][slug] = external["depopulated_school_ratio"]
        all_values["ict_teaching_capability"][slug] = external["ict_teaching_capability"]

    expected_averages = {
        metric_id: round1(sum(vals.values()) / len(vals))
        for metric_id, vals in all_values.items() if vals
    }

    for p in profile_payload["prefectures"]:
        slug = p["prefecture_code"]
        metric_id = p["metric_id"]

        expected_value = all_values[metric_id][slug]
        assert math.isclose(expected_value, p["value"], abs_tol=1e-6), (
            f"{p['prefecture_name']}/{metric_id}: 再計算値({expected_value}) != 保存値({p['value']})"
        )
        expected_avg = expected_averages.get(metric_id)
        assert p["national_average"] == expected_avg, (
            f"{p['prefecture_name']}/{metric_id}: 再計算した全国平均({expected_avg}) != 保存値({p['national_average']})"
        )


def test_external_stats_file_integrity() -> None:
    payload = json.loads(EXTERNAL_STATS_JSON.read_text(encoding="utf-8"))
    prefectures = payload["prefectures"]
    assert len(prefectures) == 47
    assert payload["sources_policy"]["no_dummy_values"] is True
    assert payload["sources_policy"]["no_estimates"] is True

    waiting_total = sum(p["waiting_children_count"] for p in prefectures)
    assert waiting_total == 2254, (
        f"待機児童数の全国合計が公表値と一致しません（{waiting_total} != 2254）"
    )

    teacher_total = sum(p["student_teacher_ratio_detail"]["teacher_count"] for p in prefectures)
    student_total = sum(p["student_teacher_ratio_detail"]["student_count"] for p in prefectures)
    assert teacher_total == 424894, f"教員数の全国合計が公表値と一致しません（{teacher_total}）"
    assert student_total == 5812375, f"児童数の全国合計が公表値と一致しません（{student_total}）"

    none_depopulated = {
        p["prefecture_code"] for p in prefectures if p["depopulated_school_ratio"] is None
    }
    assert none_depopulated == KNOWN_EMPTY_MUNICIPALITY_SLUGS, (
        f"depopulated_school_ratioがNoneの県が想定と異なります"
        f"（municipalityデータ空の県は現在ないはずです）: {none_depopulated}"
    )


def test_card_metadata_education_profile_integration() -> None:
    payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    prefectures = payload["prefectures"]
    assert len(prefectures) == 47

    profile_payload = json.loads(PROFILE_JSON.read_text(encoding="utf-8"))
    profile_by_code = {p["prefecture_code"]: p for p in profile_payload["prefectures"]}

    assert set(p["prefecture_code"] for p in prefectures) == set(profile_by_code), (
        "47都道府県が一致しません（カードメタデータ vs 教育統計データ）"
    )

    for prefecture in prefectures:
        ep = prefecture["education_profile"]
        source_ref = profile_by_code[prefecture["prefecture_code"]]

        assert ep["available"] is True
        assert "rank" not in ep, f"{prefecture['prefecture_name']}: カードメタデータにrankフィールドが残っています"
        assert "tier" not in ep, f"{prefecture['prefecture_name']}: カードメタデータにtierフィールドが残っています"
        assert "not_a_ranking_note" not in ep, (
            f"{prefecture['prefecture_name']}: カードメタデータにnot_a_ranking_noteが残っています"
        )
        assert ep["metric_id"] == source_ref["metric_id"]
        assert ep["metric_label"] == source_ref["metric_label"]
        assert ep["value"] == source_ref["value"]
        assert ep["national_average"] == source_ref["national_average"]
        assert ep["headline_text"] == source_ref["headline_text"]
        assert ep["source_short_label"] == source_ref["source_short_label"]
        assert ep["reference_date_display"] == source_ref["reference_date_display"]
        assert ep["statistic_name"] == source_ref["statistic_name"]
        assert ep["not_an_official_ranking"] is True


def test_renderer_and_css_wire_profile_line() -> None:
    js = RENDERER_JS.read_text(encoding="utf-8")
    assert "education_profile" in js
    assert "education-profile-summary" in js
    assert "education-profile-metric-label" in js
    assert "education-profile-value" in js
    assert "education-profile-average-value" in js
    assert "pref-profile-source" in js
    assert "profile.available !== true" in js

    # カードごとの「順位付けではない」注記は2026-08-02にポータル1箇所への
    # 集約へ変更したため、レンダラーが再度カード単位で描画しないことを
    # 回帰防止として確認する。
    assert "not_a_ranking_note" not in js, (
        "カード単位の注記描画が復活しています（ポータル1箇所への集約方針に反します）"
    )
    assert "pref-profile-disclaimer" not in js, (
        "カード単位の注記クラスが復活しています（ポータル1箇所への集約方針に反します）"
    )

    css = CSS_PATH.read_text(encoding="utf-8")
    assert ".education-profile-summary" in css
    assert ".education-profile-metric-label" in css
    assert ".education-profile-value" in css
    assert ".education-profile-average-value" in css
    assert ".pref-profile-source" in css


def test_portal_html_shows_disclaimer() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "教育統計について" in html, (
        "「教育統計について」の見出しがindex.htmlに見つかりません"
    )
    assert "教育水準を順位付け・評価するものではありません" in html, (
        "教育統計が教育水準の順位付け・評価ではない旨の注記がindex.htmlに見つかりません"
    )
    # ポータル1箇所にのみ注記があること（重複していないこと）を確認する。
    assert html.count("教育水準を順位付け") == 1, (
        "教育水準を順位付けしない旨の注記がポータル内に複数箇所あります"
    )


if __name__ == "__main__":
    test_prefecture_education_profile_json()
    test_metric_values_and_averages_recomputable_from_source()
    test_external_stats_file_integrity()
    test_card_metadata_education_profile_integration()
    test_renderer_and_css_wire_profile_line()
    test_portal_html_shows_disclaimer()
    print("Prefecture education profile (v3, no ranking display) validation passed successfully.")
