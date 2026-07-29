import os

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
prefectures = ["ishikawa", "fukui", "shiga"]

for pref in prefectures:
    p = os.path.join(base_dir, f"tools/school-database/convert_{pref}_sources.py")
    text = open(p, encoding="utf-8").read()
    
    old_line = 'active = yama[yama["属性情報廃止年月日"].isna() | (yama["属性情報廃止年月日"] == "nan")]'
    new_line = '''
    col_name = "属性情報廃止年月日" if "属性情報廃止年月日" in yama.columns else "廃止年月日" if "廃止年月日" in yama.columns else None
    if col_name:
        active = yama[yama[col_name].isna() | (yama[col_name] == "nan")]
    else:
        active = yama
    '''
    
    text = text.replace(old_line, new_line)
    open(p, "w", encoding="utf-8", newline='\n').write(text)
