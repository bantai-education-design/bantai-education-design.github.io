import os
import shutil

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
tools_dir = os.path.join(base_dir, "tools", "school-database")

chugoku_prefs = [
    {"en": "tottori", "ja": "鳥取県", "url": "https://www.pref.tottori.lg.jp/kyouiku/"},
    {"en": "shimane", "ja": "島根県", "url": "https://www.pref.shimane.lg.jp/education/"},
    {"en": "okayama", "ja": "岡山県", "url": "https://www.pref.okayama.jp/site/16/"},
    {"en": "yamaguchi", "ja": "山口県", "url": "https://www.pref.yamaguchi.lg.jp/sec/5000.html"}
]

# 1. Generate conversion scripts based on Fukui template
with open(os.path.join(tools_dir, "convert_fukui_sources.py"), "r", encoding="utf-8") as f:
    template_py = f.read()

for pref in chugoku_prefs:
    script_content = template_py.replace("fukui", pref["en"])
    script_content = script_content.replace("福井県", pref["ja"])
    # We will patch MUNICIPALITIES later
    out_py = os.path.join(tools_dir, f"convert_{pref['en']}_sources.py")
    with open(out_py, "w", encoding="utf-8", newline='\n') as f:
        f.write(script_content)

print("Generated python scripts.")

# 2. Generate frontend HTML based on Fukui template
fukui_html_dir = os.path.join(tools_dir, "fukui")
with open(os.path.join(fukui_html_dir, "index.html"), "r", encoding="utf-8") as f:
    template_html = f.read()

for pref in chugoku_prefs:
    pref_dir = os.path.join(tools_dir, pref["en"])
    os.makedirs(pref_dir, exist_ok=True)
    html_content = template_html.replace("fukui", pref["en"])
    html_content = html_content.replace("福井県", pref["ja"])
    
    # Replace URLs
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

print("Generated HTML pages.")

# 3. Generate JS Search Scripts based on Fukui template
js_dir = os.path.join(base_dir, "assets", "js", "school-database")
with open(os.path.join(js_dir, "search-fukui.js"), "r", encoding="utf-8") as f:
    template_js = f.read()

for pref in chugoku_prefs:
    js_content = template_js.replace("fukui", pref["en"]).replace("福井県", pref["ja"])
    out_js = os.path.join(js_dir, f"search-{pref['en']}.js")
    with open(out_js, "w", encoding="utf-8", newline='\n') as f:
        f.write(js_content)

print("Generated JS files.")
