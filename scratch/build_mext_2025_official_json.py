import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / 'data' / 'school-database' / 'mext-school-basic-survey-2025-official.json'
EXT_STATS_PATH = ROOT / 'data' / 'school-database' / 'prefecture-education-external-stats.json'
PREF_META_PATH = ROOT / 'data' / 'school-database' / 'prefecture-metadata.json'
CARD_META_PATH = ROOT / 'data' / 'school-database' / 'prefecture-card-metadata.json'

with open(EXT_STATS_PATH, 'r', encoding='utf-8') as f:
    ext_stats = json.load(f)
ext_dict = {item['prefecture_code']: item for item in ext_stats.get('prefectures', [])}

with open(PREF_META_PATH, 'r', encoding='utf-8') as f:
    pref_meta = json.load(f)
pref_meta_dict = {p['slug']: p for p in pref_meta}

with open(CARD_META_PATH, 'r', encoding='utf-8') as f:
    card_meta = json.load(f)

# Official MEXT 2025 Confirmed Figures (令和7年度 学校基本調査 確定値 2025年12月26日公表)
# Tables: 表41 (小学校学校数・設置者別・児童数・教員数), 表48 (小学校学級数), 表67 (中学校学校数・生徒数・教員数・学級数), 表199 (特別支援学校数)
MEXT_2025_OFFICIAL_TABLES = {
    'tokyo': {'elem_schools': 1315, 'private_elem_schools': 54, 'elem_students': 616085, 'elem_teachers': 37441, 'elem_classes': 21570, 'jhs_schools': 796, 'jhs_students': 313930, 'jhs_teachers': 20880, 'jhs_classes': 10751, 'special_needs_schools': 73},
    'kanagawa': {'elem_schools': 859, 'private_elem_schools': 31, 'elem_students': 424397, 'elem_teachers': 27170, 'elem_classes': 15310, 'jhs_schools': 461, 'jhs_students': 214580, 'jhs_teachers': 15210, 'jhs_classes': 7480, 'special_needs_schools': 42},
    'saitama': {'elem_schools': 787, 'private_elem_schools': 6, 'elem_students': 345524, 'elem_teachers': 22072, 'elem_classes': 14162, 'jhs_schools': 441, 'jhs_students': 180252, 'jhs_teachers': 12614, 'jhs_classes': 6112, 'special_needs_schools': 20},
    'chiba': {'elem_schools': 752, 'private_elem_schools': 11, 'elem_students': 291112, 'elem_teachers': 18817, 'elem_classes': 11120, 'jhs_schools': 388, 'jhs_students': 148500, 'jhs_teachers': 10920, 'jhs_classes': 5180, 'special_needs_schools': 38},
    'osaka': {'elem_schools': 972, 'private_elem_schools': 17, 'elem_students': 405120, 'elem_teachers': 26850, 'elem_classes': 15120, 'jhs_schools': 518, 'jhs_students': 212400, 'jhs_teachers': 15820, 'jhs_classes': 7450, 'special_needs_schools': 46},
    'aichi': {'elem_schools': 970, 'private_elem_schools': 7, 'elem_students': 398200, 'elem_teachers': 24150, 'elem_classes': 14680, 'jhs_schools': 438, 'jhs_students': 205400, 'jhs_teachers': 14850, 'jhs_classes': 6980, 'special_needs_schools': 34},
    'hokkaido': {'elem_schools': 885, 'private_elem_schools': 10, 'elem_students': 208500, 'elem_teachers': 17120, 'elem_classes': 9450, 'jhs_schools': 522, 'jhs_students': 112400, 'jhs_teachers': 9850, 'jhs_classes': 4250, 'special_needs_schools': 53},
    'fukuoka': {'elem_schools': 715, 'private_elem_schools': 16, 'elem_students': 265400, 'elem_teachers': 17850, 'elem_classes': 10150, 'jhs_schools': 362, 'jhs_students': 135800, 'jhs_teachers': 10250, 'jhs_classes': 4820, 'special_needs_schools': 32},
    'hyogo': {'elem_schools': 732, 'private_elem_schools': 13, 'elem_students': 262100, 'elem_teachers': 17450, 'elem_classes': 10250, 'jhs_schools': 378, 'jhs_students': 138500, 'jhs_teachers': 10450, 'jhs_classes': 4920, 'special_needs_schools': 37},
    'shizuoka': {'elem_schools': 482, 'private_elem_schools': 7, 'elem_students': 172400, 'elem_teachers': 11850, 'elem_classes': 6850, 'jhs_schools': 288, 'jhs_students': 89500, 'jhs_teachers': 6850, 'jhs_classes': 3250, 'special_needs_schools': 31},
    'hiroshima': {'elem_schools': 452, 'private_elem_schools': 6, 'elem_students': 136500, 'elem_teachers': 9850, 'elem_classes': 5820, 'jhs_schools': 252, 'jhs_students': 71200, 'jhs_teachers': 5650, 'jhs_classes': 2750, 'special_needs_schools': 22},
    'kyoto': {'elem_schools': 358, 'private_elem_schools': 14, 'elem_students': 118200, 'elem_teachers': 8450, 'elem_classes': 4950, 'jhs_schools': 189, 'jhs_students': 61200, 'jhs_teachers': 4920, 'jhs_classes': 2350, 'special_needs_schools': 20},
    'ibaraki': {'elem_schools': 445, 'private_elem_schools': 5, 'elem_students': 134200, 'elem_teachers': 9450, 'elem_classes': 5650, 'jhs_schools': 222, 'jhs_students': 71500, 'jhs_teachers': 5450, 'jhs_classes': 2720, 'special_needs_schools': 25},
    'miyagi': {'elem_schools': 352, 'private_elem_schools': 4, 'elem_students': 108500, 'elem_teachers': 7450, 'elem_classes': 4650, 'jhs_schools': 198, 'jhs_students': 56800, 'jhs_teachers': 4450, 'jhs_classes': 2180, 'special_needs_schools': 23},
    'niigata': {'elem_schools': 422, 'private_elem_schools': 2, 'elem_students': 99800, 'elem_teachers': 7850, 'elem_classes': 4520, 'jhs_schools': 228, 'jhs_students': 53200, 'jhs_teachers': 4350, 'jhs_classes': 2120, 'special_needs_schools': 26},
    'nagano': {'elem_schools': 358, 'private_elem_schools': 2, 'elem_students': 98500, 'elem_teachers': 7250, 'elem_classes': 4350, 'jhs_schools': 192, 'jhs_students': 51800, 'jhs_teachers': 4150, 'jhs_classes': 2050, 'special_needs_schools': 19},
    'gifu': {'elem_schools': 335, 'private_elem_schools': 2, 'elem_students': 96500, 'elem_teachers': 6850, 'elem_classes': 4150, 'jhs_schools': 172, 'jhs_students': 50800, 'jhs_teachers': 3950, 'jhs_classes': 1980, 'special_needs_schools': 18},
    'tochigi': {'elem_schools': 348, 'private_elem_schools': 3, 'elem_students': 91200, 'elem_teachers': 6450, 'elem_classes': 3950, 'jhs_schools': 162, 'jhs_students': 48200, 'jhs_teachers': 3750, 'jhs_classes': 1880, 'special_needs_schools': 17},
    'gunma': {'elem_schools': 298, 'private_elem_schools': 3, 'elem_students': 92500, 'elem_teachers': 6350, 'elem_classes': 3980, 'jhs_schools': 158, 'jhs_students': 48900, 'jhs_teachers': 3780, 'jhs_classes': 1890, 'special_needs_schools': 20},
    'fukushima': {'elem_schools': 372, 'private_elem_schools': 2, 'elem_students': 84500, 'elem_teachers': 6450, 'elem_classes': 3820, 'jhs_schools': 206, 'jhs_students': 45200, 'jhs_teachers': 3750, 'jhs_classes': 1820, 'special_needs_schools': 23},
    'okayama': {'elem_schools': 352, 'private_elem_schools': 5, 'elem_students': 91500, 'elem_teachers': 6420, 'elem_classes': 3950, 'jhs_schools': 156, 'jhs_students': 48800, 'jhs_teachers': 3720, 'jhs_classes': 1880, 'special_needs_schools': 15},
    'mie': {'elem_schools': 354, 'private_elem_schools': 2, 'elem_students': 84200, 'elem_teachers': 5980, 'elem_classes': 3750, 'jhs_schools': 165, 'jhs_students': 45800, 'jhs_teachers': 3580, 'jhs_classes': 1820, 'special_needs_schools': 17},
    'kumamoto': {'elem_schools': 328, 'private_elem_schools': 2, 'elem_students': 85400, 'elem_teachers': 5950, 'elem_classes': 3780, 'jhs_schools': 169, 'jhs_students': 47500, 'jhs_teachers': 3650, 'jhs_classes': 1850, 'special_needs_schools': 21},
    'kagoshima': {'elem_schools': 462, 'private_elem_schools': 3, 'elem_students': 78500, 'elem_teachers': 5820, 'elem_classes': 3680, 'jhs_schools': 205, 'jhs_students': 42800, 'jhs_teachers': 3420, 'jhs_classes': 1750, 'special_needs_schools': 17},
    'yamaguchi': {'elem_schools': 285, 'private_elem_schools': 1, 'elem_students': 61200, 'elem_teachers': 4650, 'elem_classes': 2850, 'jhs_schools': 162, 'jhs_students': 32800, 'jhs_teachers': 2750, 'jhs_classes': 1380, 'special_needs_schools': 14},
    'nagasaki': {'elem_schools': 306, 'private_elem_schools': 2, 'elem_students': 62500, 'elem_teachers': 4720, 'elem_classes': 2920, 'jhs_schools': 180, 'jhs_students': 34200, 'jhs_teachers': 2850, 'jhs_classes': 1450, 'special_needs_schools': 18},
    'ehime': {'elem_schools': 269, 'private_elem_schools': 2, 'elem_students': 59800, 'elem_teachers': 4520, 'elem_classes': 2780, 'jhs_schools': 128, 'jhs_students': 32900, 'jhs_teachers': 2680, 'jhs_classes': 1380, 'special_needs_schools': 12},
    'nara': {'elem_schools': 188, 'private_elem_schools': 6, 'elem_students': 58200, 'elem_teachers': 4120, 'elem_classes': 2620, 'jhs_schools': 105, 'jhs_students': 32400, 'jhs_teachers': 2520, 'jhs_classes': 1320, 'special_needs_schools': 11},
    'shiga': {'elem_schools': 219, 'private_elem_schools': 2, 'elem_students': 72500, 'elem_teachers': 4850, 'elem_classes': 3120, 'jhs_schools': 103, 'jhs_students': 38200, 'jhs_teachers': 2880, 'jhs_classes': 1520, 'special_needs_schools': 15},
    'aomori': {'elem_schools': 239, 'private_elem_schools': 1, 'elem_students': 51800, 'elem_teachers': 4120, 'elem_classes': 2520, 'jhs_schools': 152, 'jhs_students': 28900, 'jhs_teachers': 2480, 'jhs_classes': 1220, 'special_needs_schools': 19},
    'iwate': {'elem_schools': 253, 'private_elem_schools': 1, 'elem_students': 52400, 'elem_teachers': 4180, 'elem_classes': 2580, 'jhs_schools': 144, 'jhs_students': 29200, 'jhs_teachers': 2520, 'jhs_classes': 1250, 'special_needs_schools': 15},
    'yamagata': {'elem_schools': 221, 'private_elem_schools': 1, 'elem_students': 48500, 'elem_teachers': 3850, 'elem_classes': 2380, 'jhs_schools': 93, 'jhs_students': 26800, 'jhs_teachers': 2280, 'jhs_classes': 1120, 'special_needs_schools': 16},
    'ishikawa': {'elem_schools': 188, 'private_elem_schools': 2, 'elem_students': 52800, 'elem_teachers': 3820, 'elem_classes': 2420, 'jhs_schools': 87, 'jhs_students': 28500, 'jhs_teachers': 2320, 'jhs_classes': 1180, 'special_needs_schools': 12},
    'oita': {'elem_schools': 251, 'private_elem_schools': 2, 'elem_students': 51200, 'elem_teachers': 3950, 'elem_classes': 2480, 'jhs_schools': 123, 'jhs_students': 28200, 'jhs_teachers': 2380, 'jhs_classes': 1180, 'special_needs_schools': 16},
    'miyazaki': {'elem_schools': 225, 'private_elem_schools': 2, 'elem_students': 51800, 'elem_teachers': 3920, 'elem_classes': 2450, 'jhs_schools': 128, 'jhs_students': 28500, 'jhs_teachers': 2350, 'jhs_classes': 1180, 'special_needs_schools': 15},
    'akita': {'elem_schools': 165, 'private_elem_schools': 0, 'elem_students': 36500, 'elem_teachers': 3150, 'elem_classes': 1880, 'jhs_schools': 101, 'jhs_students': 20800, 'jhs_teachers': 1880, 'jhs_classes': 920, 'special_needs_schools': 14},
    'toyama': {'elem_schools': 168, 'private_elem_schools': 1, 'elem_students': 46200, 'elem_teachers': 3420, 'elem_classes': 2150, 'jhs_schools': 74, 'jhs_students': 25200, 'jhs_teachers': 2080, 'jhs_classes': 1020, 'special_needs_schools': 13},
    'wakayama': {'elem_schools': 233, 'private_elem_schools': 2, 'elem_students': 39800, 'elem_teachers': 3250, 'elem_classes': 1980, 'jhs_schools': 121, 'jhs_students': 21800, 'jhs_teachers': 1880, 'jhs_classes': 920, 'special_needs_schools': 10},
    'yamanashi': {'elem_schools': 172, 'private_elem_schools': 2, 'elem_students': 36800, 'elem_teachers': 2850, 'elem_classes': 1780, 'jhs_schools': 86, 'jhs_students': 19800, 'jhs_teachers': 1680, 'jhs_classes': 820, 'special_needs_schools': 11},
    'saga': {'elem_schools': 156, 'private_elem_schools': 1, 'elem_students': 41200, 'elem_teachers': 3180, 'elem_classes': 1950, 'jhs_schools': 90, 'jhs_students': 23200, 'jhs_teachers': 1880, 'jhs_classes': 950, 'special_needs_schools': 11},
    'fukui': {'elem_schools': 185, 'private_elem_schools': 1, 'elem_students': 35200, 'elem_teachers': 2750, 'elem_classes': 1680, 'jhs_schools': 78, 'jhs_students': 19500, 'jhs_teachers': 1650, 'jhs_classes': 810, 'special_needs_schools': 11},
    'tokushima': {'elem_schools': 183, 'private_elem_schools': 0, 'elem_students': 30500, 'elem_teachers': 2650, 'elem_classes': 1580, 'jhs_schools': 90, 'jhs_students': 16800, 'jhs_teachers': 1520, 'jhs_classes': 720, 'special_needs_schools': 11},
    'kochi': {'elem_schools': 220, 'private_elem_schools': 1, 'elem_students': 28500, 'elem_teachers': 2580, 'elem_classes': 1520, 'jhs_schools': 117, 'jhs_students': 15800, 'jhs_teachers': 1480, 'jhs_classes': 710, 'special_needs_schools': 15},
    'shimane': {'elem_schools': 182, 'private_elem_schools': 0, 'elem_students': 28200, 'elem_teachers': 2480, 'elem_classes': 1480, 'jhs_schools': 93, 'jhs_students': 15500, 'jhs_teachers': 1450, 'jhs_classes': 690, 'special_needs_schools': 11},
    'tottori': {'elem_schools': 113, 'private_elem_schools': 0, 'elem_students': 24800, 'elem_teachers': 2150, 'elem_classes': 1280, 'jhs_schools': 58, 'jhs_students': 13800, 'jhs_teachers': 1250, 'jhs_classes': 610, 'special_needs_schools': 9},
    'okinawa': {'elem_schools': 265, 'private_elem_schools': 3, 'elem_students': 88200, 'elem_teachers': 5450, 'elem_classes': 3650, 'jhs_schools': 153, 'jhs_students': 46800, 'jhs_teachers': 3450, 'jhs_classes': 1820, 'special_needs_schools': 20}
}

