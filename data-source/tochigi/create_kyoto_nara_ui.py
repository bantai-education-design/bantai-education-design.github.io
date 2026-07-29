import os

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

def create_ui(pref_en, pref_ja, pref_code, boe_url):
    print(f"Creating UI for {pref_en} ({pref_ja})")
    
    # 1. Update search.js
    js_template_path = os.path.join(base_dir, "assets", "js", "school-database", "search-yamagata.js")
    js_out_path = os.path.join(base_dir, "assets", "js", "school-database", f"search-{pref_en}.js")
    with open(js_template_path, "r", encoding="utf-8") as f:
        js_content = f.read()
    js_content = js_content.replace("yamagata", pref_en)
    with open(js_out_path, "w", encoding="utf-8", newline='\n') as f:
        f.write(js_content)
        
    # 2. Update index.html
    html_template_path = os.path.join(base_dir, "tools", "school-database", "yamagata", "index.html")
    pref_dir = os.path.join(base_dir, "tools", "school-database", pref_en)
    os.makedirs(pref_dir, exist_ok=True)
    html_out_path = os.path.join(pref_dir, "index.html")
    with open(html_template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # We replace yamagata with pref_en and 山形 with pref_ja
    html_content = html_content.replace("yamagata", pref_en)
    html_content = html_content.replace("山形", pref_ja)
    
    # Update BOE URL
    html_content = html_content.replace("https://www.pref.yamagata.jp/ou/kyoiku/index.html", boe_url)
    
    with open(html_out_path, "w", encoding="utf-8", newline='\n') as f:
        f.write(html_content)

create_ui("kyoto", "京都", "26", "https://www.kyoto-be.ne.jp/")
create_ui("nara", "奈良", "29", "https://www.pref.nara.jp/1498.htm")
