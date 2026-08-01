import json
import math
import os
import subprocess
import sys
import tempfile
import importlib.util
from pathlib import Path

ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools', 'school-database', 'generate_prefecture_metadata.py'))
spec = importlib.util.spec_from_file_location("generate_prefecture_metadata", file_path)
gm = importlib.util.module_from_spec(spec)
sys.modules["generate_prefecture_metadata"] = gm
spec.loader.exec_module(gm)

POPULATION_JSON = ROOT / "data" / "school-database" / "prefecture-population.json"
CARD_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
PILOT_JSON = ROOT / "data" / "school-database" / "prefecture-population-pilot.json"
POPULATION_SCRIPT = ROOT / "tools" / "school-database" / "generate_prefecture_population_metadata.py"

EXPECTED_GROUP_KEYS = [
    "census_preschool_3_5",
    "census_elementary_6_11",
    "census_junior_high_12_14",
    "census_high_school_15_17",
]


def test_process_prefecture_data():
    fake_data = [
        {"name": "School A", "establishment": "国", "municipality": "City A", "school_type": "小学校"},
        {"school_name": "School B", "establishment_type": "公", "municipality": "City B", "school_type": "中学校"},
        {"name": "School C", "establishment": "私", "municipality": "", "school_type": "高等学校"},
        {"establishment": "公", "municipality": "City A", "school_type": "幼稚園"},
        "bad_row",
        {"name": "School D", "municipality": "City C", "school_type": "特別支援学校"},
    ]

    meta, warnings = gm.process_prefecture_data(fake_data, "test_slug", "Test Prefecture")

    assert meta["total"] == 6, f"Expected 6, got {meta['total']}"
    assert meta["municipality_count"] == 3, f"Expected 3, got {meta['municipality_count']}"
    assert sum(meta["establishment_counts"].values()) == 5, f"Expected 5, got {sum(meta['establishment_counts'].values())}"
    assert len(warnings) > 0, "Should have warnings"
    print("Test passed successfully.")


def test_population_data_structure():
    """47都道府県人口メタデータの整合性を検証する。

    以前はtools/school-database/index.htmlに静的に埋め込まれた47枚の
    カードHTMLを直接パースしていたが、PR #87〜#92でカードはprefecture-
    card-renderer.jsがprefecture-card-metadata.jsonから動的に描画する
    構成へ移行済みのため、その前提は成立しない。本テストはJSON側の
    データ整合性を検証する（HTML構造の検証はtest_school_database_grid_
    layout.pyが担当する）。
    """
    population_payload = json.loads(POPULATION_JSON.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))

    population_prefs = population_payload["prefectures"]
    card_prefs = card_payload["prefectures"]

    assert len(population_prefs) == 47, f"prefecture-population.json: expected 47, got {len(population_prefs)}"
    assert len(card_prefs) == 47, f"prefecture-card-metadata.json: expected 47, got {len(card_prefs)}"

    population_codes = {p["prefecture_code"] for p in population_prefs}
    card_codes = {p["prefecture_code"] for p in card_prefs}
    assert len(population_codes) == 47, "prefecture-population.jsonに重複があります"
    assert len(card_codes) == 47, "prefecture-card-metadata.jsonに重複があります"
    assert population_codes == card_codes, (
        f"都道府県コード集合が一致しません。population差分={population_codes ^ card_codes}"
    )

    reference_dates = {p["reference_date"] for p in population_prefs}
    assert reference_dates == {"2020-10-01"}, f"reference_dateが全県で統一されていません: {reference_dates}"

    scopes = {p["population_scope"] for p in population_prefs}
    assert scopes == {"census_japanese_population"}, f"population_scopeが統一されていません: {scopes}"

    table_ids = {p["source_table_id"] for p in population_prefs}
    assert len(table_ids) == 1, f"source_table_idが統一されていません: {table_ids}"

    population_by_code = {p["prefecture_code"]: p for p in population_prefs}

    for card_pref in card_prefs:
        pop = card_pref["population"]
        assert pop["available"] is True, f"{card_pref['prefecture_name']}: population.available が true ではありません"
        assert pop["census_population"] > 0, f"{card_pref['prefecture_name']}: 人口値が0以下です"
        assert pop["census_age_3_17"] > 0, f"{card_pref['prefecture_name']}: 3〜17歳人口が0以下です"

        group_keys = [g["key"] for g in pop["age_groups"]]
        assert group_keys == EXPECTED_GROUP_KEYS, f"{card_pref['prefecture_name']}: age_groupsのキーが想定と異なります"
        group_sum = sum(g["population"] for g in pop["age_groups"])
        assert group_sum == pop["census_age_3_17"], (
            f"{card_pref['prefecture_name']}: 4区分合計({group_sum}) != 3〜17歳人口({pop['census_age_3_17']})"
        )

        recomputed = round((pop["census_age_3_17"] / pop["census_population"]) * 100, 6)
        assert math.isclose(recomputed, pop["share_of_census_population_percent"], abs_tol=1e-1), (
            f"{card_pref['prefecture_name']}: 割合の再計算が一致しません"
        )

        source_ref = population_by_code[card_pref["prefecture_code"]]
        assert pop["census_population"] == source_ref["census_population"]
        assert pop["census_age_3_17"] == source_ref["census_age_3_17"]

    # 東京都も他都道府県と完全に同一のpopulationキー構造であること
    # （2026年住基パイロットの独自キーが混入していないこと）。
    tokyo = next(p for p in card_prefs if p["prefecture_code"] == "tokyo")
    other = next(p for p in card_prefs if p["prefecture_code"] != "tokyo")
    assert set(tokyo["population"].keys()) == set(other["population"].keys()), (
        "東京都のpopulationキー構造が他都道府県と異なります"
    )
    for legacy_key in ("japanese_population", "japanese_age_3_17", "denominator", "foreign_residents_included"):
        assert legacy_key not in tokyo["population"], (
            f"東京都の本番カードメタデータに旧住基パイロットのキー '{legacy_key}' が混入しています"
        )
    assert tokyo["population"]["reference_date"] == "2020-10-01", (
        "東京都のreference_dateが2020年国勢調査基準になっていません（2026年住基値が混入している可能性）"
    )

    # 2026年住基パイロット値は研究資料として保存されているが、本番カード
    # メタデータの値と一致してはならない（誤って混入していないことの確認）。
    pilot_payload = json.loads(PILOT_JSON.read_text(encoding="utf-8"))
    pilot_tokyo_population = pilot_payload["prefectures"]["tokyo"]["japanese_population"]
    assert tokyo["population"]["census_population"] != pilot_tokyo_population, (
        "東京都のカードメタデータに2026年住基パイロット値が混入しています"
    )

    print("Population data structure tests passed successfully.")


def test_population_generation_script_is_idempotent():
    """生成スクリプトを2回実行しても出力が完全に一致することを確認する。"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out1 = Path(tmp_dir) / "out1.json"
        out2 = Path(tmp_dir) / "out2.json"
        for out_path in (out1, out2):
            subprocess.run(
                [
                    sys.executable,
                    str(POPULATION_SCRIPT),
                    "--output",
                    str(out_path),
                    "--accessed-at",
                    "2026-08-01",
                ],
                check=True,
                cwd=str(ROOT),
                capture_output=True,
            )
        assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8"), (
            "生成スクリプトを2回実行した結果が一致しません（非決定的な出力の可能性）"
        )
    print("Population generation script idempotency test passed successfully.")


if __name__ == "__main__":
    test_process_prefecture_data()
    test_population_data_structure()
    test_population_generation_script_is_idempotent()
    print("All tests in test_generate_metadata.py passed successfully.")
