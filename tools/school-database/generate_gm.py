import os
import shutil

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

prefectures = [
    ("gifu", "岐阜県", "21(岐阜)", "https://www.pref.gifu.lg.jp/"),
    ("mie", "三重県", "24(三重)", "https://www.pref.mie.lg.jp/")
]

template_py = os.path.join(base_dir, "tools/school-database/convert_yamagata_sources.py")
template_html = os.path.join(base_dir, "tools/school-database/yamagata/index.html")
template_js = os.path.join(base_dir, "assets/js/school-database/search-yamagata.js")

with open(template_py, "r", encoding="utf-8") as f:
    py_content = f.read()

with open(template_html, "r", encoding="utf-8") as f:
    html_content = f.read()

with open(template_js, "r", encoding="utf-8") as f:
    js_content = f.read()

for pref_en, pref_ja, pref_code, pref_url in prefectures:
    # 1. Python convert script
    py_out = py_content
    py_out = py_out.replace("yamagata", pref_en)
    py_out = py_out.replace("Yamagata", pref_en.capitalize())
    py_out = py_out.replace("山形県", pref_ja)
    py_out = py_out.replace("YAMAGATA_", pref_en.upper() + "_")
    py_out = py_out.replace("06(山形)", pref_code)
    
    # 2. HTML file
    pref_dir = os.path.join(base_dir, "tools/school-database", pref_en)
    os.makedirs(pref_dir, exist_ok=True)
    html_out = html_content
    html_out = html_out.replace("yamagata", pref_en)
    html_out = html_out.replace("山形県", pref_ja)
    html_out = html_out.replace("478", "0") # placeholder count
    html_out = html_out.replace('href="https://kyoiku.pref.yamagata.jp/"', f'href="{pref_url}"')
    html_out = html_out.replace('href="https://kyoiku.pref.yamagata.jp/about/survey/school-list/"', f'href="{pref_url}"')
    html_out = html_out.replace('href="https://kyoiku.pref.yamagata.jp/gakko/private-schools/"', f'href="{pref_url}"')
    
    with open(os.path.join(pref_dir, "index.html"), "w", encoding="utf-8", newline='\n') as f:
        f.write(html_out)
        
    # 3. JS file
    js_out = js_content
    js_out = js_out.replace("yamagata", pref_en)
    js_out = js_out.replace("山形県", pref_ja)
    
    with open(os.path.join(base_dir, f"assets/js/school-database/search-{pref_en}.js"), "w", encoding="utf-8", newline='\n') as f:
        f.write(js_out)
    
    # Also write out the py script but we need to patch it for the 廃止年月日 and df.columns bugs.
    # We will do that via a separate fix pass just like before to make sure it's 100% correct.
    with open(os.path.join(base_dir, f"tools/school-database/convert_{pref_en}_sources.py"), "w", encoding="utf-8", newline='\n') as f:
        f.write(py_out)

print("Generated templates for Gifu and Mie.")
