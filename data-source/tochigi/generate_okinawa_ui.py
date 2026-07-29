import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

# 1. Generate search-okinawa.js from yamagata template
js_src = os.path.join(base_dir, 'assets', 'js', 'school-database', 'search-yamagata.js')
js_dst = os.path.join(base_dir, 'assets', 'js', 'school-database', 'search-okinawa.js')

with open(js_src, 'r', encoding='utf-8') as f:
    js_content = f.read()

js_content = js_content.replace('山形県学校宛先データベース', '沖縄県学校宛先データベース')
js_content = js_content.replace('search-yamagata.js', 'search-okinawa.js')
js_content = js_content.replace("fetch('/data/school-database/yamagata.json')", "fetch('/data/school-database/okinawa.json')")
js_content = js_content.replace("Error fetching Yamagata school data:", "Error fetching Okinawa school data:")
js_content = js_content.replace("yamagata", "okinawa")
js_content = js_content.replace("山形県", "沖縄県")

new_muni = """const MUNICIPALITY_ORDER = [
    "那覇市", "宜野湾市", "石垣市", "浦添市", "名護市", "糸満市", "沖縄市", "豊見城市", "うるま市", "宮古島市", "南城市",
    "国頭郡国頭村", "国頭郡大宜味村", "国頭郡東村", "国頭郡今帰仁村", "国頭郡本部町", "国頭郡恩納村", "国頭郡宜野座村", "国頭郡金武町", "国頭郡伊江村",
    "中頭郡読谷村", "中頭郡嘉手納町", "中頭郡北谷町", "中頭郡北中城村", "中頭郡中城村", "中頭郡西原町",
    "島尻郡与那原町", "島尻郡南風原町", "島尻郡渡嘉敷村", "島尻郡座間味村", "島尻郡粟国村", "島尻郡渡名喜村", "島尻郡南大東村", "島尻郡北大東村", "島尻郡伊平屋村", "島尻郡伊是名村", "島尻郡八重瀬町", "島尻郡久米島町",
    "宮古郡多良間村",
    "八重山郡竹富町", "八重山郡与那国町"
  ];"""
js_content = re.sub(r'const MUNICIPALITY_ORDER = \[[^\]]+\];', new_muni, js_content, flags=re.DOTALL)

os.makedirs(os.path.dirname(js_dst), exist_ok=True)
with open(js_dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write(js_content)
print(f"Generated {js_dst}")

# 2. Generate tools/school-database/okinawa/index.html
html_src = os.path.join(base_dir, 'tools', 'school-database', 'yamagata', 'index.html')
html_dst = os.path.join(base_dir, 'tools', 'school-database', 'okinawa', 'index.html')

with open(html_src, 'r', encoding='utf-8') as f:
    html_content = f.read()

html_content = html_content.replace('山形県', '沖縄県')
html_content = html_content.replace('yamagata', 'okinawa')
html_content = html_content.replace('442校・園', '626校・園')

os.makedirs(os.path.dirname(html_dst), exist_ok=True)
with open(html_dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write(html_content)
print(f"Generated {html_dst}")
