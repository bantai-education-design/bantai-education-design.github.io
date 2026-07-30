import json
import re

prefs = [
    {"en": "toyama", "ja": "富山"},
    {"en": "tokushima", "ja": "徳島"},
    {"en": "ehime", "ja": "愛媛"},
    {"en": "kochi", "ja": "高知"}
]

for pref in prefs:
    # Fix JS MUNICIPALITY_ORDER
    json_path = f"data/school-database/{pref['en']}.json"
    data = json.load(open(json_path, encoding='utf-8'))
    
    muni_set = set()
    for item in data:
        if item.get('municipality'):
            muni_set.add(item['municipality'])
            
    muni_list = sorted(list(muni_set))
    
    js_path = f"assets/js/school-database/search-{pref['en']}.js"
    js = open(js_path, encoding='utf-8').read()
    
    new_order_str = 'const MUNICIPALITY_ORDER = [\n    ' + ', '.join(f"'{m}'" for m in muni_list) + '\n  ];'
    
    # regex sub MUNICIPALITY_ORDER
    js = re.sub(r'const MUNICIPALITY_ORDER = \[[^\]]*\];', new_order_str, js)
    
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js)

print("Fixed JS for all 4 prefectures.")
