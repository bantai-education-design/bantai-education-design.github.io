import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
template_file = os.path.join(base_dir, "tools", "school-database", "convert_yamagata_sources.py")

with open(template_file, "r", encoding="utf-8") as f:
    template = f.read()

template = re.sub(r'sc_20260529-mxt_chousa01-000011635_1\.xlsx', r'sc_20260529-mxt_chousa01-000011635_3.xlsx', template)

prefectures = [
    ("saga", "佐賀県", "41(佐賀)"),
    ("nagasaki", "長崎県", "42(長崎)"),
    ("kumamoto", "熊本県", "43(熊本)"),
]

for pref_en, pref_ja, pref_code in prefectures:
    content = template.replace('yamagata', pref_en).replace('yamagata'.upper(), pref_en.upper())
    content = content.replace('山形県', pref_ja)
    
    # Use regex to be safe about quotes
    content = re.sub(r'["\']06\(山形\)["\']', f'"{pref_code}"', content)

    script_path = os.path.join(base_dir, "tools", "school-database", f"convert_{pref_en}_sources.py")
    with open(script_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    
    print(f"Created script for {pref_ja}")
