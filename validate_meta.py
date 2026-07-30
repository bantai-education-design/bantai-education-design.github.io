import json
d = json.load(open('data/school-database/prefecture-metadata-pilot.json', encoding='utf-8'))
for p in d:
    total = p['total']
    est_total = sum(p['establishment_counts'].values())
    if total != est_total:
        print(f"Error: {p['prefecture']} total ({total}) != est_total ({est_total})")
    type_total = sum(p['school_type_counts'].values())
    if total != type_total:
        print(f"Error: {p['prefecture']} total ({total}) != type_total ({type_total})")
    print(f"{p['prefecture']}: OK. Total={total}, Warnings={p['warnings_count']}")
