import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_META_PATH = ROOT / 'data' / 'school-database' / 'prefecture-card-metadata.json'
PREF_META_PATH = ROOT / 'data' / 'school-database' / 'prefecture-metadata.json'
EXT_STATS_PATH = ROOT / 'data' / 'school-database' / 'prefecture-education-external-stats.json'
MEXT_2025_PATH = ROOT / 'data' / 'school-database' / 'mext-school-basic-survey-2025-official.json'
OUTPUT_PATH = ROOT / 'data' / 'school-database' / 'national-analytics-dataset.json'

# Official 2020 Census confirmed total population and 65+ population (年齢不詳補完結果)
CENSUS_2020_OFFICIAL = {
    '01': {'name': '北海道', 'total_pop': 5224614, 'elderly_65_plus': 1664570},
    '02': {'name': '青森県', 'total_pop': 1237984, 'elderly_65_plus': 410233},
    '03': {'name': '岩手県', 'total_pop': 1210534, 'elderly_65_plus': 412019},
    '04': {'name': '宮城県', 'total_pop': 2301996, 'elderly_65_plus': 641353},
    '05': {'name': '秋田県', 'total_pop': 959502, 'elderly_65_plus': 359687},
    '06': {'name': '山形県', 'total_pop': 1068027, 'elderly_65_plus': 354846},
    '07': {'name': '福島県', 'total_pop': 1833152, 'elderly_65_plus': 598348},
    '08': {'name': '茨城県', 'total_pop': 2867009, 'elderly_65_plus': 839267},
    '09': {'name': '栃木県', 'total_pop': 1933146, 'elderly_65_plus': 560942},
    '10': {'name': '群馬県', 'total_pop': 1939110, 'elderly_65_plus': 579796},
    '11': {'name': '埼玉県', 'total_pop': 7344765, 'elderly_65_plus': 1986516},
    '12': {'name': '千葉県', 'total_pop': 6284480, 'elderly_65_plus': 1745567},
    '13': {'name': '東京都', 'total_pop': 14047594, 'elderly_65_plus': 3178054},
    '14': {'name': '神奈川県', 'total_pop': 9237337, 'elderly_65_plus': 2374272},
    '15': {'name': '新潟県', 'total_pop': 2201272, 'elderly_65_plus': 730957},
    '16': {'name': '富山県', 'total_pop': 1034814, 'elderly_65_plus': 338409},
    '17': {'name': '石川県', 'total_pop': 1132526, 'elderly_65_plus': 339237},
    '18': {'name': '福井県', 'total_pop': 766863, 'elderly_65_plus': 237211},
    '19': {'name': '山梨県', 'total_pop': 809974, 'elderly_65_plus': 251807},
    '20': {'name': '長野県', 'total_pop': 2048011, 'elderly_65_plus': 649850},
    '21': {'name': '岐阜県', 'total_pop': 1978742, 'elderly_65_plus': 612476},
    '22': {'name': '静岡県', 'total_pop': 3633202, 'elderly_65_plus': 1093892},
    '23': {'name': '愛知県', 'total_pop': 7542415, 'elderly_65_plus': 1894008},
    '24': {'name': '三重県', 'total_pop': 1770254, 'elderly_65_plus': 548272},
    '25': {'name': '滋賀県', 'total_pop': 1413610, 'elderly_65_plus': 373636},
    '26': {'name': '京都府', 'total_pop': 2578087, 'elderly_65_plus': 757987},
    '27': {'name': '大阪府', 'total_pop': 8837685, 'elderly_65_plus': 2444986},
    '28': {'name': '兵庫県', 'total_pop': 5465002, 'elderly_65_plus': 1577419},
    '29': {'name': '奈良県', 'total_pop': 1324473, 'elderly_65_plus': 422969},
    '30': {'name': '和歌山県', 'total_pop': 922584, 'elderly_65_plus': 319657},
    '31': {'name': '鳥取県', 'total_pop': 553407, 'elderly_65_plus': 180637},
    '32': {'name': '島根県', 'total_pop': 671126, 'elderly_65_plus': 232836},
    '33': {'name': '岡山県', 'total_pop': 1888432, 'elderly_65_plus': 573153},
    '34': {'name': '広島県', 'total_pop': 2799702, 'elderly_65_plus': 819742},
    '35': {'name': '山口県', 'total_pop': 1342059, 'elderly_65_plus': 463556},
    '36': {'name': '徳島県', 'total_pop': 719559, 'elderly_65_plus': 245630},
    '37': {'name': '香川県', 'total_pop': 950244, 'elderly_65_plus': 301313},
    '38': {'name': '愛媛県', 'total_pop': 1334841, 'elderly_65_plus': 444528},
    '39': {'name': '高知県', 'total_pop': 691527, 'elderly_65_plus': 246810},
    '40': {'name': '福岡県', 'total_pop': 5135214, 'elderly_65_plus': 1414142},
    '41': {'name': '佐賀県', 'total_pop': 811442, 'elderly_65_plus': 247064},
    '42': {'name': '長崎県', 'total_pop': 1312317, 'elderly_65_plus': 437341},
    '43': {'name': '熊本県', 'total_pop': 1738301, 'elderly_65_plus': 548228},
    '44': {'name': '大分県', 'total_pop': 1123852, 'elderly_65_plus': 375348},
    '45': {'name': '宮崎県', 'total_pop': 1069576, 'elderly_65_plus': 349634},
    '46': {'name': '鹿児島県', 'total_pop': 1588256, 'elderly_65_plus': 514642},
    '47': {'name': '沖縄県', 'total_pop': 1467480, 'elderly_65_plus': 330683}
}

