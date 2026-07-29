import os
import shutil
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
prefectures = [
    ("ishikawa", "石川県", "17(石川)"),
    ("fukui", "福井県", "18(福井)"),
    ("shiga", "滋賀県", "25(滋賀)")
]

for pref_en, pref_ja, pref_code in prefectures:
    p = os.path.join(base_dir, f'tools/school-database/convert_{pref_en}_sources.py')
    shutil.copy2(os.path.join(base_dir, 'tools/school-database/convert_yamagata_sources.py'), p)
    
    text = open(p, encoding='utf-8').read()
    
    text = text.replace("yamagata", pref_en)
    text = text.replace("Yamagata", pref_en.capitalize())
    text = text.replace("山形県", pref_ja)
    text = text.replace("06(山形)", pref_code)
    text = text.replace("YAMAGATA_", f"{pref_en.upper()}_")
    
    # We need to replace the single file load with a multi-file load
    # Look for:
    #     excel_path = None
    #     for c in candidates:
    #         if c.exists():
    #             excel_path = c
    #             break
    # 
    #     if excel_path is None:
    #         warn("source_load", "MEXT Excel not found")
    #         return []
    # 
    #     print(f"Reading: {excel_path}")
    #     df = pd.read_excel(excel_path, header=1, dtype=str)
    #     df.columns = [c.replace('\n', '').strip() for c in df.columns]
    # 
    #     yama = df[df["都道府県番号"] == "17(石川)"].copy()

    # We will use regex to find the start of `candidates = ` and replace until `yama = df[...].copy()`
    
    replacement = f'''    import pandas as pd
    files = ['sc_20260529-mxt_chousa01-000011635_1.xlsx', 'sc_20260529-mxt_chousa01-000011635_3.xlsx', 'sc_20260529-mxt_chousa01-000011635_5.xlsx']
    df_list = []
    for f in files:
        file_p = Path('data-source/tochigi') / f
        if file_p.exists():
            print(f"Reading: {{file_p}}")
            df = pd.read_excel(file_p, header=1, dtype=str)
            # Remove newlines in column names
            df.columns = [c.replace('\\n', '').strip() for c in df.columns]
            df_list.append(df)

    if not df_list:
        warn("source_load", "MEXT Excel not found")
        return []
        
    df = pd.concat(df_list, ignore_index=True)
    yama = df[df["都道府県番号"] == "{pref_code}"].copy()'''

    text = re.sub(r'    candidates = \[.*?yama = df\[df\["都道府県番号"\] == ".*?"\]\.copy\(\)', replacement, text, flags=re.DOTALL)
    
    open(p, 'w', encoding='utf-8', newline='\n').write(text)