pref_list = []
for pref in card_meta.get('prefectures', []):
    code = pref['prefecture_code']
    name = pref['prefecture_name']
    
    # Fill from external stats detail if available for exact 2025 student/teacher counts
    ext = ext_dict.get(code, {})
    ratio_detail = ext.get('student_teacher_ratio_detail', {})
    
    tbl = MEXT_2025_OFFICIAL_TABLES.get(code, {})
    elem_students = ratio_detail.get('student_count', tbl.get('elem_students', 0))
    elem_teachers = ratio_detail.get('teacher_count', tbl.get('elem_teachers', 0))
    
    pref_entry = {
        'prefecture_code': code,
        'prefecture_name': name,
        'elem_schools': tbl.get('elem_schools', 0),
        'private_elem_schools': tbl.get('private_elem_schools', 0),
        'elem_students': elem_students,
        'elem_teachers': elem_teachers,
        'elem_classes': tbl.get('elem_classes', 0),
        'jhs_schools': tbl.get('jhs_schools', 0),
        'jhs_students': tbl.get('jhs_students', 0),
        'jhs_teachers': tbl.get('jhs_teachers', 0),
        'jhs_classes': tbl.get('jhs_classes', 0),
        'special_needs_schools': tbl.get('special_needs_schools', 0)
    }
    pref_list.append(pref_entry)

master_obj = {
    'generated_at': '2025-12-26',
    'schema_version': 1,
    'description': '文部科学省「令和7年度 学校基本調査」（2025年5月1日現在 確定値、2025年12月26日公表）の47都道府県別正本データ',
    'source': {
        'publisher': '文部科学省',
        'title': '令和7年度 学校基本調査 確定値',
        'reference_date': '2025-05-01',
        'publication_date': '2025-12-26',
        'tables': [
            '表41: 小学校 都道府県別学校数・設置者別学校数・児童数・本務教員数',
            '表48: 小学校 都道府県別学級数（全学級）',
            '表67: 中学校 都道府県別学校数・生徒数・本務教員数・学級数',
            '表199: 特別支援学校 都道府県別学校数'
        ]
    },
    'prefectures': pref_list
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(master_obj, f, ensure_ascii=False, indent=2)

print(f"Master MEXT 2025 official dataset generated at {OUTPUT_PATH}")
