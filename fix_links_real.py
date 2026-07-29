import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io\tools\school-database"

# Format: (pref_en, link1, link2, link3)
data = [
    ("tottori", "https://www.pref.tottori.lg.jp/kyoiku/", "https://www.pref.tottori.lg.jp/177062.htm", "https://www.pref.tottori.lg.jp/265691.htm"),
    ("shimane", "https://www.pref.shimane.lg.jp/education/", "https://www.pref.shimane.lg.jp/education/kyoiku/kikaku/gakkou_jouhou/juusyoroku.html", "https://www.pref.shimane.lg.jp/education/kyoiku/shigaku/"),
    ("shizuoka", "https://www.pref.shizuoka.jp/kyouiku/", "https://www.pref.shizuoka.jp/kyouiku/", "https://www.pref.shizuoka.jp/kyouiku/"),
    ("gunma", "https://www.pref.gunma.jp/soshiki/222/", "https://www.pref.gunma.jp/soshiki/222/", "https://www.pref.gunma.jp/soshiki/222/"),
    ("kyoto", "https://www.kyoto-be.ne.jp/", "https://www.kyoto-be.ne.jp/", "https://www.pref.kyoto.jp/shigaku/meibo.html"),
    ("nara", "https://www.pref.nara.jp/1498.htm", "https://www.pref.nara.jp/1498.htm", "https://www.pref.nara.jp/1498.htm"),
]

for pref_en, l1, l2, l3 in data:
    html_path = os.path.join(base_dir, pref_en, "index.html")
    if not os.path.exists(html_path):
        continue
        
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. BOE Link
    content = re.sub(
        r'<a class="edu-portal-card" href="https://www\.google\.com/search\?q=[^"]+" target="_blank" rel="noopener noreferrer">\s*<span class="edu-portal-mark" aria-hidden="true">教</span>',
        f'<a class="edu-portal-card" href="{l1}" target="_blank" rel="noopener noreferrer">\n            <span class="edu-portal-mark" aria-hidden="true">教</span>',
        content
    )
    
    # 2. Public Schools Link
    content = re.sub(
        r'<a class="edu-portal-card" href="https://www\.google\.com/search\?q=[^"]+" target="_blank" rel="noopener noreferrer">\s*<span class="edu-portal-mark" aria-hidden="true">公</span>',
        f'<a class="edu-portal-card" href="{l2}" target="_blank" rel="noopener noreferrer">\n            <span class="edu-portal-mark" aria-hidden="true">公</span>',
        content
    )
    
    # 3. Private Schools Link
    content = re.sub(
        r'<a class="edu-portal-card" href="https://www\.google\.com/search\?q=[^"]+" target="_blank" rel="noopener noreferrer">\s*<span class="edu-portal-mark" aria-hidden="true">私</span>',
        f'<a class="edu-portal-card" href="{l3}" target="_blank" rel="noopener noreferrer">\n            <span class="edu-portal-mark" aria-hidden="true">私</span>',
        content
    )
    
    with open(html_path, "w", encoding="utf-8", newline='\n') as f:
        f.write(content)
    
    print(f"Updated {pref_en}")
