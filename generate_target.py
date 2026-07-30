import os
import re

prefs = [
    {"en": "toyama", "ja": "富山", "url": "https://www.pref.toyama.jp/3000/"},
    {"en": "tokushima", "ja": "徳島", "url": "https://www.pref.tokushima.lg.jp/kyouiku/"},
    {"en": "ehime", "ja": "愛媛", "url": "https://www.pref.ehime.jp/site/kyouiku/"},
    {"en": "kochi", "ja": "高知", "url": "https://www.pref.kochi.lg.jp/soshiki/310101/"}
]

with open("tools/school-database/convert_fukui_sources.py", "r", encoding="utf-8") as f:
    template_py = f.read()
    
with open("tools/school-database/fukui/index.html", "r", encoding="utf-8") as f:
    template_html = f.read()
    
with open("assets/js/school-database/search-fukui.js", "r", encoding="utf-8") as f:
    template_js = f.read()

template_html = template_html.replace("https://www.pref.fukui.lg.jp/kyouiku/education/cat2001/index.html", "BOE_URL_PLACEHOLDER")

if "header=1" not in template_py:
    template_py = template_py.replace("pd.read_excel(mext_file)", "pd.read_excel(mext_file, header=1)").replace("pd.read_excel(filepath)", "pd.read_excel(filepath, header=1)")

infer_func_replacement = """import re
def infer_municipality(address: str) -> str:
    text = address
    for pref_name in ["富山県", "徳島県", "愛媛県", "高知県", "福井県", "石川県", "滋賀県", "岐阜県", "三重県", "兵庫県", "岡山県", "山口県", "広島県", "鳥取県", "島根県"]:
        if text.startswith(pref_name):
            text = text[len(pref_name):]
    m = re.match(r'^([^郡]+市|[^郡]+区|.+?郡.+?[町村]|.+?[町村])', text)
    if m:
        return m.group(1)
    return ""
"""

py_lines = template_py.splitlines()
new_py_lines = []
skip = False
for line in py_lines:
    if line.startswith("# ---------------------------------------------------------------------------"): 
        if "福井県 市区町村一覧" in py_lines[py_lines.index(line) + 1]:
            skip = True
    if line.startswith("def warn("): skip = False
    
    if not skip:
        new_py_lines.append(line)

template_py = "\n".join(new_py_lines)
template_py = template_py.replace("def infer_municipality(address: str) -> str:", infer_func_replacement + "\ndef infer_municipality_dummy(address: str) -> str:")

for pref in prefs:
    py_content = template_py.replace("fukui", pref["en"]).replace("福井", pref["ja"])
    with open(f"tools/school-database/convert_{pref['en']}_sources.py", "w", encoding="utf-8") as f:
        f.write(py_content)
        
    os.makedirs(f"tools/school-database/{pref['en']}", exist_ok=True)
    html_content = template_html.replace("fukui", pref["en"]).replace("福井県", f"{pref['ja']}県")
    html_content = html_content.replace("BOE_URL_PLACEHOLDER", pref["url"])
    with open(f"tools/school-database/{pref['en']}/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    js_content = template_js.replace("fukui", pref["en"]).replace("福井県", f"{pref['ja']}県")
    with open(f"assets/js/school-database/search-{pref['en']}.js", "w", encoding="utf-8") as f:
        f.write(js_content)

print("Generated scripts, HTML, and JS.")
