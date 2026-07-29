import os
import re
import urllib.request
import urllib.parse
import json

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
template_file = os.path.join(base_dir, "tools", "school-database", "convert_yamagata_sources.py")

with open(template_file, "r", encoding="utf-8") as f:
    template = f.read()

def fetch_cities(pref):
    url = f"https://geoapi.heartrails.com/api/json?method=getCities&prefecture={urllib.parse.quote(pref)}"
    res = urllib.request.urlopen(url)
    data = json.loads(res.read())
    return [c["city"] for c in data["response"]["location"]]

def generate_script(pref_en, pref_ja, pref_code_str, mext_source):
    cities = fetch_cities(f"{pref_ja}県")
    script = template
    # Update MEXT source file
    script = script.replace('sc_20260529-mxt_chousa01-000011635_1.xlsx', mext_source)
    
    # Update pandas filter
    script = script.replace('df[df["都道府県番号"] == "06(山形)"].copy()', f'df[df["都道府県番号"].fillna("").str.startswith("{pref_code_str}(")].copy()')
    
    # Update file paths
    script = script.replace('yamagata', pref_en)
    
    # Remove everything from YAMAGATA_CITIES = [ down to def fetch_all_institutions():
    script = re.sub(r'YAMAGATA_CITIES = \[.*?def fetch_all_institutions', f"""
import re

{pref_en.upper()}_CITIES = {cities}
{pref_en.upper()}_ORDER = sorted({pref_en.upper()}_CITIES, key=len, reverse=True)

def infer_municipality(address: str) -> str:
    text = address
    if text.startswith("{pref_ja}県"):
        text = text[len("{pref_ja}県"):]
    # Remove Gun name (anything up to 郡)
    text = re.sub(r'^.+?郡', '', text)
    for cand in {pref_en.upper()}_ORDER:
        if text.startswith(cand):
            return cand
    return ""

def fetch_all_institutions""", script, flags=re.DOTALL)
    
    out_path = os.path.join(base_dir, "tools", "school-database", f"convert_{pref_en}_sources.py")
    with open(out_path, "w", encoding="utf-8", newline='\n') as f:
        f.write(script)
    print(f"Generated {out_path}")

# generate_script("gunma", "群馬", "10", "sc_20260529-mxt_chousa01-000011635_1.xlsx")
generate_script("shizuoka", "静岡", "22", "sc_20260529-mxt_chousa01-000011635_1.xlsx")
