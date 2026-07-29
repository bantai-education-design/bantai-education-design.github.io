import os
import re
import urllib.parse

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io\tools\school-database"
prefs = [
    ("tottori", "鳥取県"),
    ("shimane", "島根県"),
    ("shizuoka", "静岡県"),
    ("gunma", "群馬県"),
    ("kyoto", "京都府"),
    ("nara", "奈良県")
]

for pref_en, pref_ja in prefs:
    html_path = os.path.join(base_dir, pref_en, "index.html")
    if not os.path.exists(html_path):
        continue
        
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. BOE Link
    q1 = urllib.parse.quote(f"{pref_ja} 教育委員会")
    content = re.sub(
        r'<a class="edu-portal-card" href="https://kyoiku\.pref\.[^"]+" target="_blank" rel="noopener noreferrer">\s*<span class="edu-portal-mark" aria-hidden="true">教</span>',
        f'<a class="edu-portal-card" href="https://www.google.com/search?q={q1}" target="_blank" rel="noopener noreferrer">\n            <span class="edu-portal-mark" aria-hidden="true">教</span>',
        content
    )
    
    # 2. Public Schools Link
    q2 = urllib.parse.quote(f"{pref_ja} 公立学校一覧")
    content = re.sub(
        r'<a class="edu-portal-card" href="https://kyoiku\.pref\.[^"]+/about/survey/school-list/" target="_blank" rel="noopener noreferrer">\s*<span class="edu-portal-mark" aria-hidden="true">公</span>',
        f'<a class="edu-portal-card" href="https://www.google.com/search?q={q2}" target="_blank" rel="noopener noreferrer">\n            <span class="edu-portal-mark" aria-hidden="true">公</span>',
        content
    )
    
    # 3. Private Schools Link
    q3 = urllib.parse.quote(f"{pref_ja} 私立学校")
    content = re.sub(
        r'<a class="edu-portal-card" href="https://kyoiku\.pref\.[^"]+/gakko/private-schools/" target="_blank" rel="noopener noreferrer">\s*<span class="edu-portal-mark" aria-hidden="true">私</span>',
        f'<a class="edu-portal-card" href="https://www.google.com/search?q={q3}" target="_blank" rel="noopener noreferrer">\n            <span class="edu-portal-mark" aria-hidden="true">私</span>',
        content
    )
    
    with open(html_path, "w", encoding="utf-8", newline='\n') as f:
        f.write(content)
    
    print(f"Updated {pref_en}")
