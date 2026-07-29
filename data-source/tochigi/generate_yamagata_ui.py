#!/usr/bin/env python3
"""山形県版 search-yamagata.js と tools/school-database/yamagata/index.html を生成する"""
import os
import re

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# 1. Generate search-yamagata.js from tochigi template
js_src = os.path.join(base_dir, 'assets', 'js', 'school-database', 'search-tochigi.js')
js_dst = os.path.join(base_dir, 'assets', 'js', 'school-database', 'search-yamagata.js')

with open(js_src, 'r', encoding='utf-8') as f:
    js_content = f.read()

js_content = js_content.replace('栃木県学校宛先データベース', '山形県学校宛先データベース')
js_content = js_content.replace('search-tochigi.js', 'search-yamagata.js')
js_content = js_content.replace("fetch('/data/school-database/tochigi.json')", "fetch('/data/school-database/yamagata.json')")
js_content = js_content.replace("Error fetching Tochigi school data:", "Error fetching Yamagata school data:")
js_content = js_content.replace("tochigi", "yamagata")
js_content = js_content.replace("栃木県", "山形県")

# Replace MUNICIPALITY_ORDER with Yamagata's list
old_muni = re.search(r'const MUNICIPALITY_ORDER = \[[^\]]+\];', js_content, re.DOTALL).group(0)
new_muni = """const MUNICIPALITY_ORDER = [
    '山形市', '米沢市', '鶴岡市', '酒田市', '新庄市', '寒河江市',
    '上山市', '村山市', '長井市', '天童市', '東根市', '尾花沢市', '南陽市',
    '東村山郡山辺町', '東村山郡中山町',
    '西村山郡河北町', '西村山郡西川町', '西村山郡朝日町', '西村山郡大江町',
    '北村山郡大石田町',
    '最上郡金山町', '最上郡最上町', '最上郡舟形町', '最上郡真室川町',
    '最上郡大蔵村', '最上郡鮭川村', '最上郡戸沢村',
    '東置賜郡高畠町', '東置賜郡川西町',
    '西置賜郡小国町', '西置賜郡白鷹町', '西置賜郡飯豊町',
    '東田川郡三川町', '東田川郡庄内町',
    '飽海郡遊佐町'
  ];"""
js_content = js_content.replace(old_muni, new_muni)

os.makedirs(os.path.dirname(js_dst), exist_ok=True)
with open(js_dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write(js_content)
print(f"Generated {js_dst}")

# 2. Generate tools/school-database/yamagata/index.html
html_src = os.path.join(base_dir, 'tools', 'school-database', 'tochigi', 'index.html')
html_dst = os.path.join(base_dir, 'tools', 'school-database', 'yamagata', 'index.html')

with open(html_src, 'r', encoding='utf-8') as f:
    html_content = f.read()

html_content = html_content.replace('栃木県', '山形県')
html_content = html_content.replace('tochigi', 'yamagata')
html_content = html_content.replace('678校・園', '442校・園')

os.makedirs(os.path.dirname(html_dst), exist_ok=True)
with open(html_dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write(html_content)
print(f"Generated {html_dst}")
