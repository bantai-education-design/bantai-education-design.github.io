#!/usr/bin/env python3
"""Consolidate the v2 externally-researched official statistics (student-
teacher ratio, waiting children, depopulated-area school ratio, ICT teaching
capability) into data/school-database/prefecture-education-external-stats.json.

Raw research inputs (not committed — see docs/school-database/
education-profile-source-manifest.md for full sourcing/license details of
each):
  - data-source/education-profile-v2/student_teacher_ratio.json
    (文部科学省「学校基本調査」令和7年5月1日, 小学校, e-Stat, PDL/CC BY 4.0 compatible)
  - data-source/education-profile-v2/waiting_children.json
    (こども家庭庁「保育所等関連状況取りまとめ」令和7年4月1日, PDL1.0)
  - data-source/education-profile-v2/ict_capability.json
    (文部科学省「学校における教育の情報化の実態等に関する調査結果」令和7年3月1日, 政府標準利用規約2.0)
  - data-source/education-profile-v2/depopulated_municipalities_raw.json
    (総務省「過疎地域市町村等一覧」令和4年4月1日現在, 885件, 公共データ利用規約1.0版)

The depopulated-area ratio is NOT a directly-published per-prefecture value —
it is computed here by cross-referencing the official municipality list
against this project's own per-prefecture school records
(data/school-database/{slug}.json, `municipality` field), counting what
fraction of each prefecture's schools sit in a designated municipality.
Per the sourcing research, this is reported as "ratio of schools in a
過疎関係市町村" (matching 総務省's own municipality-level counting unit),
not as a claim of literal geographic overlap — some designated
municipalities are only 一部過疎 (a specific pre-merger sub-area), which
this project's per-school data cannot distinguish sub-municipality.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_SOURCE_DIR = ROOT / "data-source" / "education-profile-v2"
CARD_METADATA_PATH = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
SCHOOL_DB_DIR = ROOT / "data" / "school-database"
OUTPUT_PATH = ROOT / "data" / "school-database" / "prefecture-education-external-stats.json"

STUDENT_TEACHER_SOURCE = {
    "source_short_label": "文部科学省「学校基本調査」（小学校）",
    "reference_date_display": "令和7年5月1日現在",
}
WAITING_CHILDREN_SOURCE = {
    "source_short_label": "こども家庭庁「保育所等関連状況取りまとめ」",
    "reference_date_display": "令和7年4月1日現在",
}
DEPOPULATED_SOURCE = {
    "source_short_label": "総務省「過疎地域市町村等一覧」（学校データベース集計と突合）",
    "reference_date_display": "令和4年4月1日現在の指定に基づく",
}
ICT_SOURCE = {
    "source_short_label": "文部科学省「学校における教育の情報化の実態等に関する調査結果」（教員のICT活用指導力）",
    "reference_date_display": "令和7年3月1日現在",
}


def round1(value: float) -> float:
    return round(value, 1)


def build_depopulated_ratios(name_to_slug: dict[str, str]) -> dict[str, float | None]:
    raw_path = DATA_SOURCE_DIR / "depopulated_municipalities_raw.json"
    designated = json.loads(raw_path.read_text(encoding="utf-8"))

    # Designated municipality_name values are "prefecture+city" (e.g.
    # "北海道函館市"); strip the prefecture prefix so they match this
    # project's own school-record `municipality` field (e.g. "函館市"),
    # grouped per prefecture so there is no cross-prefecture ambiguity.
    designated_by_slug: dict[str, set[str]] = {}
    for entry in designated:
        slug = name_to_slug[entry["prefecture_name"]]
        muni_name = entry["municipality_name"]
        assert muni_name.startswith(entry["prefecture_name"]), (
            f"unexpected municipality_name format: {muni_name!r}"
        )
        bare_name = muni_name[len(entry["prefecture_name"]):]
        designated_by_slug.setdefault(slug, set()).add(bare_name)

    ratios: dict[str, float | None] = {}
    for slug in name_to_slug.values():
        school_path = SCHOOL_DB_DIR / f"{slug}.json"
        schools = json.loads(school_path.read_text(encoding="utf-8"))
        if not schools:
            continue
        # A handful of prefectures have an entirely-empty `municipality`
        # field across every school record (a pre-existing data-pipeline
        # issue, tracked separately — see the spawn_task filed against
        # the same `municipality_count == 0` symptom in
        # prefecture-metadata.json). Joining against an empty string would
        # silently produce a false "0% depopulated" for these, which is a
        # data artifact, not a real measurement — exclude them (None)
        # rather than report a fabricated-looking zero.
        if not any(school["municipality"] for school in schools):
            ratios[slug] = None
            continue
        designated_names = designated_by_slug.get(slug, set())
        depopulated_count = sum(
            1 for school in schools
            if any(school["municipality"].startswith(name) for name in designated_names)
        )
        ratios[slug] = round1(depopulated_count / len(schools) * 100)
    return ratios


def main() -> None:
    card_payload = json.loads(CARD_METADATA_PATH.read_text(encoding="utf-8"))
    name_to_slug = {p["prefecture_name"]: p["prefecture_code"] for p in card_payload["prefectures"]}

    student_teacher = json.loads(
        (DATA_SOURCE_DIR / "student_teacher_ratio.json").read_text(encoding="utf-8")
    )
    waiting_children = json.loads(
        (DATA_SOURCE_DIR / "waiting_children.json").read_text(encoding="utf-8")
    )
    ict = json.loads((DATA_SOURCE_DIR / "ict_capability.json").read_text(encoding="utf-8"))
    depopulated_ratios = build_depopulated_ratios(name_to_slug)

    by_slug: dict[str, dict] = {slug: {"prefecture_code": slug} for slug in name_to_slug.values()}

    for entry in student_teacher:
        slug = name_to_slug[entry["prefecture_name"]]
        by_slug[slug]["student_teacher_ratio"] = entry["ratio"]
        by_slug[slug]["student_teacher_ratio_detail"] = {
            "teacher_count": entry["teacher_count"],
            "student_count": entry["student_count"],
        }

    for entry in waiting_children:
        slug = name_to_slug[entry["prefecture_name"]]
        by_slug[slug]["waiting_children_count"] = entry["waiting_children_count"]

    for entry in ict:
        slug = name_to_slug[entry["prefecture_name"]]
        by_slug[slug]["ict_teaching_capability"] = entry["ict_teaching_capability_percent"]

    for slug, ratio in depopulated_ratios.items():
        by_slug[slug]["depopulated_school_ratio"] = ratio

    missing = [
        slug for slug, entry in by_slug.items()
        if not {
            "student_teacher_ratio", "waiting_children_count",
            "depopulated_school_ratio", "ict_teaching_capability",
        } <= entry.keys()
    ]
    if missing:
        raise ValueError(f"incomplete external stats for slugs: {sorted(missing)}")

    prefectures_out = []
    for slug, entry in by_slug.items():
        prefectures_out.append({
            "prefecture_code": slug,
            "student_teacher_ratio": entry["student_teacher_ratio"],
            "student_teacher_ratio_detail": entry["student_teacher_ratio_detail"],
            "student_teacher_ratio_source": STUDENT_TEACHER_SOURCE,
            "waiting_children_count": entry["waiting_children_count"],
            "waiting_children_count_source": WAITING_CHILDREN_SOURCE,
            "depopulated_school_ratio": entry["depopulated_school_ratio"],
            "depopulated_school_ratio_source": DEPOPULATED_SOURCE,
            "ict_teaching_capability": entry["ict_teaching_capability"],
            "ict_teaching_capability_source": ICT_SOURCE,
        })

    payload = {
        "generated_at": "2026-08-02",
        "schema_version": 1,
        "description": "都道府県教育統計v2向けの外部統計（教員一人当たり"
                       "児童生徒数・待機児童数・過疎関係市町村所在校比率・教員のICT"
                       "活用指導力）。過疎関係市町村所在校比率のみ、本サイトの学校"
                       "データベースと総務省の市町村指定リストを突合して算出した"
                       "値であり、他3指標は公表資料の値をそのまま使用している。",
        "sources_policy": {
            "no_dummy_values": True,
            "no_estimates": True,
            "not_an_official_ranking": True,
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


if __name__ == "__main__":
    main()
