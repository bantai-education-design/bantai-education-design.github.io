import json
import os

with open('data/school-database/saitama.json', 'r', encoding='utf-8') as f:
    s_data = json.load(f)
print(f'Current saitama.json length: {len(s_data)}')

os.system('git show main:data/school-database/saitama.json > saitama_main.json')
with open('saitama_main.json', 'r', encoding='utf-8') as f:
    s_main = json.load(f)
print(f'main branch saitama.json length: {len(s_main)}')

with open('data/school-database/prefectures.json', 'r', encoding='utf-8') as f:
    p_data = json.load(f)
    for p in p_data:
        if p['id'] == 'saitama':
            print(f"prefectures.json count: {p.get('school_count', 'N/A')}")
            
os.system('git show main:tools/school-database/index.html > index_main.html')
with open('index_main.html', 'r', encoding='utf-8') as f:
    html = f.read()
    if '1,929' in html: print('1,929 is in index.html on main')
    if '1,932' in html: print('1,932 is in index.html on main')

# find the 3 new ones if any
s_ids = {r.get('id') for r in s_data}
m_ids = {r.get('id') for r in s_main}
diff_ids = s_ids - m_ids
print(f"Added IDs: {diff_ids}")

if not diff_ids and len(s_data) == len(s_main) == 1932:
    print("saitama.json has ALWAYS been 1932. The number 1929 might be a hardcoded typo in index.html")
