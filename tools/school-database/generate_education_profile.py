#!/usr/bin/env python3
"""Compute the 都道府県教育統計（客観統計の1行表示） for all 47 prefectures.

This is explicitly NOT a ranking of educational quality and does not display
any ordinal rank ("全国◯位" etc.) or comparative adjectives ("高い/低い/多い
/少ない"). For each prefecture, one statistic (chosen from the 9 metrics
below by how far its value deviates from the 47-prefecture average — a
selection mechanism, never displayed as a rank) is shown as a plain value,
optionally paired with the national average for context, always with its
source, reference date, and statistic name. The "not an educational ranking"
disclaimer is shown once, in a dedicated section on the portal page
(tools/school-database/index.html) rather than repeated on all 47 cards. See
docs/school-database/education-profile-source-manifest.md for full
methodology and policy.

Run twice and diff the output to confirm deterministic generation.
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFECTURE_METADATA_PATH = ROOT / "data" / "school-database" / "prefecture-metadata.json"
CARD_METADATA_PATH = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
EXTERNAL_STATS_PATH = ROOT / "data" / "school-database" / "prefecture-education-external-stats.json"
OUTPUT_PATH = ROOT / "data" / "school-database" / "prefecture-education-profile.json"

CAP_PER_METRIC = math.ceil(47 / 9)
SCHOOL_DB_SOURCE_LABEL = "全国学校データベース（本サイト収録データの集計）"

METRICS = [
    {
        "id": "private_school_ratio",
        "label": "私立学校の比率",
        "unit": "%",
    },
    {
        "id": "special_needs_school_ratio",
        "label": "特別支援学校の設置比率",
        "unit": "%",
    },
    {
        "id": "kindergarten_ratio",
        "label": "幼稚園の比率",
        "unit": "%",
    },
    {
        "id": "child_population_share",
        "label": "学齢人口（3〜17歳）が総人口に占める割合",
        "unit": "%",
    },
    {
        "id": "school_density",
        "label": "1市区町村あたりの学校・園数",
        "unit": "校/市区町村",
    },
    {
        "id": "student_teacher_ratio",
        "label": "教員一人当たりの児童生徒数（小学校）",
        "unit": "人",
    },
    {
        "id": "waiting_children_count",
        "label": "待機児童数",
        "unit": "人",
    },
    {
        "id": "depopulated_school_ratio",
        "label": "過疎関係市町村に所在する学校の比率",
        "unit": "%",
    },
    {
        "id": "ict_teaching_capability",
        "label": "教員のICT活用指導力（教材研究等）",
        "unit": "%",
    },
]
METRICS_BY_ID = {m["id"]: m for m in METRICS}


def round1(value: float) -> float:
    return round(value, 1)


def most_recent_date(source_dates: list[dict]) -> str:
    # A handful of prefectures store a compound "YYYY-MM-DD / YYYY-MM-DD"
    # value in a single scope's date field (a pre-existing characteristic of
    # that source data, not introduced here) — split those apart so the
    # comparison is always between clean single dates.
    all_dates = []
    for entry in source_dates:
        all_dates.extend(part.strip() for part in entry["date"].split("/"))
    return max(all_dates)


def compute_metric_value(
    metric_id: str, meta: dict, card_pref: dict, external: dict | None,
) -> float | None:
    total = meta["total"]
    if total == 0:
        return None
    if metric_id == "private_school_ratio":
        return round1(meta["establishment_counts"]["private"] / total * 100)
    if metric_id == "special_needs_school_ratio":
        return round1(meta["school_type_counts"].get("特別支援学校", 0) / total * 100)
    if metric_id == "kindergarten_ratio":
        return round1(meta["school_type_counts"].get("幼稚園", 0) / total * 100)
    if metric_id == "child_population_share":
        population = card_pref.get("population")
        if not population or population.get("available") is not True:
            return None
        return round1(population["share_of_census_population_percent"])
    if metric_id == "school_density":
        municipality_count = meta["municipality_count"]
        if municipality_count == 0:
            return None
        return round1(total / municipality_count)
    if metric_id in (
        "student_teacher_ratio", "waiting_children_count",
        "depopulated_school_ratio", "ict_teaching_capability",
    ):
        if not external:
            return None
        return external.get(metric_id)
    raise ValueError(f"unknown metric_id: {metric_id}")


def metric_source(
    metric_id: str, card_pref: dict, external: dict | None,
) -> tuple[str, str]:
    """Returns (source_short_label, reference_date_display) for a metric."""
    if metric_id == "child_population_share":
        population = card_pref["population"]
        return population["source_short_label"], population["reference_date_display"]
    if metric_id in (
        "student_teacher_ratio", "waiting_children_count",
        "depopulated_school_ratio", "ict_teaching_capability",
    ):
        source = external[f"{metric_id}_source"]
        return source["source_short_label"], source["reference_date_display"]
    return SCHOOL_DB_SOURCE_LABEL, ""  # filled in by caller with per-prefecture date


def main() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_PATH.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_PATH.read_text(encoding="utf-8"))
    card_prefectures = card_payload["prefectures"]

    external_by_slug: dict[str, dict] = {}
    if EXTERNAL_STATS_PATH.is_file():
        external_payload = json.loads(EXTERNAL_STATS_PATH.read_text(encoding="utf-8"))
        external_by_slug = {p["prefecture_code"]: p for p in external_payload["prefectures"]}

    canonical_order = {p["prefecture_code"]: i for i, p in enumerate(card_prefectures)}
    meta_by_slug = {m["slug"]: m for m in prefecture_metadata}
    card_by_slug = {p["prefecture_code"]: p for p in card_prefectures}

    missing_meta = set(card_by_slug) - set(meta_by_slug)
    if missing_meta:
        raise ValueError(f"prefecture-metadata.json missing slugs: {sorted(missing_meta)}")

    # 1. Compute raw metric values for all 47 prefectures.
    values: dict[str, dict[str, float]] = {m["id"]: {} for m in METRICS}
    for slug, meta in meta_by_slug.items():
        card_pref = card_by_slug[slug]
        external = external_by_slug.get(slug)
        for metric in METRICS:
            value = compute_metric_value(metric["id"], meta, card_pref, external)
            if value is not None:
                values[metric["id"]][slug] = value

    # 2. Compute the average per metric (for neutral "vs. national average"
    #    display only — never used to state "high"/"low"/a rank).
    averages: dict[str, float] = {
        metric_id: round1(sum(slug_values.values()) / len(slug_values))
        for metric_id, slug_values in values.items() if slug_values
    }

    # 3. Selection (internal only, never displayed): for each prefecture,
    #    choose ONE metric to feature by how far its value deviates from the
    #    47-prefecture average, measured in standard deviations (a z-score).
    #    This is purely a "which single statistic is most distinctive for
    #    this prefecture" mechanism — no rank number or "high/low" judgement
    #    is derived from it or shown anywhere in the output. A per-metric cap
    #    keeps any one metric from being featured on too many cards.
    deviation_scores: dict[str, dict[str, float]] = {m["id"]: {} for m in METRICS}
    for metric_id, slug_values in values.items():
        if len(slug_values) < 2:
            continue
        stdev = statistics.pstdev(slug_values.values())
        if stdev == 0:
            continue
        mean = averages[metric_id]
        for slug, value in slug_values.items():
            deviation_scores[metric_id][slug] = abs(value - mean) / stdev

    candidates = []
    for metric_id, slug_scores in deviation_scores.items():
        for slug, score in slug_scores.items():
            candidates.append((-score, canonical_order[slug], slug, metric_id))
    candidates.sort()

    assigned_metric: dict[str, str] = {}
    metric_assigned_count = {m["id"]: 0 for m in METRICS}
    for _neg_score, _order, slug, metric_id in candidates:
        if slug in assigned_metric:
            continue
        if metric_assigned_count[metric_id] >= CAP_PER_METRIC:
            continue
        assigned_metric[slug] = metric_id
        metric_assigned_count[metric_id] += 1

    # Any prefecture left unassigned (e.g. all its deviation scores were
    # exhausted by other prefectures' caps) falls back to whichever metric
    # has a value for it, preferring the one with the largest deviation
    # score even past the cap — every prefecture must show a real statistic.
    for slug in meta_by_slug:
        if slug in assigned_metric:
            continue
        best = None
        for metric_id, slug_scores in deviation_scores.items():
            score = slug_scores.get(slug)
            if score is None:
                continue
            if best is None or score > best[0]:
                best = (score, metric_id)
        if best is None:
            for metric_id, slug_values in values.items():
                if slug in slug_values:
                    best = (0.0, metric_id)
                    break
        assigned_metric[slug] = best[1]

    # 4. Render output: plain value + optional national-average context,
    #    always with source/date/statistic-name and the not-a-ranking note.
    prefectures_out = []
    for slug in sorted(meta_by_slug, key=lambda s: canonical_order[s]):
        meta = meta_by_slug[slug]
        card_pref = card_by_slug[slug]
        external = external_by_slug.get(slug)
        name = card_pref["prefecture_name"]
        metric_id = assigned_metric[slug]
        metric = METRICS_BY_ID[metric_id]
        value = values[metric_id][slug]
        average = averages.get(metric_id)

        source_short_label, source_date = metric_source(metric_id, card_pref, external)
        if not source_date:
            source_date = f"{most_recent_date(meta['source_dates'])}時点（区分ごとの整理日は各都道府県ページを参照）"

        if average is not None:
            headline_text = (
                f"{name}の{metric['label']}は{value}{metric['unit']}です"
                f"（全国平均：{average}{metric['unit']}）。"
            )
        else:
            headline_text = f"{name}の{metric['label']}は{value}{metric['unit']}です。"

        prefectures_out.append({
            "prefecture_code": slug,
            "prefecture_name": name,
            "metric_id": metric_id,
            "metric_label": metric["label"],
            "value": value,
            "unit": metric["unit"],
            "national_average": average,
            "headline_text": headline_text,
            "source_short_label": source_short_label,
            "reference_date_display": source_date,
            "statistic_name": source_short_label,
            "available": True,
        })

    payload = {
        "generated_at": "2026-08-02",
        "schema_version": 3,
        "description": "都道府県カード表示用の教育統計データ。本サイトの学校"
                       "データベース集計・国勢調査人口比率に加え、文部科学省・"
                       "こども家庭庁・総務省の公表統計から算出した、Ban.Tai "
                       "Education Design独自の統計表示であり、政府等による公式"
                       "ランキング・認定ではない。都道府県の教育水準を順位付ける"
                       "ものでもない（順位表示は一切行わない）。",
        "education_profile_policy": {
            "no_dummy_values": True,
            "no_estimates": True,
            "not_an_official_ranking": True,
            "not_an_educational_quality_ranking": True,
            "no_rank_display": True,
        },
        "methodology": {
            "selection_method": "largest_zscore_deviation_from_average_capped_per_metric",
            "cap_per_metric": CAP_PER_METRIC,
            "metrics": [
                {"id": m["id"], "label": m["label"], "unit": m["unit"]} for m in METRICS
            ],
        },
        "prefectures": prefectures_out,
    }

    covered = {p["prefecture_code"] for p in prefectures_out}
    if len(covered) != 47:
        raise ValueError(f"expected 47 prefectures, got {len(covered)}")

    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH} for {len(covered)} prefectures (schema_version=3)")
    print(f"Per-metric assignment counts: {metric_assigned_count}")


if __name__ == "__main__":
    main()
