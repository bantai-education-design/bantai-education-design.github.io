import json
from pathlib import Path

ROOT = Path(r'C:\Users\User\.gemini\antigravity\scratch\bantai-education-design.github.io')
CARD_META_PATH = ROOT / 'data' / 'school-database' / 'prefecture-card-metadata.json'
EXT_STATS_PATH = ROOT / 'data' / 'school-database' / 'prefecture-education-external-stats.json'
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

def build_dataset():
    with open(CARD_META_PATH, 'r', encoding='utf-8') as f:
        card_meta = json.load(f)
        
    with open(EXT_STATS_PATH, 'r', encoding='utf-8') as f:
        ext_stats = json.load(f)
        
    ext_dict = {item['prefecture_code']: item for item in ext_stats.get('prefectures', [])}
    
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
        total_pop = census_data.get('total_pop', pref.get('population', {}).get('census_population', 0))
        elderly_pop = census_data.get('elderly_65_plus', 0)
        
        school_db = pref.get('school_database', {})
        total_schools = school_db.get('record_count', 0)
        
        pref_school_json = ROOT / 'data' / 'school-database' / f'{code}.json'
        elem_count = 0
        jhs_count = 0
        hs_count = 0
        if pref_school_json.exists():
            with open(pref_school_json, 'r', encoding='utf-8') as sf:
                schools = json.load(sf)
                for s in schools:
                    stype = s.get('school_type', '')
                    if '小学校' in stype and '特別支援' not in stype:
                        elem_count += 1
                    elif '中学校' in stype and '特別支援' not in stype:
                        jhs_count += 1
                    elif '高等学校' in stype or '高校' in stype:
                        hs_count += 1
                        
        pop = pref.get('population', {})
        elem_pop = 0
        jhs_pop = 0
        hs_pop = 0
        
        for ag in pop.get('age_groups', []):
            if ag.get('key') == 'census_elementary_6_11':
                elem_pop = ag.get('population', 0)
            elif ag.get('key') == 'census_junior_high_12_14':
                jhs_pop = ag.get('population', 0)
            elif ag.get('key') == 'census_high_school_15_17':
                hs_pop = ag.get('population', 0)
                
        ext = ext_dict.get(code, {})
        ratio_detail = ext.get('student_teacher_ratio_detail', {})
        elem_teachers = ratio_detail.get('teacher_count', 0)
        elem_students = ratio_detail.get('student_count', 0)
        student_teacher_ratio = ext.get('student_teacher_ratio', 0)
        
        aging_rate = round(elderly_pop / total_pop * 100, 1) if total_pop > 0 else 0
        elem_pop_per_school = round(elem_pop / elem_count, 1) if elem_count > 0 else 0
        jhs_pop_per_school = round(jhs_pop / jhs_count, 1) if jhs_count > 0 else 0
        
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
            'aging_rate': aging_rate,
            'total_school_count': total_schools,
            'elem_school_count': elem_count,
            'jhs_school_count': jhs_count,
            'hs_school_count': hs_count,
            'elem_students': elem_students,
            'elem_teachers': elem_teachers,
            'student_teacher_ratio': student_teacher_ratio,
            'elem_pop_per_school': elem_pop_per_school,
            'jhs_pop_per_school': jhs_pop_per_school
        }
        dataset.append(entry)
        
    indicators = [
        'total_population', 'elem_age_6_11', 'jhs_age_12_14', 'elderly_65_plus',
        'aging_rate', 'total_school_count', 'elem_school_count', 'jhs_school_count',
        'elem_students', 'elem_teachers', 'student_teacher_ratio',
        'elem_pop_per_school', 'jhs_pop_per_school'
    ]
    
    ranks = {ind: {} for ind in indicators}
    for ind in indicators:
        sorted_list = sorted(dataset, key=lambda x: x[ind], reverse=True)
        for r_idx, item in enumerate(sorted_list):
            ranks[ind][item['code']] = r_idx + 1
            
    for item in dataset:
        item['ranks'] = {ind: ranks[ind][item['code']] for ind in indicators}
        
    nat_total_pop = sum(d['total_population'] for d in dataset)
    nat_elem_pop = sum(d['elem_age_6_11'] for d in dataset)
    nat_jhs_pop = sum(d['jhs_age_12_14'] for d in dataset)
    nat_elderly_pop = 36026632  # Official 2020 Census national 65+ population (年齢不詳按分/補完確定値)
    nat_total_schools = sum(d['total_school_count'] for d in dataset)
    nat_elem_schools = sum(d['elem_school_count'] for d in dataset)
    nat_jhs_schools = sum(d['jhs_school_count'] for d in dataset)
    nat_elem_students = sum(d['elem_students'] for d in dataset)
    nat_elem_teachers = sum(d['elem_teachers'] for d in dataset)
    
    # Official Census national total population confirmed figure: 126146099
    official_national_pop = 126146099
    
    national_summary = {
        'total_population': official_national_pop,
        'elem_age_6_11': nat_elem_pop,
        'jhs_age_12_14': nat_jhs_pop,
        'elderly_65_plus': nat_elderly_pop,
        'aging_rate': round(nat_elderly_pop / official_national_pop * 100, 1), # 28.6%
        'total_school_count': nat_total_schools,
        'elem_school_count': nat_elem_schools,
        'jhs_school_count': nat_jhs_schools,
        'elem_students': nat_elem_students,
        'elem_teachers': nat_elem_teachers,
        'student_teacher_ratio': round(nat_elem_students / nat_elem_teachers, 2) if nat_elem_teachers > 0 else 0,
        'elem_pop_per_school': round(nat_elem_pop / nat_elem_schools, 1) if nat_elem_schools > 0 else 0,
        'jhs_pop_per_school': round(nat_jhs_pop / nat_jhs_schools, 1) if nat_jhs_schools > 0 else 0
    }
    
    output_obj = {
        'generated_at': '2026-09-13',
        'schema_version': '1.1',
        'description': '全国47都道府県の人口・学齢人口・学校数・教員数・独自換算指標（e-Stat・文部科学省・Ban.Tai統合データベース正本）',
        'national_summary': national_summary,
        'indicators_definition': {
            'total_population': {
                'label': '総人口（国勢調査）',
                'unit': '人',
                'description': '令和2年国勢調査（2020年10月1日現在）の外国人を含む総人口確定値。',
                'source': '総務省統計局「令和2年国勢調査 確定値（表1）」',
                'base_date': '2020年10月1日時点'
            },
            'elem_age_6_11': {
                'label': '6～11歳人口（小学生期）',
                'unit': '人',
                'description': '小学校期相当の学齢人口（6歳～11歳）。',
                'source': '総務省統計局 e-Stat「社会・人口統計体系」',
                'base_date': '2020年10月1日時点'
            },
            'jhs_age_12_14': {
                'label': '12～14歳人口（中学校期）',
                'unit': '人',
                'description': '中学校期相当の学齢人口（12歳～14歳）。',
                'source': '総務省統計局 e-Stat「社会・人口統計体系」',
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
                'description': '本データベースに収録されている小学校（本校・分校含む）の総数。',
                'source': 'Ban.Tai 全国学校データベース',
                'base_date': '2026年9月時点'
            },
            'jhs_school_count': {
                'label': '中学校数',
                'unit': '校',
                'description': '本データベースに収録されている中学校（本校・分校含む）の総数。',
                'source': 'Ban.Tai 全国学校データベース',
                'base_date': '2026年9月時点'
            },
            'elem_students': {
                'label': '小学校児童数',
                'unit': '人',
                'description': '公立・私立小学校の全児童数。',
                'source': '文部科学省「学校基本調査」',
                'base_date': '2025年5月1日時点'
            },
            'elem_teachers': {
                'label': '小学校本務教員数',
                'unit': '人',
                'description': '公立・私立小学校の本務教員数。',
                'source': '文部科学省「学校基本調査」',
                'base_date': '2025年5月1日時点'
            },
            'student_teacher_ratio': {
                'label': '教員1人あたり児童数',
                'unit': '人/教員',
                'description': '小学校児童数を小学校本務教員数で除した算出指標。教員一人あたりの平均指導児童数を示します。',
                'source': '文部科学省「学校基本調査」（令和7年5月1日時点）より算出',
                'base_date': '2025年5月1日時点'
            },
            'elem_pop_per_school': {
                'label': '小学校1校あたり6～11歳人口',
                'unit': '人/校',
                'description': '6～11歳学齢人口を当該都道府県の小学校数で除した独自算定指標。地域における1校あたり学齢人口規模の目安。',
                'source': 'e-Stat国勢調査 6～11歳人口 ÷ Ban.Tai小学校数',
                'base_date': '2020年/2026年'
            },
            'jhs_pop_per_school': {
                'label': '中学校1校あたり12～14歳人口',
                'unit': '人/校',
                'description': '12～14歳学齢人口を当該都道府県の中学校数で除した独自算定指標。地域における1校あたり学齢人口規模の目安。',
                'source': 'e-Stat国勢調査 12～14歳人口 ÷ Ban.Tai中学校数',
                'base_date': '2020年/2026年'
            }
        },
        'prefectures': dataset
    }
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_obj, f, ensure_ascii=False, indent=2)
        
    print(f"Dataset successfully built at {OUTPUT_PATH}")
    print(f"National aggregate aging rate: {national_summary['aging_rate']}% (Elderly: {national_summary['elderly_65_plus']:,} / Total: {national_summary['total_population']:,})")
    
    akita = [p for p in dataset if p['code'] == 'akita'][0]
    tokyo = [p for p in dataset if p['code'] == 'tokyo'][0]
    okinawa = [p for p in dataset if p['code'] == 'okinawa'][0]
    
    print(f"Akita Aging Rate: {akita['aging_rate']}% (Rank {akita['ranks']['aging_rate']}) - Elderly: {akita['elderly_65_plus']:,}")
    print(f"Tokyo Aging Rate: {tokyo['aging_rate']}% (Rank {tokyo['ranks']['aging_rate']}) - Elderly: {tokyo['elderly_65_plus']:,}")
    print(f"Okinawa Aging Rate: {okinawa['aging_rate']}% (Rank {okinawa['ranks']['aging_rate']}) - Elderly: {okinawa['elderly_65_plus']:,}")

if __name__ == '__main__':
    build_dataset()
