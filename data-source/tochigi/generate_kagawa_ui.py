import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

# 1. Generate search-kagawa.js from yamagata template
js_src = os.path.join(base_dir, 'assets', 'js', 'school-database', 'search-yamagata.js')
js_dst = os.path.join(base_dir, 'assets', 'js', 'school-database', 'search-kagawa.js')

with open(js_src, 'r', encoding='utf-8') as f:
    js_content = f.read()

js_content = js_content.replace('山形県学校宛先データベース', '香川県学校宛先データベース')
js_content = js_content.replace('search-yamagata.js', 'search-kagawa.js')
js_content = js_content.replace("fetch('/data/school-database/yamagata.json')", "fetch('/data/school-database/kagawa.json')")
js_content = js_content.replace("Error fetching Yamagata school data:", "Error fetching Kagawa school data:")
js_content = js_content.replace("yamagata", "kagawa")
js_content = js_content.replace("山形県", "香川県")

new_muni = """const MUNICIPALITY_ORDER = [
    "高松市", "丸亀市", "坂出市", "善通寺市", "観音寺市", "さぬき市", "東かがわ市", "三豊市",
    "小豆郡土庄町", "小豆郡小豆島町",
    "木田郡三木町",
    "香川郡直島町",
    "綾歌郡宇多津町", "綾歌郡綾川町",
    "仲多度郡琴平町", "仲多度郡多度津町", "仲多度郡まんのう町"
  ];"""
js_content = re.sub(r'const MUNICIPALITY_ORDER = \[[^\]]+\];', new_muni, js_content, flags=re.DOTALL)

os.makedirs(os.path.dirname(js_dst), exist_ok=True)
with open(js_dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write(js_content)
print(f"Generated {js_dst}")

# 2. Generate tools/school-database/kagawa/index.html
html_src = os.path.join(base_dir, 'tools', 'school-database', 'yamagata', 'index.html')
html_dst = os.path.join(base_dir, 'tools', 'school-database', 'kagawa', 'index.html')

with open(html_src, 'r', encoding='utf-8') as f:
    html_content = f.read()

html_content = html_content.replace('山形県', '香川県')
html_content = html_content.replace('yamagata', 'kagawa')
html_content = html_content.replace('442校・園', '379校・園')

os.makedirs(os.path.dirname(html_dst), exist_ok=True)
with open(html_dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write(html_content)
print(f"Generated {html_dst}")
