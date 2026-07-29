import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

# 1. Generate search-fukuoka.js from yamagata template
js_src = os.path.join(base_dir, 'assets', 'js', 'school-database', 'search-yamagata.js')
js_dst = os.path.join(base_dir, 'assets', 'js', 'school-database', 'search-fukuoka.js')

with open(js_src, 'r', encoding='utf-8') as f:
    js_content = f.read()

js_content = js_content.replace('山形県学校宛先データベース', '福岡県学校宛先データベース')
js_content = js_content.replace('search-yamagata.js', 'search-fukuoka.js')
js_content = js_content.replace("fetch('/data/school-database/yamagata.json')", "fetch('/data/school-database/fukuoka.json')")
js_content = js_content.replace("Error fetching Yamagata school data:", "Error fetching Fukuoka school data:")
js_content = js_content.replace("yamagata", "fukuoka")
js_content = js_content.replace("山形県", "福岡県")

new_muni = """const MUNICIPALITY_ORDER = [
    "福岡市", "北九州市", "久留米市", "大牟田市", "直方市", "飯塚市", "田川市", "柳川市", "八女市", "筑後市", "大川市", "行橋市", "豊前市", "中間市", "小郡市", "筑紫野市", "春日市", "大野城市", "宗像市", "太宰府市", "古賀市", "福津市", "うきは市", "宮若市", "嘉麻市", "朝倉市", "みやま市", "糸島市", "那珂川市",
    "糟屋郡宇美町", "糟屋郡篠栗町", "糟屋郡志免町", "糟屋郡須恵町", "糟屋郡新宮町", "糟屋郡久山町", "糟屋郡粕屋町",
    "遠賀郡芦屋町", "遠賀郡水巻町", "遠賀郡岡垣町", "遠賀郡遠賀町",
    "鞍手郡小竹町", "鞍手郡鞍手町",
    "嘉穂郡桂川町",
    "朝倉郡筑前町", "朝倉郡東峰村",
    "三井郡大刀洗町",
    "三潴郡大木町",
    "八女郡広川町",
    "田川郡香春町", "田川郡添田町", "田川郡糸田町", "田川郡川崎町", "田川郡大任町", "田川郡赤村", "田川郡福智町",
    "京都郡苅田町", "京都郡みやこ町",
    "築上郡吉富町", "築上郡上毛町", "築上郡築上町"
  ];"""
js_content = re.sub(r'const MUNICIPALITY_ORDER = \[[^\]]+\];', new_muni, js_content, flags=re.DOTALL)

os.makedirs(os.path.dirname(js_dst), exist_ok=True)
with open(js_dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write(js_content)
print(f"Generated {js_dst}")

# 2. Generate tools/school-database/fukuoka/index.html
html_src = os.path.join(base_dir, 'tools', 'school-database', 'yamagata', 'index.html')
html_dst = os.path.join(base_dir, 'tools', 'school-database', 'fukuoka', 'index.html')

with open(html_src, 'r', encoding='utf-8') as f:
    html_content = f.read()

html_content = html_content.replace('山形県', '福岡県')
html_content = html_content.replace('yamagata', 'fukuoka')
html_content = html_content.replace('442校・園', '1,659校・園')

os.makedirs(os.path.dirname(html_dst), exist_ok=True)
with open(html_dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write(html_content)
print(f"Generated {html_dst}")
