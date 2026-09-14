import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

MEXT_OFFICIAL_PATH = ROOT / 'data' / 'school-database' / 'mext-school-basic-survey-2025-official.json'
ANALYTICS_PATH = ROOT / 'data' / 'school-database' / 'national-analytics-dataset.json'

from build_perfect_mext_2025_from_estat_tables import build_official_dataset_dict

def test_estat_live_parser_matches_official_json():
    """Verify live e-Stat table download & parse matches committed mext-school-basic-survey-2025-official.json 100% across all 47 prefectures."""
    assert MEXT_OFFICIAL_PATH.exists(), f"{MEXT_OFFICIAL_PATH} does not exist"
    committed_data = json.loads(MEXT_OFFICIAL_PATH.read_text(encoding='utf-8'))
    
    live_dataset = build_official_dataset_dict()
    
    committed_prefs = {p['prefecture_code']: p for p in committed_data.get('prefectures', [])}
    live_prefs = {p['prefecture_code']: p for p in live_dataset.get('prefectures', [])}
    
    assert len(committed_prefs) == 47, f"Committed expected 47 prefectures, got {len(committed_prefs)}"
    assert len(live_prefs) == 47, f"Live expected 47 prefectures, got {len(live_prefs)}"
    
    metrics = [
        'elem_schools', 'private_elem_schools', 'elem_students', 'elem_teachers', 'elem_classes',
        'jhs_schools', 'jhs_students', 'jhs_teachers', 'jhs_classes', 'special_needs_schools'
    ]
    
    for code, live_pref in live_prefs.items():
        assert code in committed_prefs, f"Prefecture {code} missing in committed dataset"
        committed_pref = committed_prefs[code]
        for metric in metrics:
            assert live_pref[metric] == committed_pref[metric], (
                f"Mismatch for prefecture {code} metric {metric}: "
                f"live={live_pref[metric]} vs committed={committed_pref[metric]}"
            )

def test_47_prefecture_ground_truth_sample_values():
    """Verify ground truth values for benchmark prefectures."""
    official_data = json.loads(MEXT_OFFICIAL_PATH.read_text(encoding='utf-8'))
    pref_by_code = {p['prefecture_code']: p for p in official_data.get('prefectures', [])}
    
    # 1. Tokyo
    tokyo = pref_by_code['tokyo']
    assert tokyo['elem_schools'] == 1315
    assert tokyo['private_elem_schools'] == 55
    assert tokyo['elem_students'] == 616084
    assert tokyo['elem_teachers'] == 37441
    assert tokyo['elem_classes'] == 21535
    assert tokyo['jhs_schools'] == 796
    assert tokyo['jhs_students'] == 313932
    assert tokyo['jhs_teachers'] == 20880
    assert tokyo['jhs_classes'] == 7424
    assert tokyo['special_needs_schools'] == 71

    # 2. Saitama
    saitama = pref_by_code['saitama']
    assert saitama['elem_schools'] == 787
    assert saitama['private_elem_schools'] == 6
    assert saitama['elem_classes'] == 14039
    assert saitama['elem_students'] == 345524
    assert saitama['elem_teachers'] == 22072
    assert saitama['jhs_schools'] == 441
    assert saitama['jhs_classes'] == 5773
    assert saitama['jhs_students'] == 180252
    assert saitama['jhs_teachers'] == 12614
    assert saitama['special_needs_schools'] == 59

    # 3. Aichi
    aichi = pref_by_code['aichi']
    assert aichi['elem_schools'] == 965
    assert aichi['elem_students'] == 382083
    assert aichi['elem_teachers'] == 25957
    assert aichi['elem_classes'] == 16842
    assert aichi['jhs_schools'] == 440
    assert aichi['jhs_students'] == 204811
    assert aichi['jhs_teachers'] == 14564
    assert aichi['jhs_classes'] == 6876
    assert aichi['special_needs_schools'] == 44

    # 4. Osaka
    osaka = pref_by_code['osaka']
    assert osaka['elem_schools'] == 977
    assert osaka['elem_students'] == 396445
    assert osaka['elem_teachers'] == 29510
    assert osaka['elem_classes'] == 18484
    assert osaka['jhs_schools'] == 511
    assert osaka['jhs_students'] == 212561
    assert osaka['jhs_teachers'] == 17353
    assert osaka['jhs_classes'] == 7331
    assert osaka['special_needs_schools'] == 51

    # 5. Hokkaido
    hokkaido = pref_by_code['hokkaido']
    assert hokkaido['elem_schools'] == 913
    assert hokkaido['elem_students'] == 209620
    assert hokkaido['jhs_schools'] == 548
    assert hokkaido['jhs_students'] == 115120

    # 6. Okinawa
    okinawa = pref_by_code['okinawa']
    assert okinawa['elem_schools'] == 263
    assert okinawa['elem_students'] == 98202
    assert okinawa['jhs_schools'] == 152
    assert okinawa['jhs_students'] == 50463

