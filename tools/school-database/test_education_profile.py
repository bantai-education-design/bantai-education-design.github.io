#!/usr/bin/env python3
"""Validate the 都道府県教育プロフィール（1行タグライン） data (v1 in-repo
metrics + v2 externally-researched metrics), its integration into
prefecture-card-metadata.json, and its rendering wiring.

This is NOT a test of an official government ranking — every value must be
independently recomputable from data already in this repository (see
generate_education_profile.py, build_education_external_stats.py, and
docs/school-database/education-profile-source-manifest.md). No estimates,
no dummy values, no unsourced claims."""

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

PROHIBITED_TERMS = ("公式ランキング", "認定", "日本一", "都道府県章")

# The 9 prefectures whose per-school `municipality` field is entirely empty
# in data/school-database/{slug}.json (a pre-existing, separately-tracked
# data-pipeline issue — see the spawn_task filed against the identical
# `municipality_count == 0` symptom in prefecture-metadata.json). The
# depopulated_school_ratio join can never produce a real value for these,
# so build_education_external_stats.py stores None rather than a
# fabricated-looking 0%.
KNOWN_EMPTY_MUNICIPALITY_SLUGS = {
    "gifu", "gunma", "ishikawa", "kyoto", "mie", "nara", "shimane", "shizuoka", "tottori",
}


def round1(value: float) -> float:
    return round(value, 1)


def _compute_all_metric_values() -> dict[str, dict[str, float]]:
    """全47県×9指標の生値を、保存済みprofile.jsonを一切参照せず独立に
    再計算する（tier1割当の有無に関わらず、タイ判定を正しく検証するため
    には全県の値が必要）。generate_education_profile.pyのロジックと
    build_education_external_stats.pyの出力を直接の一次情報源とする。"""
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    external_payload = json.loads(EXTERNAL_STATS_JSON.read_text(encoding="utf-8"))

    meta_by_slug = {m["slug"]: m for m in prefecture_metadata}
    card_by_slug = {p["prefecture_code"]: p for p in card_payload["prefectures"]}
    external_by_slug = {p["prefecture_code"]: p for p in external_payload["prefectures"]}

    values: dict[str, dict[str, float]] = {
        "private_school_ratio": {}, "special_needs_school_ratio": {}, "kindergarten_ratio": {},
        "child_population_share": {}, "school_density": {}, "student_teacher_ratio": {},
        "waiting_children_count": {}, "depopulated_school_ratio": {}, "ict_teaching_capability": {},
    }
    for slug, meta in meta_by_slug.items():
        total = meta["total"]
        card_pref = card_by_slug[slug]
        external = external_by_slug[slug]
        if total > 0:
            values["private_school_ratio"][slug] = round1(meta["establishment_counts"]["private"] / total * 100)
            values["special_needs_school_ratio"][slug] = round1(meta["school_type_counts"].get("特別支援学校", 0) / total * 100)
            values["kindergarten_ratio"][slug] = round1(meta["school_type_counts"].get("幼稚園", 0) / total * 100)
            if meta["municipality_count"] > 0:
                values["school_density"][slug] = round1(total / meta["municipality_count"])
        population = card_pref.get("population")
        if population and population.get("available") is True:
            values["child_population_share"][slug] = round1(population["share_of_census_population_percent"])
        values["student_teacher_ratio"][slug] = external["student_teacher_ratio"]
        values["waiting_children_count"][slug] = external["waiting_children_count"]
        if external["depopulated_school_ratio"] is not None:
            values["depopulated_school_ratio"][slug] = external["depopulated_school_ratio"]
        values["ict_teaching_capability"][slug] = external["ict_teaching_capability"]
    return values


def _tie_aware_ranks(slug_values: dict[str, float], direction: str) -> dict[str, int]:
    sign = 1 if direction == "higher" else -1
    ranks = {}
    for slug, value in slug_values.items():
        better_count = sum(1 for v in slug_values.values() if sign * v > sign * value)
        ranks[slug] = better_count + 1
    return ranks


