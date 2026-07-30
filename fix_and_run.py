import os
import subprocess

prefs = [
    {"en": "toyama", "code_str": "16(富山)"},
    {"en": "tokushima", "code_str": "36(徳島)"},
    {"en": "ehime", "code_str": "38(愛媛)"},
    {"en": "kochi", "code_str": "39(高知)"}
]

for pref in prefs:
    py_path = f"tools/school-database/convert_{pref['en']}_sources.py"
    with open(py_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # It currently says "18(富山)", "18(徳島)" etc.
    # Replace anything matching 'df["都道府県番号"] == "XX(NAME)"'
    # Actually just replace '"18(' + pref['ja'] + ')"' or similar.
    # The safest way is to regex replace:
    import re
    content = re.sub(r'df\["都道府県番号"\] == "[0-9]+\([^)]+\)"', f'df["都道府県番号"] == "{pref["code_str"]}"', content)
    
    # Wait, the source data directory is STILL "data-source/tochigi" because that's what the template had.
    # But wait, MEXT data IS in `data-source/tochigi`?
    # Yes, I checked earlier and `data-source/tochigi` contains the NATIONWIDE files `sc_20260529-mxt_chousa01-000011635_1.xlsx` etc.
    
    with open(py_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Fixed prefecture codes. Now running scripts...")

# Run them
for pref in prefs:
    print(f"Running {pref['en']}...")
    subprocess.run(["python", f"tools/school-database/convert_{pref['en']}_sources.py"], env=os.environ)

print("All extractions completed.")
