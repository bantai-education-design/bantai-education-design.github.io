import os
import json
import re
import pandas as pd

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
prefectures = [
    ("ishikawa", "石川県", "17(石川)"),
    ("fukui", "福井県", "18(福井)"),
    ("shiga", "滋賀県", "25(滋賀)")
]

def get_municipalities_from_excel(pref_code, pref_ja):
    excel_candidates = [
        "sc_20260529-mxt_chousa01-000011635_1.xlsx",
        "sc_20260529-mxt_chousa01-000011635_3.xlsx",
        "sc_20260529-mxt_chousa01-000011635_5.xlsx"
    ]
    
    cities = set()
    gun_towns = set()
    
    for fname in excel_candidates:
        excel_path = os.path.join(base_dir, "data-source", "tochigi", fname)
        if not os.path.exists(excel_path):
            continue
        df = pd.read_excel(excel_path, header=1, dtype=str)
        df.columns = [c.replace("\n", "").strip() for c in df.columns]
        yama = df[df["都道府県番号"] == pref_code].copy()
        
        for addr in yama["学校所在地"].dropna():
            addr = addr.replace(" ", "").replace("　", "")
            if addr.startswith(pref_ja):
                addr = addr[len(pref_ja):]
                
            m = re.match(r'^(.*?市|.*?郡.+?[町村])', addr)
            if m:
                muni = m.group(1)
                if "市" in muni and not "郡" in muni:
                    cities.add(muni)
                else:
                    gun_towns.add(muni)
                    
    return sorted(list(cities)), sorted(list(gun_towns))

for pref_en, pref_ja, pref_code in prefectures:
    cities, gun_towns = get_municipalities_from_excel(pref_code, pref_ja)
    print(f"{pref_ja} cities:", cities)
    print(f"{pref_ja} gun_towns:", gun_towns)
    
    cities_str = ", ".join(f'"{c}"' for c in cities)
    gun_towns_str = ", ".join(f'"{g}"' for g in gun_towns)
    
    script_path = os.path.join(base_dir, "tools", "school-database", f"convert_{pref_en}_sources.py")
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Replace the CITIES array
    content = re.sub(
        r'[A-Z]+_CITIES = \[.*?\]',
        f'{pref_en.upper()}_CITIES = [\n    {cities_str}\n]',
        content,
        flags=re.DOTALL
    )
    
    content = re.sub(
        r'[A-Z]+_GUN_TOWNS = \[.*?\]',
        f'{pref_en.upper()}_GUN_TOWNS = [\n    {gun_towns_str}\n]',
        content,
        flags=re.DOTALL
    )
    
    with open(script_path, "w", encoding="utf-8", newline='\n') as f:
        f.write(content)
