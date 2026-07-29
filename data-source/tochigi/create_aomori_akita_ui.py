import os
import shutil

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

def create_ui(pref_en, pref_ja, pref_code, boe_url):
    print(f"Creating UI for {pref_en} ({pref_ja})")
    
    # 1. Update search.js
    yamagata_js = os.path.join(base_dir, "assets", "js", "school-database", "search-yamagata.js")
    out_js = os.path.join(base_dir, "assets", "js", "school-database", f"search-{pref_en}.js")
    with open(yamagata_js, "r", encoding="utf-8") as f:
        js = f.read()
    js = js.replace("yamagata", pref_en)
    js = js.replace("YAMAGATA", pref_en.upper())
    js = js.replace("山形", pref_ja.replace("県", ""))
    with open(out_js, "w", encoding="utf-8") as f:
        f.write(js)
        
    # 2. Update style.css (if we want, we can just copy yamagata or link to it, but wait, the CSS was shared. Wait, in previous runs we just copied style.css)
    yamagata_css = os.path.join(base_dir, "tools", "school-database", "yamagata", "style.css")
    out_dir = os.path.join(base_dir, "tools", "school-database", pref_en)
    os.makedirs(out_dir, exist_ok=True)
    out_css = os.path.join(out_dir, "style.css")
    shutil.copy2(yamagata_css, out_css)
    
    # 3. Update index.html
    yamagata_html = os.path.join(base_dir, "tools", "school-database", "yamagata", "index.html")
    out_html = os.path.join(out_dir, "index.html")
    with open(yamagata_html, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("yamagata", pref_en)
    html = html.replace("山形県", pref_ja)
    html = html.replace("山形", pref_ja.replace("県", ""))
    html = html.replace("学校宛先データベース", "全国学校データベース")
    
    # Update BOE URLs (replacing the yamagata ones)
    html = html.replace("https://www.pref.yamagata.jp/kyoiku/index.html", boe_url)
    html = html.replace("https://www.pref.yamagata.jp/bunkyo/kyoiku/iinkai/", boe_url)
    html = html.replace("https://www.pref.yamagata.jp/bunkyo/kyoiku/shigaku/", boe_url)
    
    with open(out_html, "w", encoding="utf-8", newline='\n') as f:
        f.write(html)

create_ui("aomori", "青森県", "02", "https://www.pref.aomori.lg.jp/")
create_ui("akita", "秋田県", "05", "https://www.pref.akita.lg.jp/")
print("Done creating UI files")