OFFICIAL_DEMOGRAPHICS_CENSUS = {
    '01': {'pop_under_15': 555804, 'pop_2015': 5381733},
    '02': {'pop_under_15': 129112, 'pop_2015': 1308265},
    '03': {'pop_under_15': 132447, 'pop_2015': 1279594},
    '04': {'pop_under_15': 268428, 'pop_2015': 2333899},
    '05': {'pop_under_15': 92673, 'pop_2015': 1023119},
    '06': {'pop_under_15': 120086, 'pop_2015': 1123891},
    '07': {'pop_under_15': 206152, 'pop_2015': 1914039},
    '08': {'pop_under_15': 333741, 'pop_2015': 2916976},
    '09': {'pop_under_15': 227553, 'pop_2015': 1974255},
    '10': {'pop_under_15': 224304, 'pop_2015': 1973115},
    '11': {'pop_under_15': 858384, 'pop_2015': 7266534},
    '12': {'pop_under_15': 734496, 'pop_2015': 6222666},
    '13': {'pop_under_15': 1566840, 'pop_2015': 13515271},
    '14': {'pop_under_15': 1085763, 'pop_2015': 9126214},
    '15': {'pop_under_15': 247480, 'pop_2015': 2304264},
    '16': {'pop_under_15': 115177, 'pop_2015': 1066328},
    '17': {'pop_under_15': 137096, 'pop_2015': 1154008},
    '18': {'pop_under_15': 95544, 'pop_2015': 786740},
    '19': {'pop_under_15': 91629, 'pop_2015': 834930},
    '20': {'pop_under_15': 242873, 'pop_2015': 2098804},
    '21': {'pop_under_15': 240520, 'pop_2015': 2031903},
    '22': {'pop_under_15': 438723, 'pop_2015': 3700305},
    '23': {'pop_under_15': 973642, 'pop_2015': 7483128},
    '24': {'pop_under_15': 211090, 'pop_2015': 1815865},
    '25': {'pop_under_15': 191369, 'pop_2015': 1412916},
    '26': {'pop_under_15': 293465, 'pop_2015': 2610353},
    '27': {'pop_under_15': 1029499, 'pop_2015': 8839469},
    '28': {'pop_under_15': 660205, 'pop_2015': 5534800},
    '29': {'pop_under_15': 154271, 'pop_2015': 1364316},
    '30': {'pop_under_15': 105360, 'pop_2015': 963579},
    '31': {'pop_under_15': 68330, 'pop_2015': 573441},
    '32': {'pop_under_15': 81641, 'pop_2015': 694352},
    '33': {'pop_under_15': 229352, 'pop_2015': 1921525},
    '34': {'pop_under_15': 352678, 'pop_2015': 2843990},
    '35': {'pop_under_15': 153608, 'pop_2015': 1404729},
    '36': {'pop_under_15': 77129, 'pop_2015': 755733},
    '37': {'pop_under_15': 113757, 'pop_2015': 976263},
    '38': {'pop_under_15': 153764, 'pop_2015': 1385262},
    '39': {'pop_under_15': 74946, 'pop_2015': 728276},
    '40': {'pop_under_15': 662179, 'pop_2015': 5101556},
    '41': {'pop_under_15': 108241, 'pop_2015': 832832},
    '42': {'pop_under_15': 164303, 'pop_2015': 1377187},
    '43': {'pop_under_15': 228366, 'pop_2015': 1786170},
    '44': {'pop_under_15': 135272, 'pop_2015': 1166338},
    '45': {'pop_under_15': 139773, 'pop_2015': 1104069},
    '46': {'pop_under_15': 205381, 'pop_2015': 1648177},
    '47': {'pop_under_15': 243246, 'pop_2015': 1433566}
}

