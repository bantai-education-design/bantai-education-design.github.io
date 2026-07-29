#!/usr/bin/env python3
import os
import re

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# 1. Generate search-tochigi.js
js_src = os.path.join(base_dir, 'assets', 'js', 'school-database', 'search-ibaraki.js')
js_dst = os.path.join(base_dir, 'assets', 'js', 'school-database', 'search-tochigi.js')

with open(js_src, 'r', encoding='utf-8') as f:
    js_content = f.read()

# Replace references
js_content = js_content.replace('茨城県学校宛先データベース', '栃木県学校宛先データベース')
js_content = js_content.replace('search-ibaraki.js', 'search-tochigi.js')
js_content = js_content.replace('茨城県', '栃木県')
js_content = js_content.replace('Ibaraki', 'Tochigi')
js_content = js_content.replace('/data/school-database/ibaraki.json', '/data/school-database/tochigi.json')
js_content = js_content.replace('ibaraki', 'tochigi')

# Replace MUNICIPALITY_ORDER
old_muni = re.search(r'const MUNICIPALITY_ORDER = \[[^\]]+\];', js_content, re.DOTALL).group(0)
new_muni = """const MUNICIPALITY_ORDER = [
    '宇都宮市', '足利市', '栃木市', '佐野市', '鹿沼市', '日光市', '小山市', '真岡市',
    '大田原市', '矢板市', '那須塩原市', 'さくら市', '那須烏山市', '下野市',
    '河内郡上三川町',
    '芳賀郡益子町', '芳賀郡茂木町', '芳賀郡市貝町', '芳賀郡芳賀町',
    '下都賀郡壬生町', '下都賀郡野木町',
    '塩谷郡塩谷町', '塩谷郡高根沢町',
    '那須郡那須町', '那須郡那珂川町'
  ];"""
js_content = js_content.replace(old_muni, new_muni)

os.makedirs(os.path.dirname(js_dst), exist_ok=True)
with open(js_dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write(js_content)
print(f"Generated {js_dst}")

# 2. Generate tools/school-database/tochigi/index.html
html_src = os.path.join(base_dir, 'tools', 'school-database', 'ibaraki', 'index.html')
html_dst = os.path.join(base_dir, 'tools', 'school-database', 'tochigi', 'index.html')

with open(html_src, 'r', encoding='utf-8') as f:
    html_content = f.read()

html_content = html_content.replace('茨城県', '栃木県')
html_content = html_content.replace('ibaraki', 'tochigi')
html_content = html_content.replace('872校・園', '678校・園')
html_content = html_content.replace('水戸市立・日立第一・高専等', '宇都宮市立・作新学院等')

os.makedirs(os.path.dirname(html_dst), exist_ok=True)
with open(html_dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write(html_content)
print(f"Generated {html_dst}")
