import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
js_template_path = os.path.join(base_dir, "assets", "js", "school-database", "search-yamagata.js")

prefectures = [
    ("saga", "佐賀県"),
    ("nagasaki", "長崎県"),
    ("kumamoto", "熊本県"),
]

with open(js_template_path, "r", encoding="utf-8") as f:
    js_template = f.read()

for pref_en, pref_ja in prefectures:
    js_out_path = os.path.join(base_dir, "assets", "js", "school-database", f"search-{pref_en}.js")
    js_content = js_template.replace("yamagata", pref_en)
    with open(js_out_path, "w", encoding="utf-8", newline='\n') as f:
        f.write(js_content)
    print(f"Created {js_out_path}")

# Fix Saga BOE link
saga_html_path = os.path.join(base_dir, "tools", "school-database", "saga", "index.html")
with open(saga_html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

html_content = html_content.replace(
    "https://www.pref.saga.lg.jp/kiji00318029/index.html", 
    "https://www.pref.saga.lg.jp/kyouiku/"
)

with open(saga_html_path, "w", encoding="utf-8", newline='\n') as f:
    f.write(html_content)
print(f"Updated Saga BOE link in {saga_html_path}")