def build_dataset():
    with open(CARD_META_PATH, 'r', encoding='utf-8') as f:
        card_meta = json.load(f)
        
    with open(PREF_META_PATH, 'r', encoding='utf-8') as f:
        pref_meta = json.load(f)
    pref_meta_dict = {p['slug']: p for p in pref_meta}
        
    with open(EXT_STATS_PATH, 'r', encoding='utf-8') as f:
        ext_stats = json.load(f)
    ext_dict = {item['prefecture_code']: item for item in ext_stats.get('prefectures', [])}
    
    with open(MEXT_2025_PATH, 'r', encoding='utf-8') as f:
        mext_master = json.load(f)
    mext_dict = {item['prefecture_code']: item for item in mext_master.get('prefectures', [])}
    
    dataset = []
    
    for pref in card_meta.get('prefectures', []):
        code = pref['prefecture_code']
        name = pref['prefecture_name']
        region = pref.get('region', {}).get('name', '')
        
        pref_num = pref.get('silhouette', {}).get('src', '').split('/')[-1].split('-')[0]
        if not pref_num.isdigit():
            code_map = {'hokkaido': '01', 'tokyo': '13', 'kanagawa': '14', 'osaka': '27', 'okinawa': '47'}
            pref_num = code_map.get(code, '01')
            
        census_data = CENSUS_2020_OFFICIAL.get(pref_num, {})
        demo_data = OFFICIAL_DEMOGRAPHICS_CENSUS.get(pref_num, {})
        mext_data = mext_dict.get(code, {})
        pmeta = pref_meta_dict.get(code, {})
        
        total_pop = census_data.get('total_pop', pref.get('population', {}).get('census_population', 0))
        elderly_pop = census_data.get('elderly_65_plus', 0)
        pop_under_15 = demo_data.get('pop_under_15', 0)
        pop_2015 = demo_data.get('pop_2015', total_pop)
        
        school_db = pref.get('school_database', {})
        total_schools = school_db.get('record_count', pmeta.get('total', 0))
        
        # MEXT 2025 Official Table Values
        mext_elem_schools = mext_data.get('elem_schools', 0)
        private_elem_count = mext_data.get('private_elem_schools', 0)
        elem_students = mext_data.get('elem_students', 0)
        elem_teachers = mext_data.get('elem_teachers', 0)
        elem_classes = mext_data.get('elem_classes', 0)
        
        mext_jhs_schools = mext_data.get('jhs_schools', 0)
        jhs_students = mext_data.get('jhs_students', 0)
        jhs_teachers = mext_data.get('jhs_teachers', 0)
        jhs_classes = mext_data.get('jhs_classes', 0)
        
        special_needs_school_count = mext_data.get('special_needs_schools', 0)
        
        # DB school count for pop ratio & summary card compatibility
        pref_school_json = ROOT / 'data' / 'school-database' / f'{code}.json'
        elem_count_db = 0
        jhs_count_db = 0
        hs_count_db = 0
        if pref_school_json.exists():
            with open(pref_school_json, 'r', encoding='utf-8') as sf:
                schools = json.load(sf)
                for s in schools:
                    stype = s.get('school_type', '')
                    if '小学校' in stype and '特別支援' not in stype:
                        elem_count_db += 1
                    elif '中学校' in stype and '特別支援' not in stype:
                        jhs_count_db += 1
                    elif '高等学校' in stype or '高校' in stype:
                        hs_count_db += 1
                        
        pop = pref.get('population', {})
        elem_pop = 0
        jhs_pop = 0
        hs_pop = 0
        preschool_pop = 0
        
        for ag in pop.get('age_groups', []):
            if ag.get('key') == 'census_elementary_6_11':
                elem_pop = ag.get('population', 0)
            elif ag.get('key') == 'census_junior_high_12_14':
                jhs_pop = ag.get('population', 0)
            elif ag.get('key') == 'census_high_school_15_17':
                hs_pop = ag.get('population', 0)
            elif ag.get('key') == 'census_preschool_3_5':
                preschool_pop = ag.get('population', 0)
                
        ext = ext_dict.get(code, {})
        student_teacher_ratio = round(elem_students / elem_teachers, 2) if elem_teachers > 0 else 0
        ict_capability = ext.get('ict_teaching_capability', 0.0)
        waiting_children = ext.get('waiting_children_count', 0)
        
        # 6-17 School age population for special needs school ratio per 100k
        school_age_pop_6_17 = elem_pop + jhs_pop + hs_pop
        
        # Raw float precision for sorting
        aging_rate_raw = (elderly_pop / total_pop * 100) if total_pop > 0 else 0.0
        elem_pop_per_school_raw = (elem_pop / mext_elem_schools) if mext_elem_schools > 0 else 0.0
        jhs_pop_per_school_raw = (jhs_pop / mext_jhs_schools) if mext_jhs_schools > 0 else 0.0
        student_teacher_ratio_raw = (elem_students / elem_teachers) if elem_teachers > 0 else 0.0
        
        # Strict MEXT 2025 aligned school counts
        elem_enrolled_per_school_raw = (elem_students / mext_elem_schools) if mext_elem_schools > 0 else 0.0
        elem_enrolled_per_class_raw = (elem_students / elem_classes) if elem_classes > 0 else 0.0
        jhs_enrolled_per_school_raw = (jhs_students / mext_jhs_schools) if mext_jhs_schools > 0 else 0.0
        jhs_enrolled_per_class_raw = (jhs_students / jhs_classes) if jhs_classes > 0 else 0.0
        jhs_student_teacher_ratio_raw = (jhs_students / jhs_teachers) if jhs_teachers > 0 else 0.0
        
        child_under_15_ratio_raw = (pop_under_15 / total_pop * 100) if total_pop > 0 else 0.0
        pop_change_rate_raw = ((total_pop - pop_2015) / pop_2015 * 100) if pop_2015 > 0 else 0.0
        
        private_elem_school_ratio_raw = (private_elem_count / mext_elem_schools * 100) if mext_elem_schools > 0 else 0.0
        special_needs_schools_per_100k_age_6_17_raw = (special_needs_school_count / school_age_pop_6_17 * 100000) if school_age_pop_6_17 > 0 else 0.0
        ict_teaching_capability_raw = float(ict_capability)
        waiting_children_per_10k_preschool_raw = (waiting_children / preschool_pop * 10000) if preschool_pop > 0 else 0.0
        
        entry = {
            'code': code,
            'pref_number': pref_num,
            'name': name,
            'region': region,
            'total_population': total_pop,
            'elem_age_6_11': elem_pop,
            'jhs_age_12_14': jhs_pop,
            'hs_age_15_17': hs_pop,
            'elderly_65_plus': elderly_pop,
            'aging_rate': round(aging_rate_raw, 1),
            'total_school_count': total_schools,
            'elem_school_count': mext_elem_schools,
            'private_elem_schools': private_elem_count,
            'elem_students': elem_students,
            'elem_teachers': elem_teachers,
            'elem_classes': elem_classes,
            'jhs_school_count': mext_jhs_schools,
            'jhs_students': jhs_students,
            'jhs_teachers': jhs_teachers,
            'jhs_classes': jhs_classes,
            'special_needs_schools': special_needs_school_count,
            'hs_school_count': hs_count_db,
            'student_teacher_ratio': student_teacher_ratio,
            'elem_pop_per_school': round(elem_pop_per_school_raw, 1),
            'jhs_pop_per_school': round(jhs_pop_per_school_raw, 1),
            
            # Refined 24 Indicators
            'elem_enrolled_per_school': round(elem_enrolled_per_school_raw, 1),
            'elem_enrolled_per_class': round(elem_enrolled_per_class_raw, 1),
            'jhs_enrolled_per_school': round(jhs_enrolled_per_school_raw, 1),
            'jhs_enrolled_per_class': round(jhs_enrolled_per_class_raw, 1),
            'jhs_student_teacher_ratio': round(jhs_student_teacher_ratio_raw, 1),
            'child_under_15_ratio': round(child_under_15_ratio_raw, 1),
            'pop_change_rate': round(pop_change_rate_raw, 1),
            'private_elem_school_ratio': round(private_elem_school_ratio_raw, 1),
            'special_needs_schools_per_100k_age_6_17': round(special_needs_schools_per_100k_age_6_17_raw, 1),
            'ict_teaching_capability': round(ict_teaching_capability_raw, 1),
            'waiting_children_per_10k_preschool': round(waiting_children_per_10k_preschool_raw, 1),
            
            '_raw': {
                'total_population': total_pop,
                'elem_age_6_11': elem_pop,
                'jhs_age_12_14': jhs_pop,
                'elderly_65_plus': elderly_pop,
                'aging_rate': aging_rate_raw,
                'total_school_count': total_schools,
                'elem_school_count': mext_elem_schools,
                'jhs_school_count': mext_jhs_schools,
                'elem_students': elem_students,
                'elem_teachers': elem_teachers,
                'student_teacher_ratio': student_teacher_ratio_raw,
                'elem_pop_per_school': elem_pop_per_school_raw,
                'jhs_pop_per_school': jhs_pop_per_school_raw,
                'elem_enrolled_per_school': elem_enrolled_per_school_raw,
                'elem_enrolled_per_class': elem_enrolled_per_class_raw,
                'jhs_enrolled_per_school': jhs_enrolled_per_school_raw,
                'jhs_enrolled_per_class': jhs_enrolled_per_class_raw,
                'jhs_student_teacher_ratio': jhs_student_teacher_ratio_raw,
                'child_under_15_ratio': child_under_15_ratio_raw,
                'pop_change_rate': pop_change_rate_raw,
                'private_elem_school_ratio': private_elem_school_ratio_raw,
                'special_needs_schools_per_100k_age_6_17': special_needs_schools_per_100k_age_6_17_raw,
                'ict_teaching_capability': ict_teaching_capability_raw,
                'waiting_children_per_10k_preschool': waiting_children_per_10k_preschool_raw
            }
        }
        dataset.append(entry)
        
    indicators = [
        'total_population', 'elem_age_6_11', 'jhs_age_12_14', 'elderly_65_plus',
        'aging_rate', 'total_school_count', 'elem_school_count', 'jhs_school_count',
        'elem_students', 'elem_teachers', 'student_teacher_ratio',
        'elem_pop_per_school', 'jhs_pop_per_school',
        'elem_enrolled_per_school', 'elem_enrolled_per_class',
        'jhs_enrolled_per_school', 'jhs_enrolled_per_class',
        'jhs_student_teacher_ratio', 'child_under_15_ratio', 'pop_change_rate',
        'private_elem_school_ratio', 'special_needs_schools_per_100k_age_6_17',
        'ict_teaching_capability', 'waiting_children_per_10k_preschool'
    ]
    
    ranks = {ind: {} for ind in indicators}
    for ind in indicators:
        sorted_list = sorted(dataset, key=lambda x: x['_raw'][ind], reverse=True)
        for r_idx, item in enumerate(sorted_list):
            ranks[ind][item['code']] = r_idx + 1
            
    for item in dataset:
        item['ranks'] = {ind: ranks[ind][item['code']] for ind in indicators}
        del item['_raw']
        
    nat_total_pop = sum(d['total_population'] for d in dataset)
    nat_elem_pop = sum(d['elem_age_6_11'] for d in dataset)
    nat_jhs_pop = sum(d['jhs_age_12_14'] for d in dataset)
    nat_elderly_pop = 36026632
    nat_under_15_pop = 15031608
    nat_pop_2015 = 127094745
    
    nat_total_schools = sum(d['total_school_count'] for d in dataset)
    nat_elem_schools = sum(d['elem_school_count'] for d in dataset)
    nat_jhs_schools = sum(d['jhs_school_count'] for d in dataset)
    nat_elem_students = sum(d['elem_students'] for d in dataset)
    nat_elem_teachers = sum(d['elem_teachers'] for d in dataset)
    
    nat_elem_classes = sum(p['elem_classes'] for p in mext_master['prefectures'])
    nat_jhs_students = sum(p['jhs_students'] for p in mext_master['prefectures'])
    nat_jhs_teachers = sum(p['jhs_teachers'] for p in mext_master['prefectures'])
    nat_jhs_classes = sum(p['jhs_classes'] for p in mext_master['prefectures'])
    
    nat_private_elem_schools = sum(p['private_elem_schools'] for p in mext_master['prefectures'])
    nat_special_needs_schools = sum(p['special_needs_schools'] for p in mext_master['prefectures'])
    nat_school_age_6_17_pop = sum(d['elem_age_6_11'] + d['jhs_age_12_14'] + d['hs_age_15_17'] for d in dataset)
    nat_waiting_children = sum(ext_dict[p['prefecture_code']].get('waiting_children_count', 0) for p in card_meta['prefectures'])
    nat_preschool_pop = sum(next(ag['population'] for ag in p['population']['age_groups'] if ag['key'] == 'census_preschool_3_5') for p in card_meta['prefectures'])
    
    official_national_pop = 126146099
    
    national_summary = {
        'total_population': official_national_pop,
        'elem_age_6_11': nat_elem_pop,
        'jhs_age_12_14': nat_jhs_pop,
        'elderly_65_plus': nat_elderly_pop,
        'aging_rate': round(nat_elderly_pop / official_national_pop * 100, 1),
        'total_school_count': nat_total_schools,
        'elem_school_count': nat_elem_schools,
        'jhs_school_count': nat_jhs_schools,
        'elem_students': nat_elem_students,
        'elem_teachers': nat_elem_teachers,
        'jhs_students': nat_jhs_students,
        'jhs_teachers': nat_jhs_teachers,
        'student_teacher_ratio': round(nat_elem_students / nat_elem_teachers, 2) if nat_elem_teachers > 0 else 0,
        'elem_pop_per_school': round(nat_elem_pop / nat_elem_schools, 1) if nat_elem_schools > 0 else 0,
        'jhs_pop_per_school': round(nat_jhs_pop / nat_jhs_schools, 1) if nat_jhs_schools > 0 else 0,
        
        'elem_enrolled_per_school': round(nat_elem_students / nat_elem_schools, 1) if nat_elem_schools > 0 else 0,
        'elem_enrolled_per_class': round(nat_elem_students / nat_elem_classes, 1) if nat_elem_classes > 0 else 0,
        'jhs_enrolled_per_school': round(nat_jhs_students / nat_jhs_schools, 1) if nat_jhs_schools > 0 else 0,
        'jhs_enrolled_per_class': round(nat_jhs_students / nat_jhs_classes, 1) if nat_jhs_classes > 0 else 0,
        'jhs_student_teacher_ratio': round(nat_jhs_students / nat_jhs_teachers, 2) if nat_jhs_teachers > 0 else 0,
        'child_under_15_ratio': round(nat_under_15_pop / official_national_pop * 100, 1),
        'pop_change_rate': round((official_national_pop - nat_pop_2015) / nat_pop_2015 * 100, 1),
        
        'private_elem_school_ratio': round(nat_private_elem_schools / nat_elem_schools * 100, 1) if nat_elem_schools > 0 else 0,
        'special_needs_schools_per_100k_age_6_17': round(nat_special_needs_schools / nat_school_age_6_17_pop * 100000, 1) if nat_school_age_6_17_pop > 0 else 0,
        'ict_teaching_capability': 90.7, # Official MEXT national figure for Major Category A
        'waiting_children_per_10k_preschool': round(nat_waiting_children / nat_preschool_pop * 10000, 1) if nat_preschool_pop > 0 else 0
    }
    
    output_obj = {
        'generated_at': '2026-09-14',
        'schema_version': '1.7',
        'description': '全国47都道府県の人口・学齢人口・実在籍生徒数・学級数・教員数・校種構造・独自換算指標（e-Stat・文部科学省「学校基本調査 令和7年度確定値」統合正本）',
        'national_summary': national_summary,
        'indicators_definition': {
            'total_population': {
                'label': '総人口（国勢調査）',
                'unit': '人',
                'description': '令和2年国勢調査（2020年10月1日現在）の外国人を含む総人口確定値。',
                'source': '総務省統計局「令和2年国勢調査 確定値」',
                'base_date': '2020年10月1日時点'
            },
            'elem_age_6_11': {
                'label': '6～11歳人口（小学生期）',
                'unit': '人',
                'description': '小学校期相当の潜在学齢人口（6歳～11歳、国籍総数）。',
                'source': '総務省統計局 e-Stat「令和2年国勢調査 表2-1」',
                'base_date': '2020年10月1日時点'
            },
            'jhs_age_12_14': {
                'label': '12～14歳人口（中学校期）',
                'unit': '人',
                'description': '中学校期相当の潜在学齢人口（12歳～14歳、国籍総数）。',
                'source': '総務省統計局 e-Stat「令和2年国勢調査 表2-1」',
                'base_date': '2020年10月1日時点'
            },
            'elderly_65_plus': {
                'label': '65歳以上人口（高齢人口）',
                'unit': '人',
                'description': '65歳以上の高齢人口（年齢不詳補完値）。',
                'source': '総務省統計局「令和2年国勢調査 年齢不詳補完結果」',
                'base_date': '2020年10月1日時点'
            },
            'aging_rate': {
                'label': '高齢化率（65歳以上割合）',
                'unit': '%',
                'description': '総人口に占める65歳以上人口の割合（年齢不詳補完結果に基づく公式算出値）。',
                'source': '総務省統計局「令和2年国勢調査 年齢不詳補完結果」',
                'base_date': '2020年10月1日時点'
            },
            'total_school_count': {
                'label': '全学校・園数',
                'unit': '校・園',
                'description': '国立・公立・私立の幼稚園から高等専門学校までの全収録学校数。',
                'source': 'Ban.Tai 全国学校データベース',
                'base_date': '2026年9月時点'
            },
            'elem_school_count': {
                'label': '小学校数',
                'unit': '校',
                'description': '都道府県内の小学校数。（文部科学省「学校基本調査 表41」2025年5月1日時点 確定値）',
                'source': '文部科学省「学校基本調査」【確報値】',
                'base_date': '2025年5月1日時点'
            },
            'jhs_school_count': {
                'label': '中学校数',
                'unit': '校',
                'description': '都道府県内の中学校数。（文部科学省「学校基本調査 表67」2025年5月1日時点 確定値）',
                'source': '文部科学省「学校基本調査」【確報値】',
                'base_date': '2025年5月1日時点'
            },
            'elem_students': {
                'label': '小学校児童数',
                'unit': '人',
                'description': '公立・私立小学校の全在籍児童数。',
                'source': '文部科学省「学校基本調査」【確報値】',
                'base_date': '2025年5月1日時点'
            },
            'elem_teachers': {
                'label': '小学校本務教員数',
                'unit': '人',
                'description': '公立・私立小学校の本務教員数。',
                'source': '文部科学省「学校基本調査」【確報値】',
                'base_date': '2025年5月1日時点'
            },
            'student_teacher_ratio': {
                'label': '小学校 教員1人あたり児童数',
                'unit': '人/教員',
                'description': '小学校児童数を本務教員数で除した算出指標。教員1人あたりの平均指導児童数を示します。',
                'source': '文部科学省「学校基本調査」【確報値】',
                'base_date': '2025年5月1日時点'
            },
            'elem_pop_per_school': {
                'label': '小学校1校あたり6～11歳人口',
                'unit': '人/校',
                'description': '6～11歳学齢人口（国籍総数）を小学校数で除した潜在規模指標。（国勢調査2020年 / 学校基本調査2025年）',
                'source': 'e-Stat国勢調査 6～11歳人口（総数） ÷ 学校基本調査 小学校数',
                'base_date': '2020年/2025年'
            },
            'jhs_pop_per_school': {
                'label': '中学校1校あたり12～14歳人口',
                'unit': '人/校',
                'description': '12～14歳学齢人口（国籍総数）を中学校数で除した潜在規模指標。（国勢調査2020年 / 学校基本調査2025年）',
                'source': 'e-Stat国勢調査 12～14歳人口（総数） ÷ 学校基本調査 中学校数',
                'base_date': '2020年/2025年'
            },
            'elem_enrolled_per_school': {
                'label': '小学校1校あたり実児童数',
                'unit': '人/校',
                'description': '小学校児童数を小学校数で除した1校あたり平均在籍児童数。文部科学省「学校基本調査 表41」の同一調査・同一基準日データにより算出。（2025年5月1日時点 確定値）',
                'source': '文部科学省「学校基本調査」【確報値】',
                'base_date': '2025年5月1日時点'
            },
            'elem_enrolled_per_class': {
                'label': '小学校1学級あたり児童数（全学級ベース）',
                'unit': '人/学級',
                'description': '小学校児童数を全学級数（通常＋特別支援学級）で除した1学級あたり平均児童数。',
                'source': '文部科学省「学校基本調査 表46」【確報値】',
                'base_date': '2025年5月1日時点'
            },
            'jhs_enrolled_per_school': {
                'label': '中学校1校あたり生徒数',
                'unit': '人/校',
                'description': '中学校生徒数を中学校数で除した1校あたり平均在籍生徒数。文部科学省「学校基本調査 表67」の同一調査・同一基準日データにより算出。（2025年5月1日時点 確定値）',
                'source': '文部科学省「学校基本調査」【確報値】',
                'base_date': '2025年5月1日時点'
            },
            'jhs_enrolled_per_class': {
                'label': '中学校1学級あたり生徒数（全学級ベース）',
                'unit': '人/学級',
                'description': '中学校生徒数を全学級数（通常＋特別支援学級）で除した1学級あたり平均生徒数。',
                'source': '文部科学省「学校基本調査 表73」【確報値】',
                'base_date': '2025年5月1日時点'
            },
            'jhs_student_teacher_ratio': {
                'label': '中学校 教員1人あたり生徒数',
                'unit': '人/教員',
                'description': '中学校の本務教員1人あたりの担当生徒数（指導負担比率）。（文部科学省「学校基本調査 表82」2025年5月1日時点 確定値）',
                'source': '文部科学省「学校基本調査 表82」【確報値】',
                'base_date': '2025年5月1日時点'
            },
            'child_under_15_ratio': {
                'label': '15歳未満人口割合',
                'unit': '%',
                'description': '総人口に占める15歳未満（年少人口）の割合。（総務省「国勢調査」2020年10月1日時点 確定値）',
                'source': '総務省統計局「令和2年国勢調査 確定値」',
                'base_date': '2020年10月1日時点'
            },
            'pop_change_rate': {
                'label': '人口増減率（5年変化率）',
                'unit': '%',
                'description': '2015年から2020年の5年間における総人口の変化率（+増加/-減少）。',
                'source': '総務省統計局「平成27年・令和2年国勢調査 確定値」',
                'base_date': '2015年〜2020年比較'
            },
            'private_elem_school_ratio': {
                'label': '私立小学校比率',
                'unit': '%',
                'description': '小学校全体に占める私立小学校の割合（私立小学校数÷全小学校数）。（文部科学省「学校基本調査 表41」2025年5月1日時点 確定値）',
                'source': '文部科学省「学校基本調査」【確報値】',
                'base_date': '2025年5月1日時点'
            },
            'special_needs_schools_per_100k_age_6_17': {
                'label': '特別支援学校数（6～17歳人口10万人あたり）',
                'unit': '校/10万人',
                'description': '学齢期人口（6～17歳、国籍総数）10万人あたりの特別支援学校数。※対象障害種・在籍規模・分校等の違いがあるため、学校数が多い＝支援が充実と単純比較しないようご注意ください。（学校基本調査 表199 / 国勢調査）',
                'source': '学校基本調査 / 国勢調査',
                'base_date': '2025年5月1日 / 2020年10月1日時点'
            },
            'ict_teaching_capability': {
                'label': '教員のICT活用能力（大項目A：教材研究・指導の準備・評価・校務などにICTを活用する能力）',
                'unit': '%',
                'description': '教材研究、指導の準備、児童生徒の評価、校務などにICTを活用する能力に関する教員の自己評価割合（大項目A）。（文部科学省「学校における教育の情報化の実態等に関する調査」2025年3月1日時点 確定値）',
                'source': '文部科学省「教育情報化実態調査」',
                'base_date': '2025年3月1日時点'
            },
            'waiting_children_per_10k_preschool': {
                'label': '待機児童数（未就学児 3～5歳人口1万人あたり）',
                'unit': '人/1万人',
                'description': '未就学児（3～5歳人口、国籍総数）1万人あたりの待機児童数。（こども家庭庁「保育所等関連状況取りまとめ」2025年4月1日時点 確定値 / 総務省「令和2年国勢調査」2020年10月1日時点 確定値）',
                'source': 'こども家庭庁 / 国勢調査',
                'base_date': '2025年4月1日／2020年10月1日時点'
            }
        },
        'prefectures': dataset
    }
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_obj, f, ensure_ascii=False, indent=2)
        
    print(f"Dataset successfully built at {OUTPUT_PATH}")
    print(f"Total 24 indicators built cleanly with master MEXT 2025 data!")

if __name__ == '__main__':
    build_dataset()
