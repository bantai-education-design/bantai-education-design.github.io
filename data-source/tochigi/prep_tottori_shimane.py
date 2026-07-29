# -*- coding: utf-8 -*-
import os
import pandas as pd

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
mext_file = os.path.join(base_dir, "data-source", "tochigi", "sc_20260529-mxt_chousa01-000011635_3.xlsx")
template_file = os.path.join(base_dir, "tools", "school-database", "convert_yamagata_sources.py")

print("Reading MEXT file:", mext_file)
df = pd.read_excel(mext_file, dtype=str, skiprows=1)

# column 2 is Prefecture code (e.g. "31(鳥取県)")
# column 4 is City code (e.g. "31201(鳥取市)")

tottori_cities_raw = df[df.iloc[:, 2].fillna("").str.startswith("31(")].iloc[:, 4].dropna().unique().tolist()
shimane_cities_raw = df[df.iloc[:, 2].fillna("").str.startswith("32(")].iloc[:, 4].dropna().unique().tolist()

def clean_city_name(raw):
    # raw looks like "31201(鳥取市)"
    # we want to extract what's inside the parentheses
    if "(" in raw and ")" in raw:
        return raw.split("(")[1].split(")")[0]
    return raw

tottori_cities = [clean_city_name(c) for c in tottori_cities_raw]
shimane_cities = [clean_city_name(c) for c in shimane_cities_raw]

def split_cities_guns(cities):
    guns = [c for c in cities if c.endswith("郡")]
    real_cities = [c for c in cities if not c.endswith("郡")]
    # Strip 郡 prefix logic for mapping. Wait, my convert_xxx_sources.py handles mapping internally now.
    return real_cities, guns

tottori_c, tottori_g = split_cities_guns(tottori_cities)
shimane_c, shimane_g = split_cities_guns(shimane_cities)

print("Tottori cities:", len(tottori_c), tottori_c)
print("Tottori guns:", len(tottori_g), tottori_g)
print("Shimane cities:", len(shimane_c), shimane_c)
print("Shimane guns:", len(shimane_g), shimane_g)

with open(template_file, "r", encoding="utf-8") as f:
    template = f.read()

def generate_script(pref_en, pref_ja, pref_code_str, mext_source, cities, guns):
    script = template
    # Update MEXT source file
    script = script.replace('sc_20260529-mxt_chousa01-000011635_1.xlsx', mext_source)
    # Update prefecture matching (Yamagata was "06(")
    script = script.replace('pref_val.startswith("06(")', f'pref_val.startswith("{pref_code_str}(")')
    
    # Update file paths
    script = script.replace('yamagata', pref_en)
    
    # Replace CITY/GUN arrays
    # Find CITY_LIST = [...] and GUN_LIST = [...]
    import re
    script = re.sub(r'CITY_LIST = \[.*?\]', f'CITY_LIST = {cities}', script, flags=re.DOTALL)
    script = re.sub(r'GUN_LIST = \[.*?\]', f'GUN_LIST = {guns}', script, flags=re.DOTALL)
    
    out_path = os.path.join(base_dir, "tools", "school-database", f"convert_{pref_en}_sources.py")
    with open(out_path, "w", encoding="utf-8", newline='\n') as f:
        f.write(script)
    print(f"Generated {out_path}")

generate_script("tottori", "鳥取", "31", "sc_20260529-mxt_chousa01-000011635_3.xlsx", tottori_c, tottori_g)
generate_script("shimane", "島根", "32", "sc_20260529-mxt_chousa01-000011635_3.xlsx", shimane_c, shimane_g)

