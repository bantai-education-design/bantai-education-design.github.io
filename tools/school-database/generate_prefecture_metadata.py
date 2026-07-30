import os
import json
from collections import Counter
from datetime import datetime

TARGETS = ["tokyo", "saitama", "chiba", "kanagawa", "fukushima", "miyagi"]
PREFECTURE_NAMES = {
    "tokyo": "東京都",
    "saitama": "埼玉県",
    "chiba": "千葉県",
    "kanagawa": "神奈川県",
    "fukushima": "福島県",
    "miyagi": "宮城県"
}

def generate_pilot_metadata():
    results = []
    
    for slug in TARGETS:
        filepath = f"data/school-database/{slug}.json"
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        total = len(data)
        municipalities = set()
        
        est_counts = {"国立": 0, "公立": 0, "私立": 0, "その他": 0}
        school_type_counts = Counter()
        
        # Schema tracking
        used_name_keys = set()
        used_est_keys = set()
        missing_count = 0
        
        # Date tracking per establishment
        source_dates = {}
        
        warnings = []
        seen_schools = set()
        
        for row in data:
            # 1. School Name
            name1 = row.get("name")
            name2 = row.get("school_name")
            
            if name1 is not None and name2 is not None and name1 != name2:
                warnings.append(f"Name conflict: {name1} vs {name2}")
            
            name = name1 if name1 else name2
            if name1: used_name_keys.add("name")
            if name2: used_name_keys.add("school_name")
            
            if not name:
                warnings.append("Missing school name")
                name = "Unknown"
            
            if name in seen_schools:
                warnings.append(f"Duplicate school name: {name}")
            seen_schools.add(name)
                
            # 2. Establishment Type
            est1 = row.get("establishment")
            est2 = row.get("establishment_type")
            
            if est1 is not None and est2 is not None and est1 != est2:
                warnings.append(f"Establishment conflict: {est1} vs {est2}")
                
            est_raw = est1 if est1 else est2
            if est1: used_est_keys.add("establishment")
            if est2: used_est_keys.add("establishment_type")
            
            if not est_raw:
                warnings.append(f"Missing establishment for {name}")
                missing_count += 1
                est_raw = "その他"
                
            # Handle array if necessary (though we confirmed they are strings)
            if isinstance(est_raw, list):
                est = est_raw[0] if est_raw else "その他"
            else:
                est = est_raw
                
            if est not in ["国立", "公立", "私立"]:
                warnings.append(f"Unexpected establishment: {est} for {name}")
                est = "その他"
                
            est_counts[est] += 1
            
            # 3. Municipality
            muni = row.get("municipality")
            if muni:
                municipalities.add(muni)
            else:
                warnings.append(f"Missing municipality for {name}")
                
            # 4. School Type
            stype = row.get("school_type")
            if stype:
                school_type_counts[stype] += 1
                
            # 5. Dates
            s_date = row.get("data_date") or row.get("source_date")
            if s_date:
                if est not in source_dates:
                    source_dates[est] = set()
                source_dates[est].add(s_date)
                
        # Format dates
        formatted_dates = []
        for est, dates in source_dates.items():
            formatted_dates.append({
                "scope": est,
                "date": " / ".join(sorted(list(dates)))
            })
            
        # Verify totals
        est_total = sum(est_counts.values())
        if est_total != total:
            print(f"ERROR: {slug} total mismatch! {est_total} != {total}")
            return
            
        if missing_count > 0 or warnings:
            print(f"[{slug}] Warnings: {len(warnings)}, Missing: {missing_count}")
            # Optional: print warnings if needed
            # for w in warnings[:5]: print("  ", w)
            
        results.append({
            "prefecture": PREFECTURE_NAMES[slug],
            "slug": slug,
            "total": total,
            "municipality_count": len(municipalities),
            "establishment_counts": {
                "national": est_counts["国立"],
                "public": est_counts["公立"],
                "private": est_counts["私立"],
                "other": est_counts["その他"]
            },
            "school_type_count": len(school_type_counts),
            "school_type_counts": dict(school_type_counts),
            "schema": {
                "name_key": list(used_name_keys)[0] if used_name_keys else None,
                "establishment_key": list(used_est_keys)[0] if used_est_keys else None
            },
            "source_dates": formatted_dates,
            "warnings_count": len(warnings),
            "missing_count": missing_count
        })
        
    out_path = "data/school-database/prefecture-metadata-pilot.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"Generated {out_path} for {len(results)} prefectures.")

if __name__ == "__main__":
    generate_pilot_metadata()