def test_national_analytics_dataset_sync_with_ground_truth():
    """Verify national-analytics-dataset.json matches official 2025 ground truth for all 47 prefectures and all metrics."""
    assert ANALYTICS_PATH.exists(), f"{ANALYTICS_PATH} does not exist"
    analytics_data = json.loads(ANALYTICS_PATH.read_text(encoding='utf-8'))
    official_data = json.loads(MEXT_OFFICIAL_PATH.read_text(encoding='utf-8'))
    
    official_by_code = {p['prefecture_code']: p for p in official_data['prefectures']}
    analytics_by_code = {p['code']: p for p in analytics_data['prefectures']}
    
    assert len(analytics_by_code) == 47, f"Expected 47 prefectures in analytics dataset, got {len(analytics_by_code)}"
    
    for code, official in official_by_code.items():
        assert code in analytics_by_code, f"Prefecture {code} missing in analytics dataset"
        analytics = analytics_by_code[code]
        
        # Primary metrics
        assert analytics['elem_school_count'] == official['elem_schools'], f"{code}: elem_school_count mismatch"
        assert analytics['elem_students'] == official['elem_students'], f"{code}: elem_students mismatch"
        assert analytics['elem_teachers'] == official['elem_teachers'], f"{code}: elem_teachers mismatch"
        assert analytics['jhs_school_count'] == official['jhs_schools'], f"{code}: jhs_school_count mismatch"
        assert analytics['jhs_students'] == official['jhs_students'], f"{code}: jhs_students mismatch"
        
        # Derived metrics verification
        expected_elem_enrolled_per_school = round(official['elem_students'] / official['elem_schools'], 1)
        assert analytics['elem_enrolled_per_school'] == expected_elem_enrolled_per_school, f"{code}: elem_enrolled_per_school mismatch"
        
        expected_elem_enrolled_per_class = round(official['elem_students'] / official['elem_classes'], 1)
        assert analytics['elem_enrolled_per_class'] == expected_elem_enrolled_per_class, f"{code}: elem_enrolled_per_class mismatch"
        
        expected_student_teacher_ratio = round(official['elem_students'] / official['elem_teachers'], 2)
        assert analytics['student_teacher_ratio'] == expected_student_teacher_ratio, f"{code}: student_teacher_ratio mismatch"
        
        expected_jhs_enrolled_per_school = round(official['jhs_students'] / official['jhs_schools'], 1)
        assert analytics['jhs_enrolled_per_school'] == expected_jhs_enrolled_per_school, f"{code}: jhs_enrolled_per_school mismatch"
        
        expected_jhs_enrolled_per_class = round(official['jhs_students'] / official['jhs_classes'], 1)
        assert analytics['jhs_enrolled_per_class'] == expected_jhs_enrolled_per_class, f"{code}: jhs_enrolled_per_class mismatch"
        
        expected_jhs_student_teacher_ratio = round(official['jhs_students'] / official['jhs_teachers'], 1)
        assert analytics['jhs_student_teacher_ratio'] == expected_jhs_student_teacher_ratio, f"{code}: jhs_student_teacher_ratio mismatch"

        expected_private_elem_ratio = round(official['private_elem_schools'] / official['elem_schools'] * 100, 1)
        assert analytics['private_elem_school_ratio'] == expected_private_elem_ratio, f"{code}: private_elem_school_ratio mismatch"

    # National summary totals check
    nat = analytics_data.get('national_summary', {})
    total_official_elem_schools = sum(p['elem_schools'] for p in official_data['prefectures'])
    total_official_elem_students = sum(p['elem_students'] for p in official_data['prefectures'])
    total_official_elem_teachers = sum(p['elem_teachers'] for p in official_data['prefectures'])
    total_official_jhs_schools = sum(p['jhs_schools'] for p in official_data['prefectures'])
    total_official_jhs_students = sum(p['jhs_students'] for p in official_data['prefectures'])
    total_official_jhs_teachers = sum(p['jhs_teachers'] for p in official_data['prefectures'])

    assert nat['elem_school_count'] == total_official_elem_schools
    assert nat['elem_students'] == total_official_elem_students
    assert nat['elem_teachers'] == total_official_elem_teachers
    assert nat['jhs_school_count'] == total_official_jhs_schools
    assert nat['jhs_students'] == total_official_jhs_students
    assert nat['jhs_teachers'] == total_official_jhs_teachers

if __name__ == '__main__':
    test_estat_live_parser_matches_official_json()
    test_47_prefecture_ground_truth_sample_values()
    test_national_analytics_dataset_sync_with_ground_truth()
    print("ALL 47 PREFECTURE E-STAT GROUND TRUTH TESTS PASSED SUCCESSFULLY!")
