import json
import re

path = "data/school-database/hiroshima.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

def slug(text: str) -> str:
    # A simple slugifier to match whatever was used in convert_hiroshima_sources.py
    import urllib.parse
    return urllib.parse.quote(text.replace(" ", "-"))

MUNICIPAL_HIGHS = {
    "基町", "舟入", "広島みらい創生", "広島商業", "広島工業", "沼田", "美鈴が丘",
    "広島中等教育", "安佐北", "呉", "福山", "福山中・高"
}

changed = 0
for row in data:
    if row.get("school_type") == "高等学校" and row.get("establishment") == "公立":
        name = row["name"]
        if "立" in name:
            idx = name.index("立")
            raw_name = name[idx+1:]
            
            raw_core = raw_name.replace("高等学校", "")
            if raw_core in MUNICIPAL_HIGHS:
                if raw_core == "呉":
                    correct_prefix = "呉市"
                elif raw_core == "福山" or raw_core == "福山中・高":
                    correct_prefix = "福山市"
                else:
                    correct_prefix = "広島市"
                
                correct_name = f"{correct_prefix}立{raw_name}"
            else:
                correct_name = f"広島県立{raw_name}"
                
            if name != correct_name:
                row["name"] = correct_name
                changed += 1

for row in data:
    if row["name"] == "広島市立広島商業高等学校":
        if "南区" in row["address"]:
            row["name"] = "広島県立広島商業高等学校"
            
    if row["name"] == "広島市立広島工業高等学校":
        if "出汐" in row["address"]:
            row["name"] = "広島県立広島工業高等学校"

# Fix IDs
counts = {}
for row in data:
    base = slug(f"hiroshima-{row['establishment']}-{row['school_type']}-{row['municipality']}-{row['name']}")
    counts[base] = counts.get(base, 0) + 1
    row["id"] = base if counts[base] == 1 else f"{base}-{counts[base]}"

with open(path, "w", encoding="utf-8", newline='\n') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Fixed {changed} high schools.")
