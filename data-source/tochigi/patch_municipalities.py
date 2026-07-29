import os
import json
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
prefectures = [
    ("saga", "佐賀県", "41(佐賀)"),
    ("nagasaki", "長崎県", "42(長崎)"),
    ("kumamoto", "熊本県", "43(熊本)"),
]

def get_municipalities_from_excel(pref_code, pref_ja):
    import pandas as pd
    excel_path = os.path.join(base_dir, "data-source", "tochigi", "sc_20260529-mxt_chousa01-000011635_3.xlsx")
    df = pd.read_excel(excel_path, header=1, dtype=str)
    df.columns = [c.replace("\n", "").strip() for c in df.columns]
    yama = df[df["都道府県番号"] == pref_code].copy()
    
    cities = set()
    gun_towns = set()
    
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
        
    # Replace the SAGA_CITIES array
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
