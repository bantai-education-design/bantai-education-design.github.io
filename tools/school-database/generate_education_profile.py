#!/usr/bin/env python3
"""Compute the v1 都道府県教育プロフィール（1行タグライン） for all 47 prefectures.

This is NOT an official government ranking. Every tagline is derived purely
from statistics already present in this repository (school-database record
counts already aggregated in prefecture-metadata.json, and the census-based
population share already computed in prefecture-card-metadata.json) — no new
external research is used in this v1 script. See
docs/school-database/education-profile-source-manifest.md for the full
ranking/selection methodology and the "no unsourced official-sounding claims"
policy this project follows (see the abandoned prefecture-emblems approach).

Run twice and diff the output to confirm deterministic generation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFECTURE_METADATA_PATH = ROOT / "data" / "school-database" / "prefecture-metadata.json"
CARD_METADATA_PATH = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
OUTPUT_PATH = ROOT / "data" / "school-database" / "prefecture-education-profile.json"

TIER1_MAX_RANK = 15
FALLBACK_A_MAX_RANK = 23
SCHOOL_DB_SOURCE_LABEL = "全国学校データベース（本サイト収録データの集計）"

METRICS = [
    {
        "id": "private_school_ratio",
        "label": "私立学校の比率",
        "unit": "%",
        "template_tier1": "{name}は私立学校の比率が高く、全国{rank}位です（{value}%）。",
    },
    {
        "id": "special_needs_school_ratio",
        "label": "特別支援学校の設置比率",
        "unit": "%",
        "template_tier1": "{name}は特別支援学校の設置比率が高く、全国{rank}位です（{value}%）。",
    },
    {
        "id": "kindergarten_ratio",
        "label": "幼稚園の比率",
        "unit": "%",
        "template_tier1": "{name}は幼稚園の比率が高く、全国{rank}位です（{value}%）。",
    },
    {
        "id": "child_population_share",
        "label": "学齢人口（3〜17歳）が総人口に占める割合",
        "unit": "%",
        "template_tier1": "{name}は学齢人口（3〜17歳）が総人口に占める割合が高く、全国{rank}位です（{value}%）。",
    },
    {
        "id": "school_density",
        "label": "1市区町村あたりの学校・園数",
        "unit": "校/市区町村",
        "template_tier1": "{name}は1市区町村あたりの学校・園数が多く、全国{rank}位です（{value}校/市区町村）。",
    },
]
METRICS_BY_ID = {m["id"]: m for m in METRICS}
TIER1_CAP = math.ceil(47 / len(METRICS))

FALLBACK_A_TEMPLATE = (
    "{name}は{label}が全国平均を上回っています（{value}{unit}、全国平均{avg}{unit}）。"
)
FALLBACK_B_TEMPLATE = (
    "{name}には{record_count}件の学校・園情報を掲載しています"
    "（{municipality_count}市区町村・{school_type_count}校種）。"
)


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


def compute_metric_value(metric_id: str, meta: dict, card_pref: dict) -> float | None:
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
    raise ValueError(f"unknown metric_id: {metric_id}")


def metric_source(metric_id: str, card_pref: dict) -> tuple[str, str]:
    """Returns (source_short_label, reference_date_display) for a metric."""
    if metric_id == "child_population_share":
        population = card_pref["population"]
        return population["source_short_label"], population["reference_date_display"]
    return SCHOOL_DB_SOURCE_LABEL, "" # filled in by caller with per-prefecture date


def main() -> None:
    prefecture_metadata = json.loads(PREFECTURE_METADATA_PATH.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_PATH.read_text(encoding="utf-8"))
    card_prefectures = card_payload["prefectures"]

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
        for metric in METRICS:
            value = compute_metric_value(metric["id"], meta, card_pref)
            if value is not None:
                values[metric["id"]][slug] = value

    # 2. Rank each metric (1 = most notable / highest value). Ties broken by
    #    canonical prefecture order for full determinism.
    ranks: dict[str, dict[str, int]] = {m["id"]: {} for m in METRICS}
    averages: dict[str, float] = {}
    for metric_id, slug_values in values.items():
        ordered = sorted(
            slug_values.items(),
            key=lambda item: (-item[1], canonical_order[item[0]]),
        )
        for rank, (slug, _value) in enumerate(ordered, start=1):
            ranks[metric_id][slug] = rank
        averages[metric_id] = round1(sum(slug_values.values()) / len(slug_values))

    # 3. Greedy tier1 assignment: most extreme (prefecture, metric) pairs
    #    first, capped per metric so no single metric dominates all 47 cards.
    tier1_candidates = []
    for metric_id, slug_ranks in ranks.items():
        for slug, rank in slug_ranks.items():
            if rank <= TIER1_MAX_RANK:
                tier1_candidates.append((rank, canonical_order[slug], slug, metric_id))
    tier1_candidates.sort()

    assigned: dict[str, dict] = {}
    metric_assigned_count = {m["id"]: 0 for m in METRICS}
    for rank, _order, slug, metric_id in tier1_candidates:
        if slug in assigned:
            continue
        if metric_assigned_count[metric_id] >= TIER1_CAP:
            continue
        assigned[slug] = {"tier": "tier1", "metric_id": metric_id, "rank": rank}
        metric_assigned_count[metric_id] += 1

    # 4. Fallback A (above-median, no explicit rank digit) / Fallback B
    #    (no comparison at all) for prefectures left unassigned.
    for slug in meta_by_slug:
        if slug in assigned:
            continue
        best = None
        for metric_id, slug_ranks in ranks.items():
            rank = slug_ranks.get(slug)
            if rank is None:
                continue
            if best is None or rank < best[0]:
                best = (rank, metric_id)
        if best is not None and best[0] <= FALLBACK_A_MAX_RANK:
            assigned[slug] = {"tier": "fallback_a", "metric_id": best[1], "rank": best[0]}
        else:
            assigned[slug] = {"tier": "fallback_b", "metric_id": None, "rank": None}

    # 5. Render templates.
    prefectures_out = []
    for slug in sorted(meta_by_slug, key=lambda s: canonical_order[s]):
        meta = meta_by_slug[slug]
        card_pref = card_by_slug[slug]
        name = card_pref["prefecture_name"]
        assignment = assigned[slug]
        tier = assignment["tier"]
        metric_id = assignment["metric_id"]

        entry = {
            "prefecture_code": slug,
            "prefecture_name": name,
            "tier": tier,
            "metric_id": metric_id,
        }

        if tier in ("tier1", "fallback_a"):
            metric = METRICS_BY_ID[metric_id]
            value = values[metric_id][slug]
            rank = assignment["rank"]
            source_short_label, source_date = metric_source(metric_id, card_pref)
            if not source_date:
                source_date = f"{most_recent_date(meta['source_dates'])}時点（区分ごとの整理日は各都道府県ページを参照）"
            entry.update({
                "value": value,
                "unit": metric["unit"],
                "rank": rank if tier == "tier1" else None,
                "source_short_label": source_short_label,
                "reference_date_display": source_date,
            })
            if tier == "tier1":
                entry["headline_text"] = metric["template_tier1"].format(
                    name=name, rank=rank, value=value,
                )
            else:
                entry["headline_text"] = FALLBACK_A_TEMPLATE.format(
                    name=name, label=metric["label"], value=value,
                    avg=averages[metric_id], unit=metric["unit"],
                )
        else:
            entry.update({
                "value": None,
                "unit": None,
                "rank": None,
                "source_short_label": SCHOOL_DB_SOURCE_LABEL,
                "reference_date_display": f"{most_recent_date(meta['source_dates'])}時点",
                "headline_text": FALLBACK_B_TEMPLATE.format(
                    name=name,
                    record_count=meta["total"],
                    municipality_count=meta["municipality_count"],
                    school_type_count=card_pref["school_database"]["school_type_count"],
                ),
            })

        entry["available"] = True
        prefectures_out.append(entry)

    payload = {
        "generated_at": "2026-08-02",
        "schema_version": 1,
        "description": "都道府県カード表示用の教育プロフィール（1行タグライン）v1データ。"
                       "既存の学校データベース集計・国勢調査人口比率のみから算出した、"
                       "Ban.Tai Education Design独自の順位付けであり、政府等による公式"
                       "ランキング・認定ではない。",
        "education_profile_policy": {
            "no_dummy_values": True,
            "no_estimates": True,
            "not_an_official_ranking": True,
        },
        "methodology": {
            "tier1_max_rank": TIER1_MAX_RANK,
            "fallback_a_max_rank": FALLBACK_A_MAX_RANK,
            "tier1_cap_per_metric": TIER1_CAP,
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
    print(f"Wrote {OUTPUT_PATH} for {len(covered)} prefectures")

    tier_counts: dict[str, int] = {}
    for p in prefectures_out:
        tier_counts[p["tier"]] = tier_counts.get(p["tier"], 0) + 1
    print(f"Tier distribution: {tier_counts}")
    print(f"Per-metric tier1 assignment counts: {metric_assigned_count}")


if __name__ == "__main__":
    main()
