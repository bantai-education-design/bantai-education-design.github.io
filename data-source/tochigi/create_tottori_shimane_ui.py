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
        
    # 2. Update index.html
    yamagata_html = os.path.join(base_dir, "tools", "school-database", "yamagata", "index.html")
    out_dir = os.path.join(base_dir, "tools", "school-database", pref_en)
    os.makedirs(out_dir, exist_ok=True)
    out_html = os.path.join(out_dir, "index.html")
    with open(yamagata_html, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("yamagata", pref_en)
    html = html.replace("山形県", pref_ja)
    html = html.replace("山形", pref_ja.replace("県", ""))
    html = html.replace("学校宛先データベース", "全国学校データベース")
    
    # Update BOE URLs (replacing the yamagata ones inside the template, assuming they were set to something.
    # Wait, in the yamagata template, they might be kyoiku.pref.yamagata.jp!
    # Let's replace ALL the portal cards with the boe_url
    
    import re
    # We find all <a class="edu-portal-card" href="..."> and replace the href
    html = re.sub(r'(<a class="edu-portal-card"[^>]*?href=")[^"]*(")', r'\g<1>' + boe_url + r'\g<2>', html)
    
    with open(out_html, "w", encoding="utf-8", newline='\n') as f:
        f.write(html)

create_ui("tottori", "鳥取県", "31", "https://www.pref.tottori.lg.jp/")
create_ui("shimane", "島根県", "32", "https://www.pref.shimane.lg.jp/")
print("Done creating UI files")
