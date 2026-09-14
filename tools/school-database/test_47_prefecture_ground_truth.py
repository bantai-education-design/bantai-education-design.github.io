import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEXT_OFFICIAL_PATH = ROOT / 'data' / 'school-database' / 'mext-school-basic-survey-2025-official.json'
ANALYTICS_PATH = ROOT / 'data' / 'school-database' / 'national-analytics-dataset.json'

def test_47_prefecture_estat_ground_truth_integrity():
    """Verify that mext-school-basic-survey-2025-official.json contains all 47 prefectures with exact confirmed e-Stat 2025 values."""
    assert MEXT_OFFICIAL_PATH.exists(), f"{MEXT_OFFICIAL_PATH} does not exist"
    official_data = json.loads(MEXT_OFFICIAL_PATH.read_text(encoding='utf-8'))
    
    prefs = official_data.get('prefectures', [])
    assert len(prefs) == 47, f"Expected 47 prefectures, got {len(prefs)}"
    
    pref_by_code = {p['prefecture_code']: p for p in prefs}
    
    # 1. Check Tokyo confirmed values
    tokyo = pref_by_code['tokyo']
    assert tokyo['elem_schools'] == 1315
    assert tokyo['elem_students'] == 616084
    assert tokyo['elem_teachers'] == 37441
    assert tokyo['jhs_schools'] == 796
    assert tokyo['jhs_students'] == 313932
    assert tokyo['jhs_teachers'] == 20880
    assert tokyo['special_needs_schools'] == 71
    
    # 2. Check Saitama confirmed values
    saitama = pref_by_code['saitama']
    assert saitama['elem_schools'] == 787
    assert saitama['private_elem_schools'] == 6
    assert saitama['elem_classes'] == 14039
    assert saitama['elem_students'] == 345524
    assert saitama['elem_teachers'] == 22072
    assert saitama['jhs_schools'] == 441
    assert saitama['jhs_classes'] == 5773
    assert saitama['jhs_students'] == 180252
    assert saitama['special_needs_schools'] == 59
    
    # 3. Check Aichi confirmed values
    aichi = pref_by_code['aichi']
    assert aichi['elem_schools'] == 965
    assert aichi['elem_students'] == 382083
    assert aichi['jhs_schools'] == 440
    assert aichi['jhs_students'] == 204811
    
    # 4. Check Osaka confirmed values
    osaka = pref_by_code['osaka']
    assert osaka['elem_schools'] == 977
    assert osaka['jhs_schools'] == 511
    assert osaka['jhs_students'] == 212561
    
    # 5. Check Hokkaido confirmed values
    hokkaido = pref_by_code['hokkaido']
    assert hokkaido['elem_schools'] == 913
    assert hokkaido['elem_students'] == 209620
    assert hokkaido['jhs_schools'] == 548
    assert hokkaido['jhs_students'] == 115120
    
    # 6. Check Okinawa confirmed values
    okinawa = pref_by_code['okinawa']
    assert okinawa['elem_schools'] == 263
    assert okinawa['elem_students'] == 98202
    assert okinawa['jhs_schools'] == 152
    assert okinawa['jhs_students'] == 50463

def test_national_analytics_dataset_sync_with_ground_truth():
    """Verify national-analytics-dataset.json matches official 2025 ground truth for all 47 prefectures."""
    assert ANALYTICS_PATH.exists(), f"{ANALYTICS_PATH} does not exist"
    analytics_data = json.loads(ANALYTICS_PATH.read_text(encoding='utf-8'))
    official_data = json.loads(MEXT_OFFICIAL_PATH.read_text(encoding='utf-8'))
    
    official_by_code = {p['prefecture_code']: p for p in official_data['prefectures']}
    analytics_by_code = {p['code']: p for p in analytics_data['prefectures']}
    
    for code, official in official_by_code.items():
        assert code in analytics_by_code, f"Prefecture {code} missing in analytics dataset"
        analytics = analytics_by_code[code]
        assert analytics['elem_school_count'] == official['elem_schools'], f"{code}: Elem schools mismatch"
        assert analytics['elem_students'] == official['elem_students'], f"{code}: Elem students mismatch"
        assert analytics['jhs_school_count'] == official['jhs_schools'], f"{code}: JHS schools mismatch"

if __name__ == '__main__':
    test_47_prefecture_estat_ground_truth_integrity()
    test_national_analytics_dataset_sync_with_ground_truth()
    print("ALL 47 PREFECTURE E-STAT GROUND TRUTH TESTS PASSED!")
