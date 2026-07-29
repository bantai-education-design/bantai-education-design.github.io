import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

def create_ui(pref_en, pref_ja, pref_code, boe_url):
    print(f"Creating UI for {pref_en} ({pref_ja})")
    
    # 1. Update index.html
    html_template_path = os.path.join(base_dir, "tools", "school-database", "yamagata", "index.html")
    with open(html_template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    html_content = html_content.replace('yamagata', pref_en)
    html_content = html_content.replace('Yamagata', pref_en.capitalize())
    html_content = html_content.replace('山形県', pref_ja)
    
    # Also update the BOE links inside HTML
    html_content = re.sub(
        r'<a class="edu-portal-card" href="[^"]+" target="_blank" rel="noopener noreferrer">\s*<span class="edu-portal-mark" aria-hidden="true">教</span>',
        f'<a class="edu-portal-card" href="{boe_url}" target="_blank" rel="noopener noreferrer">\n            <span class="edu-portal-mark" aria-hidden="true">教</span>',
        html_content
    )
    html_content = re.sub(
        r'<a class="edu-portal-card" href="[^"]+" target="_blank" rel="noopener noreferrer">\s*<span class="edu-portal-mark" aria-hidden="true">公</span>',
        f'<a class="edu-portal-card" href="{boe_url}" target="_blank" rel="noopener noreferrer">\n            <span class="edu-portal-mark" aria-hidden="true">公</span>',
        html_content
    )
    html_content = re.sub(
        r'<a class="edu-portal-card" href="[^"]+" target="_blank" rel="noopener noreferrer">\s*<span class="edu-portal-mark" aria-hidden="true">私</span>',
        f'<a class="edu-portal-card" href="{boe_url}" target="_blank" rel="noopener noreferrer">\n            <span class="edu-portal-mark" aria-hidden="true">私</span>',
        html_content
    )
    
    # 2. Create the directories and write files
    target_dir = os.path.join(base_dir, "tools", "school-database", pref_en)
    os.makedirs(target_dir, exist_ok=True)
        
    with open(os.path.join(target_dir, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html_content)

prefectures = [
    ("saga", "佐賀県", "41", "https://www.pref.saga.lg.jp/kiji00318029/index.html"),
    ("nagasaki", "長崎県", "42", "https://www.pref.nagasaki.jp/bunrui/kanko-kyoiku-bunka/kyoikuiinkai/"),
    ("kumamoto", "熊本県", "43", "https://www.pref.kumamoto.jp/site/kyouiku/"),
]

for p_en, p_ja, p_code, boe in prefectures:
    create_ui(p_en, p_ja, p_code, boe)

print("Done generating UI files.")
