import json
from collections import defaultdict

TARGETS = ["tokyo", "saitama", "chiba", "kanagawa", "fukushima", "miyagi"]
PREFECTURE_NAMES = {
    "tokyo": "東京都", "saitama": "埼玉県", "chiba": "千葉県", 
    "kanagawa": "神奈川県", "fukushima": "福島県", "miyagi": "宮城県"
}

def analyze_duplicates_and_missing():
    print("=== Duplicates Analysis ===")
    for slug in TARGETS:
        filepath = f"data/school-database/{slug}.json"
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        seen_schools = defaultdict(list)
        for idx, row in enumerate(data):
            name = row.get("name") or row.get("school_name") or "Unknown"
            est_raw = row.get("establishment") or row.get("establishment_type")
            est = est_raw[0] if isinstance(est_raw, list) else est_raw
            if not est: est = "その他"
            muni = row.get("municipality")
            stype = row.get("school_type")
            key = (PREFECTURE_NAMES[slug], muni, name, stype, est)
            seen_schools[key].append(row)
            
        for key, rows in seen_schools.items():
            if len(rows) > 1:
                print(f"\nDuplicate Group: {key}")
                for r in rows:
                    addr = r.get("address") or r.get("location")
                    phone = r.get("phone") or r.get("contact")
                    code = r.get("school_code")
                    print(f"  - Addr: {addr}, Phone: {phone}, Code: {code}")

    print("\n=== Saitama Missing Municipality ===")
    with open("data/school-database/saitama.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        for row in data:
            if not row.get("municipality"):
                print(f"Name: {row.get('school_name', row.get('name'))}")
                print(f"Address: {row.get('address', row.get('location'))}")
                print(f"Type: {row.get('school_type')}")
                print(f"Establishment: {row.get('establishment_type', row.get('establishment'))}")
                print("---")

if __name__ == "__main__":
    analyze_duplicates_and_missing()
