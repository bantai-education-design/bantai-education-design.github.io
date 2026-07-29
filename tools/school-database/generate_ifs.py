import os
import shutil
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
prefectures = [
    ("ishikawa", "石川県", "17(石川)", "https://www.pref.ishikawa.lg.jp/kyoiku/index.html"),
    ("fukui", "福井県", "18(福井)", "https://www.pref.fukui.lg.jp/doc/kyouiku/index.html"),
    ("shiga", "滋賀県", "25(滋賀)", "https://www.pref.shiga.lg.jp/edu/")
]

def generate_ui_and_js(pref_en, pref_ja, boe_url):
    print(f"Generating UI for {pref_ja}...")
    
    # 1. Generate tools/school-database/{pref_en}/index.html
    target_html_dir = os.path.join(base_dir, "tools", "school-database", pref_en)
    os.makedirs(target_html_dir, exist_ok=True)
    
    with open(os.path.join(base_dir, "tools", "school-database", "yamagata", "index.html"), "r", encoding="utf-8") as f:
        html = f.read()
    
    html = html.replace("yamagata", pref_en)
    html = html.replace("Yamagata", pref_en.capitalize())
    html = html.replace("山形県", pref_ja)
    
    # Replace BOE URL
    # Find the old Yamagata BOE URL and replace it
    old_yamagata_url = "https://www.pref.yamagata.jp/700001/bunkyo/kyoiku/shougai/school-list.html"
    if old_yamagata_url in html:
        html = html.replace(old_yamagata_url, boe_url)
    else:
        # regex replace
        html = re.sub(r'href="[^"]*".*?>' + pref_ja + r'教育委員会', f'href="{boe_url}" target="_blank">{pref_ja}教育委員会', html)
    
    with open(os.path.join(target_html_dir, "index.html"), "w", encoding="utf-8", newline='\n') as f:
        f.write(html)
        
    # 2. Generate assets/js/school-database/search-{pref_en}.js
    with open(os.path.join(base_dir, "assets", "js", "school-database", "search-yamagata.js"), "r", encoding="utf-8") as f:
        js = f.read()
        
    js = js.replace("yamagata", pref_en)
    js = js.replace("Yamagata", pref_en.capitalize())
    js = js.replace("山形県", pref_ja)
    
    # Check if there is an empty municipality filter logic, it should already be handled by Set
    
    with open(os.path.join(base_dir, "assets", "js", "school-database", f"search-{pref_en}.js"), "w", encoding="utf-8", newline='\n') as f:
        f.write(js)
        
    # 3. Create the database generator script
    with open(os.path.join(base_dir, "tools", "school-database", "convert_yamagata_sources.py"), "r", encoding="utf-8") as f:
        py = f.read()
        
    py = py.replace("yamagata", pref_en)
    py = py.replace("Yamagata", pref_en.capitalize())
    py = py.replace("山形県", pref_ja)
    py = py.replace("06(山形)", [p[2] for p in prefectures if p[0] == pref_en][0])
    
    # Update prefixes 
    py = py.replace("YAMAGATA_", f"{pref_en.upper()}_")
    
    with open(os.path.join(base_dir, "tools", "school-database", f"convert_{pref_en}_sources.py"), "w", encoding="utf-8", newline='\n') as f:
        f.write(py)
        
for p in prefectures:
    generate_ui_and_js(p[0], p[1], p[3])
