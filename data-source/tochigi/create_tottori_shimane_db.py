# -*- coding: utf-8 -*-
import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
template_file = os.path.join(base_dir, "tools", "school-database", "convert_yamagata_sources.py")

with open(template_file, "r", encoding="utf-8") as f:
    template = f.read()

def generate_script(pref_en, pref_ja, pref_code_str, mext_source, cities):
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

tottori = ["鳥取市", "米子市", "倉吉市", "境港市", "岩美町", "若桜町", "智頭町", "八頭町", "三朝町", "湯梨浜町", "琴浦町", "北栄町", "日吉津村", "大山町", "南部町", "伯耆町", "日南町", "日野町", "江府町"]
shimane = ["松江市", "浜田市", "出雲市", "益田市", "大田市", "安来市", "江津市", "雲南市", "奥出雲町", "飯南町", "川本町", "美郷町", "邑南町", "津和野町", "吉賀町", "海士町", "西ノ島町", "知夫村", "隠岐の島町"]

generate_script("tottori", "鳥取", "31", "sc_20260529-mxt_chousa01-000011635_3.xlsx", tottori)
generate_script("shimane", "島根", "32", "sc_20260529-mxt_chousa01-000011635_3.xlsx", shimane)
