import os
import json
from glob import glob
from datetime import datetime

DATA_DIR = "data/school-database"
OUTPUT_FILE = os.path.join(DATA_DIR, "prefectures_meta.json")

def generate_meta():
    meta = {}
    json_files = glob(os.path.join(DATA_DIR, "*.json"))
    
    for fpath in json_files:
        basename = os.path.basename(fpath)
        if basename in ["prefectures.json", "prefectures_meta.json", "prefecture-statistics.json"]:
            continue
            
        slug = basename.replace(".json", "")
        
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            continue
            
        if not isinstance(data, list) or len(data) == 0:
            continue
            
        total_schools = len(data)
        municipalities = set()
        est_counts = {"公立": 0, "私立": 0, "国立": 0, "組合立": 0, "株式会社立": 0}
        type_counts = {"幼稚園": 0, "認定こども園": 0, "小学校": 0, "中学校": 0, "義務教育学校": 0, "高等学校": 0, "中等教育学校": 0, "特別支援学校": 0}
        
        # Determine the most common data_date
        dates = {}
        for row in data:
            if "municipality" in row and row["municipality"]:
                municipalities.add(row["municipality"])
            
            est = row.get("establishment_type", "不明")
            if est in est_counts:
                est_counts[est] += 1
            else:
                est_counts[est] = 1
                
            stype = row.get("school_type", "不明")
            if stype in type_counts:
                type_counts[stype] += 1
            elif "こども園" in stype:
                type_counts["認定こども園"] += 1
            elif "特別支援" in stype:
                type_counts["特別支援学校"] += 1
            else:
                if "その他" not in type_counts:
                    type_counts["その他"] = 0
                type_counts["その他"] += 1
                
            d_date = row.get("data_date") or row.get("source_date")
            if d_date:
                dates[d_date] = dates.get(d_date, 0) + 1
                
        # Get the most common date
        primary_date = max(dates.items(), key=lambda x: x[1])[0] if dates else "未定"
        
        meta[slug] = {
            "slug": slug,
            "total_schools": total_schools,
            "municipalities_count": len(municipalities),
            "primary_data_date": primary_date,
            "establishment_counts": est_counts,
            "school_type_counts": type_counts,
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
        
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Generated metadata for {len(meta)} prefectures.")

if __name__ == "__main__":
    generate_meta()
