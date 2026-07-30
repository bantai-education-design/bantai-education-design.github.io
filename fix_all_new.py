import os
import re

prefs = {
    "toyama": "https://www.pref.toyama.jp/",
    "kagawa": "https://www.pref.kagawa.lg.jp/",
    "tokushima": "https://www.pref.tokushima.lg.jp/",
    "ehime": "https://www.pref.ehime.jp/",
    "kochi": "https://www.pref.kochi.lg.jp/"
}

for pref, url in prefs.items():
    pref_html_path = f"tools/school-database/{pref}/index.html"
    if os.path.exists(pref_html_path):
        with open(pref_html_path, "r", encoding="utf-8") as f:
            p_html = f.read()
        
        # Replace the URL in the edu-portal-card anchor
        p_html = re.sub(r'(<a class="edu-portal-card" href=")[^"]+(" target="_blank" rel="noopener noreferrer">)', r'\g<1>' + url + r'\g<2>', p_html)
        
        with open(pref_html_path, "w", encoding="utf-8") as f:
            f.write(p_html)

print("URLs updated with edu-portal-card regex.")
