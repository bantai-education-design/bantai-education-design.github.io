import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
p = os.path.join(base_dir, f"tools/school-database/convert_hyogo_sources.py")

new_load_mext_data = '''def load_mext_data(source_root: Path) -> list[dict[str, Any]]:
    import pandas as pd
    
    files = [
        "sc_20260529-mxt_chousa01-000011635_1.xlsx",
        "sc_20260529-mxt_chousa01-000011635_3.xlsx",
        "sc_20260529-mxt_chousa01-000011635_5.xlsx"
    ]
    
    df_list = []
    for f in files:
        file_p = source_root / f
        if file_p.exists():
            print(f"Reading: {file_p}")
            df = pd.read_excel(file_p, header=1, dtype=str)
            df.columns = [str(c).replace("\\n", "").strip() for c in df.columns]
            df_list.append(df)
            
    if not df_list:
        warn("source_load", "MEXT Excel files not found")
        return []
        
    df = pd.concat(df_list, ignore_index=True)
    
    col_name = "属性変更・廃止年月日" if "属性変更・廃止年月日" in df.columns else "廃止年月日" if "廃止年月日" in df.columns else None
    if col_name:
        active = df[df[col_name].isna() | (df[col_name] == "nan")]
    else:
        active = df

'''

with open(p, "r", encoding="utf-8") as f:
    text = f.read()

pattern = re.compile(r'def load_mext_data.*?for idx, row in active.iterrows():', re.DOTALL)
text = pattern.sub(new_load_mext_data + '    for idx, row in active.iterrows():', text)

with open(p, "w", encoding="utf-8", newline='\n') as f:
    f.write(text)

print("Applied load_mext_data fix for Hyogo.")
