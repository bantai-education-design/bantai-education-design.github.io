#!/usr/bin/env python3
"""Validate the v1 都道府県教育プロフィール（1行タグライン） data, its
integration into prefecture-card-metadata.json, and its rendering wiring.

This is NOT a test of an official government ranking — every value must be
independently recomputable from data already in this repository (see
generate_education_profile.py and
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
RENDERER_JS = ROOT / "assets" / "js" / "school-database" / "prefecture-card-renderer.js"
CSS_PATH = ROOT / "assets" / "css" / "school-database.css"
INDEX_HTML = ROOT / "tools" / "school-database" / "index.html"

PROHIBITED_TERMS = ("公式ランキング", "認定", "日本一", "都道府県章")


def round1(value: float) -> float:
    return round(value, 1)


def test_prefecture_education_profile_json() -> None:
    payload = json.loads(PROFILE_JSON.read_text(encoding="utf-8"))
    prefectures = payload["prefectures"]
    assert len(prefectures) == 47, f"expected 47 prefectures, got {len(prefectures)}"

    codes = [p["prefecture_code"] for p in prefectures]
    assert len(set(codes)) == 47, "prefecture_code に重複があります"

    assert payload["education_profile_policy"]["no_dummy_values"] is True
    assert payload["education_profile_policy"]["no_estimates"] is True
    assert payload["education_profile_policy"]["not_an_official_ranking"] is True

    metric_ids = {m["id"] for m in payload["methodology"]["metrics"]}
    tier1_max_rank = payload["methodology"]["tier1_max_rank"]
    cap = payload["methodology"]["tier1_cap_per_metric"]

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
        else:
            # フォールバックA/Bでは、順位を断定する表現を含めない
            # （全国平均超という緩やかな表現、または比較なしの説明文のみ）。
            assert not re.search(r"全国\d+位", p["headline_text"]), (
                f"{p['prefecture_name']}: フォールバック文なのに「全国◯位」を含んでいます"
            )

        for prohibited in PROHIBITED_TERMS:
            assert prohibited not in p["headline_text"], (
                f"{p['prefecture_name']}: 見出し文に禁止表現「{prohibited}」が含まれています"
            )

    for metric_id, count in metric_tier1_counts.items():
        assert count <= cap, f"{metric_id}: tier1割当が上限{cap}件を超えています（{count}件）"

    headline_texts = [p["headline_text"] for p in prefectures]
    assert len(set(headline_texts)) > 1, "全県で同一の見出し文になっています"


def test_metric_values_recomputable_from_source() -> None:
    """各指標の値・順位を、生データ（prefecture-metadata.json /
    prefecture-card-metadata.json）から独立に再計算し、一致することを確認する。"""
    profile_payload = json.loads(PROFILE_JSON.read_text(encoding="utf-8"))
    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))

    meta_by_slug = {m["slug"]: m for m in prefecture_metadata}
    card_by_slug = {p["prefecture_code"]: p for p in card_payload["prefectures"]}

    for p in profile_payload["prefectures"]:
        if p["tier"] not in ("tier1", "fallback_a"):
            continue
        slug = p["prefecture_code"]
        meta = meta_by_slug[slug]
        card_pref = card_by_slug[slug]
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
        else:
            raise AssertionError(f"unknown metric_id: {p['metric_id']}")

        assert math.isclose(expected, p["value"], abs_tol=1e-6), (
            f"{p['prefecture_name']}/{p['metric_id']}: 再計算値({expected}) != 保存値({p['value']})"
        )


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
    test_card_metadata_education_profile_integration()
    test_renderer_and_css_wire_profile_line()
    test_portal_html_shows_disclaimer()
    print("Prefecture education profile (v1) validation passed successfully.")
