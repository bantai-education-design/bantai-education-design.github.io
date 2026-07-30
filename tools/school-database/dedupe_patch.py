# coding: utf-8
import os
import re

def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "def deduplicate_exact" in content:
        content = re.sub(r'def deduplicate_exact.*?return \[merged\[k\] for k in ordered_keys\]\n', '', content, flags=re.DOTALL)
        content = content.replace('all_records = deduplicate_exact(all_records)\n    all_records = deduplicate(all_records)', 'all_records = deduplicate(all_records)')
        
    func = """
def deduplicate_exact(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = {}
    ordered_keys = []
    
    for r in records:
        name_val = r.get("school_name", r.get("name", ""))
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
            
    return [merged[k] for k in ordered_keys]
"""
    
    content = content.replace("def deduplicate(", func + "\n\ndef deduplicate(")
    content = content.replace("all_records = deduplicate(all_records)", "all_records = deduplicate_exact(all_records)\n    all_records = deduplicate(all_records)")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

patch_file("tools/school-database/convert_kanagawa_workbooks.py")
patch_file("tools/school-database/convert_fukushima_workbooks.py")
patch_file("tools/school-database/convert_miyagi_workbooks.py")
