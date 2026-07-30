import os
import glob
import json
import re
from collections import Counter

def extract_prefecture_names(html_path="tools/school-database/index.html"):
    mapping = {}
    if not os.path.exists(html_path):
        return mapping
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    cards = re.findall(r'<a class=".*?pref-card.*?href=".*?/([^/]+)/?".*?<h2>(.*?)</h2>', html, re.DOTALL)
    for slug, name in cards:
        if slug == "tokyo-school-address":
            slug = "tokyo"
        mapping[slug] = name
    return mapping

def process_prefecture_data(data, slug, pref_name):
    total = len(data)
    municipalities = set()
    est_counts = {"国立": 0, "公立": 0, "私立": 0, "その他": 0}
    school_type_counts = Counter()
    
    used_name_keys = set()
    used_est_keys = set()
    missing_count = 0
    source_dates = {}
    warnings = []
    seen_schools = set()
    
    for idx, row in enumerate(data):
        if not isinstance(row, dict):
            warnings.append(f"Row {idx} is not an object")
            continue
            
        # 1. School Name
        name1 = row.get("name")
        name2 = row.get("school_name")
        
        if name1 is not None and name2 is not None and name1 != name2:
            warnings.append(f"Name conflict: {name1} vs {name2}")
        
        name = name1 if name1 else name2
        if name1: used_name_keys.add("name")
        if name2: used_name_keys.add("school_name")
        
        if not name:
            warnings.append(f"Missing school name at index {idx}")
            name = "Unknown"
        
        if name in seen_schools and name != "Unknown":
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
        if muni and str(muni).strip():
            if muni == pref_name:
                warnings.append(f"Suspicious municipality value (equals prefecture name): {muni} for {name}")
            municipalities.add(str(muni).strip())
        else:
            warnings.append(f"Missing municipality for {name}")
            
        # 4. School Type
        stype = row.get("school_type")
        if stype:
            school_type_counts[stype] += 1
        else:
            warnings.append(f"Missing school_type for {name}")
            
        # 5. Dates
        s_date = row.get("data_date") or row.get("source_date")
        if s_date:
            if est not in source_dates:
                source_dates[est] = set()
            source_dates[est].add(s_date)
            
    formatted_dates = []
    for est, dates in source_dates.items():
        formatted_dates.append({
            "scope": est,
            "date": " / ".join(sorted(list(dates)))
        })
        
    est_total = sum(est_counts.values())
    type_total = sum(school_type_counts.values())
    
    if est_total != total:
        warnings.append(f"ERROR: {slug} total mismatch! est {est_total} != {total}")
    if type_total != total:
        warnings.append(f"ERROR: {slug} total mismatch! type {type_total} != {total}")
        
    return {
        "prefecture": pref_name,
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
        "missing_count": missing_count,
        "warnings": warnings
    }

def generate_metadata():
    results = []
    slug_to_name = extract_prefecture_names()
    
    files = glob.glob("data/school-database/*.json")
    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        if filename in ["prefectures.json", "prefecture-metadata-pilot.json", "prefecture-metadata.json"]:
            continue
            
        slug = filename.replace(".json", "")
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to read {filename}: {e}")
            continue
            
        if not isinstance(data, list) or not data:
            print(f"Warning: {filename} does not contain a valid JSON array or is empty.")
            continue
            
        pref_name = slug_to_name.get(slug)
        if not pref_name:
            for row in data:
                if isinstance(row, dict) and row.get("prefecture"):
                    pref_name = row["prefecture"]
                    break
            
        if not pref_name:
            print(f"Warning: Could not determine Japanese prefecture name for {slug}")
            continue

        meta = process_prefecture_data(data, slug, pref_name)
        results.append(meta)
        
    out_path = "data/school-database/prefecture-metadata.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"Generated {out_path} for {len(results)} prefectures.")
    print("Total national count:", sum(r['total'] for r in results))

if __name__ == "__main__":
    generate_metadata()
