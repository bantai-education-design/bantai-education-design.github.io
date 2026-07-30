import os
import glob
import pandas as pd
import json
import re

prefs_info = [
    {"en": "wakayama", "ja": "和歌山県", "code": "30(和歌山)"},
    {"en": "oita", "ja": "大分県", "code": "44(大分)"},
    {"en": "miyazaki", "ja": "宮崎県", "code": "45(宮崎)"},
    {"en": "kagoshima", "ja": "鹿児島県", "code": "46(鹿児島)"}
]

DATA_DIR = "data-source/tochigi"

files = [
    "sc_20260529-mxt_chousa01-000011635_1.xlsx",
    "sc_20260529-mxt_chousa01-000011635_3.xlsx",
    "sc_20260529-mxt_chousa01-000011635_5.xlsx"
]

TYPE_MAPPING = {
    "A1(幼稚園)": "幼稚園",
    "B1(小学校)": "小学校",
    "C1(中学校)": "中学校",
    "C2(義務)": "義務教育学校",
    "D1(高校)": "高等学校",
    "D2(中等)": "中等教育学校",
    "E1(特支盲)": "特別支援学校",
    "E1(特支聾)": "特別支援学校",
    "E1(養護)": "特別支援学校",
}

ESTABLISHMENT_MAPPING = {
    "1(国)": "国立",
    "2(公)": "公立",
    "3(私)": "私立",
}

def normalize_name(text):
    if pd.isna(text): return ""
    text = str(text).replace("\n", "").replace("\r", "")
    text = re.sub(r"[ \t　]+", "", text)
    return text.strip()

for p in prefs_info:
    print(f"Processing {p['ja']}...")
    all_schools = []
    
    for fname in files:
        file_path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(file_path):
            print(f"Missing {file_path}")
            continue
            
        df = pd.read_excel(file_path, header=1, dtype=str)
        df.columns = [c.replace("\n", "").strip() for c in df.columns]
        
        pref_col = "都道府県番号"
        if pref_col not in df.columns:
            continue
            
        df_pref = df[df[pref_col] == p['code']]
        
        # 廃止校を除外
        col_name = "属性情報廃止年月日" if "属性情報廃止年月日" in df.columns else "廃止年月日" if "廃止年月日" in df.columns else None
        if col_name:
            df_pref = df_pref[df_pref[col_name].isna() | (df_pref[col_name] == "nan") | (df_pref[col_name] == "")]
        
        for _, row in df_pref.iterrows():
            raw_type = str(row.get("学校種", "")).strip()
            raw_est = str(row.get("設置区分", "")).strip()

            if raw_type not in TYPE_MAPPING or raw_est not in ESTABLISHMENT_MAPPING:
                continue

            school_type = TYPE_MAPPING[raw_type]
            est_type = ESTABLISHMENT_MAPPING[raw_est]
            
            raw_name = normalize_name(row.get("学校名", ""))
            raw_addr = normalize_name(row.get("学校所在地", ""))
            raw_postal = str(row.get("郵便番号", ""))
            
            if not raw_name or not raw_addr:
                continue
                
            municipality = ""
            addr_no_pref = raw_addr
            if addr_no_pref.startswith(p['ja']):
                addr_no_pref = addr_no_pref[len(p['ja']):]
                
            m = re.match(r'^([^郡]+市|[^郡]+区|.+?郡.+?[町村]|.+?[町村])', addr_no_pref)
            if m:
                municipality = m.group(1)
            else:
                m2 = re.match(r'^([^市]+市|[^区]+区|[^町]+町|[^村]+村)', addr_no_pref)
                if m2:
                    municipality = m2.group(1)
            
            # Simple official name logic
            already_complete = any(raw_name.endswith(s) for s in ["幼稚園", "小学校", "中学校", "義務教育学校", "高等学校", "中等教育学校", "特別支援学校", "学園", "分校", "分教室"])
            
            official_name = raw_name
            if est_type == "公立":
                if not re.search(r'[都道府県市区町村]立', raw_name):
                    if school_type in ["高等学校", "中等教育学校", "特別支援学校"]:
                        official_name = f"{p['ja']}立{raw_name}"
                    else:
                        bare_muni = re.sub(r"^.+郡", "", municipality)
                        official_name = f"{bare_muni}立{raw_name}"
            
            if not already_complete:
                official_name += school_type
                
            all_schools.append({
                "id": f"{p['en']}-{len(all_schools)}",
                "prefecture": p['ja'],
                "name": official_name,
                "name_kana": "",
                "postal_code": raw_postal,
                "address": raw_addr,
                "municipality": municipality,
                "school_type": school_type,
                "establishment": est_type,
                "operator": "",
                "phone": "",
                "website": "",
                "source_name": "文部科学省",
                "source_url": "",
                "source_date": "2026-05-29",
                "course": []
            })
            
    # Save to JSON
    out_dir = "data/school-database"
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{p['en']}.json"), "w", encoding="utf-8") as f:
        json.dump(all_schools, f, ensure_ascii=False, indent=2)
        
    print(f"Generated {len(all_schools)} schools for {p['ja']}")