def test_prefecture_education_profile_json() -> None:
    payload = json.loads(PROFILE_JSON.read_text(encoding="utf-8"))
    prefectures = payload["prefectures"]
    assert len(prefectures) == 47, f"expected 47 prefectures, got {len(prefectures)}"
    assert payload["schema_version"] == 2, "外部統計4分野が統合されたv2データではありません"

    codes = [p["prefecture_code"] for p in prefectures]
    assert len(set(codes)) == 47, "prefecture_code に重複があります"

    assert payload["education_profile_policy"]["no_dummy_values"] is True
    assert payload["education_profile_policy"]["no_estimates"] is True
    assert payload["education_profile_policy"]["not_an_official_ranking"] is True

    metric_defs = {m["id"]: m for m in payload["methodology"]["metrics"]}
    metric_ids = set(metric_defs)
    assert metric_ids == {
        "private_school_ratio", "special_needs_school_ratio", "kindergarten_ratio",
        "child_population_share", "school_density", "student_teacher_ratio",
        "waiting_children_count", "depopulated_school_ratio", "ict_teaching_capability",
    }, f"想定と異なる指標セットです: {metric_ids}"
    tier1_max_rank = payload["methodology"]["tier1_max_rank"]
    cap = payload["methodology"]["tier1_cap_per_metric"]

    # 全県×全指標の生値からタイ含みの順位を独立に再計算する（見出しに
    # 採用されなかった側の県でも同値ならタイになるため、tier1割当済みの
    # エントリだけを見てグループ化すると見逃しがある — 必ず全県の生値
    # から計算し直すこと）。
    all_values = _compute_all_metric_values()
    all_ranks = {
        metric_id: _tie_aware_ranks(slug_values, metric_defs[metric_id]["direction"])
        for metric_id, slug_values in all_values.items()
    }

    metric_tier1_counts: dict[str, int] = {}
    for p in prefectures:
        assert p["available"] is True, f"{p['prefecture_name']}: available が true ではありません"
        assert p["headline_text"], f"{p['prefecture_name']}: headline_text が空です"
        assert p["source_short_label"], f"{p['prefecture_name']}: source_short_label が空です"
        assert p["reference_date_display"], f"{p['prefecture_name']}: reference_date_display が空です"
        assert p["tier"] in ("tier1", "fallback_a", "fallback_b"), (
            f"{p['prefecture_name']}: 想定外のtier {p['tier']!r}"
        )

        if p["tier"] in ("tier1", "fallback_a"):
            assert p["metric_id"] in metric_ids, f"{p['prefecture_name']}: 未定義のmetric_id {p['metric_id']!r}"

        if p["tier"] == "tier1":
            assert p["rank"] is not None and p["rank"] <= tier1_max_rank, (
                f"{p['prefecture_name']}: tier1なのに順位が{p['rank']}（{tier1_max_rank}位以内である必要があります）"
            )
            assert re.search(r"全国\d+位", p["headline_text"]), (
                f"{p['prefecture_name']}: tier1の見出し文に「全国◯位」の表記がありません"
            )
            metric_tier1_counts[p["metric_id"]] = metric_tier1_counts.get(p["metric_id"], 0) + 1

            slug = p["prefecture_code"]
            metric_id = p["metric_id"]
            expected_rank = all_ranks[metric_id][slug]
            assert p["rank"] == expected_rank, (
                f"{p['prefecture_name']}/{metric_id}: 保存された順位({p['rank']})が独立再計算({expected_rank})と一致しません"
            )
            expected_group_size = sum(1 for r in all_ranks[metric_id].values() if r == expected_rank)
            expected_tied = expected_group_size > 1
            assert p["rank_tied"] == expected_tied, (
                f"{p['prefecture_name']}/{metric_id}: rank_tiedフラグ({p['rank_tied']})が"
                f"全県の生値から再計算した同順位状況({expected_tied}, 同順位件数={expected_group_size})と一致しません"
            )
            has_tie_text = "位タイ" in p["headline_text"]
            assert has_tie_text == expected_tied, (
                f"{p['prefecture_name']}: 見出し文の「タイ」表記の有無が実際の同順位状況と一致しません"
            )
        else:
            # フォールバックA/Bでは、順位を断定する表現を含めない
            # （全国平均超/未満という緩やかな表現、または比較なしの説明文のみ）。
            assert not re.search(r"全国\d+位", p["headline_text"]), (
                f"{p['prefecture_name']}: フォールバック文なのに「全国◯位」を含んでいます"
            )

        for prohibited in PROHIBITED_TERMS:
            assert prohibited not in p["headline_text"], (
                f"{p['prefecture_name']}: 見出し文に禁止表現「{prohibited}」が含まれています"
            )

    for metric_id, count in metric_tier1_counts.items():
        assert count <= cap, f"{metric_id}: tier1割当が上限{cap}件を超えています（{count}件）"

    # 少なくとも1件は実際にタイが存在すること（このテストのタイ判定ロジック
    # 自体が意味のある検証をしていることの確認 — 47県×9指標もあれば
    # 同値は必ず発生する）。
    assert any(p.get("rank_tied") for p in prefectures if p["tier"] == "tier1"), (
        "同順位（タイ）が1件も検出されていません。タイ判定ロジックが正しく動作しているか確認してください。"
    )

    headline_texts = [p["headline_text"] for p in prefectures]
    assert len(set(headline_texts)) > 1, "全県で同一の見出し文になっています"


