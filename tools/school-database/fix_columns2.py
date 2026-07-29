import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
prefectures = ["ishikawa", "fukui", "shiga"]

for pref in prefectures:
    p = os.path.join(base_dir, f"tools/school-database/convert_{pref}_sources.py")
    text = open(p, encoding="utf-8").read()
    
    # We will replace `df_list.append(df)` with stripping logic and append
    
    old_str = "            df_list.append(df)"
    new_str = '            df.columns = [c.replace("\\n", "").strip() for c in df.columns]\n            df_list.append(df)'
    
    if 'df.columns = [c.replace("\\n", "").strip()' not in text:
        text = text.replace(old_str, new_str)
        open(p, "w", encoding="utf-8", newline='\n').write(text)
        print(f"Fixed {pref}")
    else:
        print(f"Already fixed {pref}")
