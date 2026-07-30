import json
from collections import defaultdict

TARGETS = ["tokyo", "saitama", "chiba", "kanagawa", "fukushima", "miyagi"]
PREFECTURE_NAMES = {
    "tokyo": "東京都", "saitama": "埼玉県", "chiba": "千葉県", 
    "kanagawa": "神奈川県", "fukushima": "福島県", "miyagi": "宮城県"
}

def analyze_warnings():
    results = {}
    
    for slug in TARGETS:
        filepath = f"data/school-database/{slug}.json"
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        warnings = {
            "同名校": [],
            "学校名欠損": [],
            "設置区分欠損": [],
            "設置区分の想定外値": [],
            "自治体欠損": [],
            "校種欠損": [],
            "基準日欠損": [],
            "キー競合": [],
            "その他": []
        }
        
        seen_schools = defaultdict(list)
        
        for idx, row in enumerate(data):
            name1 = row.get("name")
            name2 = row.get("school_name")
            
            if name1 is not None and name2 is not None and name1 != name2:
                warnings["キー競合"].append(f"Name conflict: {name1} vs {name2}")
            
            name = name1 if name1 else name2
            if not name:
                warnings["学校名欠損"].append(f"Row {idx}")
                name = "Unknown"
                
            est1 = row.get("establishment")
            est2 = row.get("establishment_type")
            
            if est1 is not None and est2 is not None and est1 != est2:
                warnings["キー競合"].append(f"Est conflict: {est1} vs {est2}")
                
            est_raw = est1 if est1 else est2
            
            if not est_raw:
                warnings["設置区分欠損"].append(name)
                est_raw = "その他"
                
            if isinstance(est_raw, list):
                est = est_raw[0] if est_raw else "その他"
            else:
                est = est_raw
                
            if est not in ["国立", "公立", "私立"]:
                warnings["設置区分の想定外値"].append(f"{name} ({est})")
                
            muni = row.get("municipality")
            if not muni:
                warnings["自治体欠損"].append(name)
                
            stype = row.get("school_type")
            if not stype:
                warnings["校種欠損"].append(name)
                
            s_date = row.get("data_date") or row.get("source_date")
            if not s_date:
                warnings["基準日欠損"].append(name)
                
            # Check true duplicates
            key = (PREFECTURE_NAMES[slug], muni, name, stype, est)
            seen_schools[key].append(row)
            
        for key, rows in seen_schools.items():
            if len(rows) > 1:
                warnings["同名校"].append(f"{key} (Count: {len(rows)})")
                
        results[slug] = warnings
        
    for slug, w in results.items():
        print(f"--- {PREFECTURE_NAMES[slug]} ---")
        total_w = sum(len(v) for v in w.values())
        if total_w == 0:
            print("No warnings.")
            continue
        for k, v in w.items():
            if v:
                print(f"  {k}: {len(v)}件")
                for item in v[:3]:
                    print(f"    - {item}")
                if len(v) > 3:
                    print("    - ...")

if __name__ == "__main__":
    analyze_warnings()
