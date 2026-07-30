import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
tools_dir = os.path.join(base_dir, "tools", "school-database")

pref = {"en": "hyogo", "ja": "兵庫", "code": "28", "url": "https://www.hyogo-c.ed.jp/"}
muni_list = ['神戸市', '姫路市', '尼崎市', '明石市', '西宮市', '洲本市', '芦屋市', '伊丹市', '相生市', '豊岡市', '加古川市', '赤穂市', '西脇市', '宝塚市', '三木市', '高砂市', '川西市', '小野市', '三田市', '加西市', '丹波篠山市', '養父市', '丹波市', '南あわじ市', '朝来市', '淡路市', '宍粟市', '加東市', 'たつの市', '川辺郡猪名川町', '多可郡多可町', '加古郡稲美町', '加古郡播磨町', '神崎郡市川町', '神崎郡福崎町', '神崎郡神河町', '揖保郡太子町', '赤穂郡上郡町', '佐用郡佐用町', '美方郡香美町', '美方郡新温泉町']

with open(os.path.join(tools_dir, "convert_fukui_sources.py"), "r", encoding="utf-8") as f:
    template_py = f.read()

# 1. Generate conversion script
script = template_py.replace("fukui", pref["en"])
script = script.replace("福井県", f"{pref['ja']}県")
script = script.replace("FUKUI", pref["en"].upper())
script = script.replace('18(福井)', f"{pref['code']}({pref['ja']})")

cities = [m for m in muni_list if m.endswith('市')]
towns = [m for m in muni_list if not m.endswith('市')]

cities_str = f"{pref['en'].upper()}_CITIES = {repr(cities)}"
towns_str = f"{pref['en'].upper()}_GUN_TOWNS = {repr(towns)}"

script = re.sub(r'FUKUI_CITIES\s*=\s*\[.*?\]', cities_str, script, flags=re.DOTALL)
script = re.sub(r'FUKUI_GUN_TOWNS\s*=\s*\[.*?\]', towns_str, script, flags=re.DOTALL)

script = script.replace('Path("data-source/tochigi")', 'Path("data-source/mext")')
script = script.replace("Path('data-source/tochigi')", "Path('data-source/mext')")

out_py = os.path.join(tools_dir, f"convert_{pref['en']}_sources.py")
with open(out_py, "w", encoding="utf-8", newline='\n') as f:
    f.write(script)

# 2. Generate HTML
fukui_html_dir = os.path.join(tools_dir, "fukui")
with open(os.path.join(fukui_html_dir, "index.html"), "r", encoding="utf-8") as f:
    template_html = f.read()

pref_dir = os.path.join(tools_dir, pref["en"])
os.makedirs(pref_dir, exist_ok=True)
html_content = template_html.replace("fukui", pref["en"])
html_content = html_content.replace("福井県", f"{pref['ja']}県")

old_urls = [
    "https://www.pref.fukui.lg.jp/kyouiku/education/cat2001/index.html",
    "https://kyoiku.pref.fukui.jp/",
    "https://kyoiku.pref.fukui.jp/about/survey/school-list/",
    "https://kyoiku.pref.fukui.jp/gakko/private-schools/"
]
for old_url in old_urls:
    html_content = html_content.replace(old_url, pref["url"])

out_html = os.path.join(pref_dir, "index.html")
with open(out_html, "w", encoding="utf-8", newline='\n') as f:
    f.write(html_content)

# 3. Generate JS
js_dir = os.path.join(base_dir, "assets", "js", "school-database")
with open(os.path.join(js_dir, "search-fukui.js"), "r", encoding="utf-8") as f:
    template_js = f.read()

js_content = template_js.replace("fukui", pref["en"]).replace("福井県", f"{pref['ja']}県")
out_js = os.path.join(js_dir, f"search-{pref['en']}.js")
with open(out_js, "w", encoding="utf-8", newline='\n') as f:
    f.write(js_content)

print(f"Generated scaffolding for {pref['ja']}県.")
