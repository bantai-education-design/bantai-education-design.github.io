# coding: utf-8
import json
import sys
from pathlib import Path

def clean_file(filepath: Path, is_saitama: bool = False, tokyo_kanagawa_fukushima_miyagi: bool = False):
    if not filepath.exists():
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    initial_count = len(data)
    
    # 1. Remove Saitama invalid records
    if is_saitama:
        data = [
            r for r in data 
            if not (
                r.get("municipality") == "" and 
                r.get("address") == "" and 
                r.get("postal_code") == "" and 
                r.get("school_name") == "さいたま市"
            )
        ]
    
    # 2. Exact Deduplication with Course Merging (Option B)
    if tokyo_kanagawa_fukushima_miyagi:
        merged = {}
        ordered_keys = []
        for r in data:
            name_key = "school_name" if "school_name" in r else "name"
            name_val = r.get(name_key, "")
            est_val = r.get("establishment", r.get("establishment_type", ""))
            
            sig = (
                r.get("prefecture", ""),
                r.get("municipality", ""),
                name_val,
                r.get("school_type", ""),
                est_val,
                r.get("postal_code", ""),
                r.get("address", ""),
                r.get("phone", ""),
                r.get("operator", "")
            )
            
            if sig not in merged:
                merged[sig] = r.copy()
                if "course" not in merged[sig] or merged[sig]["course"] is None:
                    pass
                elif isinstance(merged[sig]["course"], str):
                    merged[sig]["course"] = [merged[sig]["course"]]
                elif not isinstance(merged[sig]["course"], list):
                    merged[sig]["course"] = list(merged[sig]["course"])
                ordered_keys.append(sig)
            else:
                # Merge course
                current_courses = merged[sig].get("course", [])
                if not isinstance(current_courses, list):
                    current_courses = [current_courses] if current_courses else []
                    
                new_courses = r.get("course", [])
                if not isinstance(new_courses, list):
                    new_courses = [new_courses] if new_courses else []
                    
                for c in new_courses:
                    if c and c not in current_courses:
                        current_courses.append(c)
                
                if "course" in merged[sig] or current_courses:
                    merged[sig]["course"] = current_courses
                    
        data = [merged[k] for k in ordered_keys]

    final_count = len(data)
    if initial_count != final_count:
        print(f"{filepath.name}: Removed {initial_count - final_count} records.")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

def main():
    root = Path("data/school-database")
    clean_file(root / "tokyo.json", tokyo_kanagawa_fukushima_miyagi=True)
    clean_file(root / "kanagawa.json", tokyo_kanagawa_fukushima_miyagi=True)
    clean_file(root / "fukushima.json", tokyo_kanagawa_fukushima_miyagi=True)
    clean_file(root / "miyagi.json", tokyo_kanagawa_fukushima_miyagi=True)
    clean_file(root / "saitama.json", is_saitama=True)

if __name__ == "__main__":
    main()