def test_metric_values_recomputable_from_source() -> None:
    """各指標の値・順位を、生データ（prefecture-metadata.json /
    prefecture-card-metadata.json / prefecture-education-external-stats.json）
    から独立に再計算し、一致することを確認する。"""
    profile_payload = json.loads(PROFILE_JSON.read_text(encoding="utf-8"))
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    external_payload = json.loads(EXTERNAL_STATS_JSON.read_text(encoding="utf-8"))

    meta_by_slug = {m["slug"]: m for m in prefecture_metadata}
    card_by_slug = {p["prefecture_code"]: p for p in card_payload["prefectures"]}
    external_by_slug = {p["prefecture_code"]: p for p in external_payload["prefectures"]}

    for p in profile_payload["prefectures"]:
        if p["tier"] not in ("tier1", "fallback_a"):
            continue
        slug = p["prefecture_code"]
        meta = meta_by_slug[slug]
        card_pref = card_by_slug[slug]
        external = external_by_slug[slug]
        total = meta["total"]

        if p["metric_id"] == "private_school_ratio":
            expected = round1(meta["establishment_counts"]["private"] / total * 100)
        elif p["metric_id"] == "special_needs_school_ratio":
            expected = round1(meta["school_type_counts"].get("特別支援学校", 0) / total * 100)
        elif p["metric_id"] == "kindergarten_ratio":
            expected = round1(meta["school_type_counts"].get("幼稚園", 0) / total * 100)
        elif p["metric_id"] == "child_population_share":
            expected = round1(card_pref["population"]["share_of_census_population_percent"])
        elif p["metric_id"] == "school_density":
            expected = round1(total / meta["municipality_count"])
        elif p["metric_id"] == "student_teacher_ratio":
            expected = external["student_teacher_ratio"]
        elif p["metric_id"] == "waiting_children_count":
            expected = external["waiting_children_count"]
        elif p["metric_id"] == "depopulated_school_ratio":
            assert slug not in KNOWN_EMPTY_MUNICIPALITY_SLUGS, (
                f"{p['prefecture_name']}: municipalityデータが空の県が"
                "depopulated_school_ratioで選出されるべきではありません"
            )
            expected = external["depopulated_school_ratio"]
        elif p["metric_id"] == "ict_teaching_capability":
            expected = external["ict_teaching_capability"]
        else:
            raise AssertionError(f"unknown metric_id: {p['metric_id']}")

        assert math.isclose(expected, p["value"], abs_tol=1e-6), (
            f"{p['prefecture_name']}/{p['metric_id']}: 再計算値({expected}) != 保存値({p['value']})"
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
        f"depopulated_school_ratioがNoneの県が想定と異なります: {none_depopulated}"
    )

    for p in prefectures:
        assert 0 <= p["ict_teaching_capability"] <= 100, (
            f"{p['prefecture_code']}: ICT活用指導力の値が0-100%の範囲外です"
        )
        assert p["student_teacher_ratio"] > 0
        if p["depopulated_school_ratio"] is not None:
            assert 0 <= p["depopulated_school_ratio"] <= 100


def test_card_metadata_education_profile_integration() -> None:
    payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    prefectures = payload["prefectures"]
    assert len(prefectures) == 47

    profile_payload = json.loads(PROFILE_JSON.read_text(encoding="utf-8"))
    profile_by_code = {p["prefecture_code"]: p for p in profile_payload["prefectures"]}

    assert set(p["prefecture_code"] for p in prefectures) == set(profile_by_code), (
        "47都道府県が一致しません（カードメタデータ vs 教育プロフィールデータ）"
    )

    for prefecture in prefectures:
        ep = prefecture["education_profile"]
        source_ref = profile_by_code[prefecture["prefecture_code"]]

        assert ep["available"] is True
        assert ep["tier"] == source_ref["tier"]
        assert ep["metric_id"] == source_ref["metric_id"]
        assert ep["value"] == source_ref["value"]
        assert ep["rank"] == source_ref["rank"]
        assert ep["headline_text"] == source_ref["headline_text"]
        assert ep["source_short_label"] == source_ref["source_short_label"]
        assert ep["reference_date_display"] == source_ref["reference_date_display"]
        assert ep["not_an_official_ranking"] is True


def test_renderer_and_css_wire_profile_line() -> None:
    js = RENDERER_JS.read_text(encoding="utf-8")
    assert "education_profile" in js
    assert "pref-profile-line" in js
    assert "pref-profile-source" in js
    assert "profile.available !== true" in js

    css = CSS_PATH.read_text(encoding="utf-8")
    assert ".pref-profile-line" in css
    assert ".pref-profile-source" in css


def test_portal_html_shows_disclaimer() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "公式のランキング・認定ではありません" in html, (
        "教育プロフィールが公式ランキングではない旨の注記がindex.htmlに見つかりません"
    )


if __name__ == "__main__":
    test_prefecture_education_profile_json()
    test_metric_values_recomputable_from_source()
    test_external_stats_file_integrity()
    test_card_metadata_education_profile_integration()
    test_renderer_and_css_wire_profile_line()
    test_portal_html_shows_disclaimer()
    print("Prefecture education profile (v2) validation passed successfully.")
