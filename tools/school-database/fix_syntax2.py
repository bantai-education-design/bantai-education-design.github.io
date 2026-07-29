import os
import shutil
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
prefectures = [
    ("ishikawa", "17(石川)"),
    ("fukui", "18(福井)"),
    ("shiga", "25(滋賀)")
]

replacement = '''def load_mext_data(source_root: Path) -> list[dict[str, Any]]:
    import pandas as pd
    files = ['sc_20260529-mxt_chousa01-000011635_1.xlsx', 'sc_20260529-mxt_chousa01-000011635_3.xlsx', 'sc_20260529-mxt_chousa01-000011635_5.xlsx']
    df_list = []
    for f in files:
        p = Path('data-source/tochigi') / f
        if p.exists():
            print(f'Reading: {p}')
            df = pd.read_excel(p, header=1, dtype=str)
            df.columns = [c.replace("\\n", "").strip() for c in df.columns]
            df_list.append(df)
    
    if not df_list:
        warn("source_load", "MEXT Excel not found")
        return []
        
    df = pd.concat(df_list, ignore_index=True)

    yama = df[df["都道府県番号"] == "PREF_CODE"].copy()
'''

for pref, pcode in prefectures:
    p = os.path.join(base_dir, f'tools/school-database/convert_{pref}_sources.py')
    text = open(p, encoding='utf-8').read()
    
    # Remove the broken lines and replace everything up to `yama = ...`
    text = re.sub(r'def load_mext_data.*?(# 廃止校を除外)', replacement.replace("PREF_CODE", pcode) + '\n    \\1', text, flags=re.DOTALL)
    
    open(p, 'w', encoding='utf-8', newline='\n').write(text)
