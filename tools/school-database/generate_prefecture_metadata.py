import os
import glob
import json
import re
from collections import Counter, defaultdict

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

def categorize_warning(w):
    if "Name conflict" in w: return "Name conflict"
    if "Missing school name" in w: return "Missing school name"
    if "Duplicate school name" in w: return "Duplicate school name"
    if "Establishment conflict" in w: return "Establishment conflict"
    if "Missing establishment" in w: return "Missing establishment"
    if "Unexpected establishment" in w: return "Unexpected establishment"
    if "Missing municipality" in w: return "Missing municipality"
    if "Suspicious municipality value" in w: return "Suspicious municipality value"
    if "Missing school_type" in w: return "Missing school_type"
    if "is not an object" in w: return "Not an object"
    return "Other"

def process_prefecture_data(data, slug, pref_name):
    total = len(data)
    municipalities = set()
    est_counts = {"国": 0, "公": 0, "私": 0, "その他": 0}
    school_type_counts = Counter()
    
    used_name_keys = set()
    used_est_keys = set()
    missing_count = 0
    source_dates = {}
    
    warnings_list = []
    seen_schools = set()
    
    for idx, row in enumerate(data):
        if not isinstance(row, dict):
            warnings_list.append(f"Row {idx} is not an object")
            continue
            
        # 1. School Name
        name1 = row.get("name")
        name2 = row.get("school_name")
        
        if name1 is not None and name2 is not None and name1 != name2:
            warnings_list.append(f"Name conflict: {name1} vs {name2}")
        
        name = name1 if name1 else name2
        if name1: used_name_keys.add("name")
        if name2: used_name_keys.add("school_name")
        
        if not name:
            warnings_list.append(f"Missing school name at index {idx}")
            name = "Unknown"
        
        if name in seen_schools and name != "Unknown":
            warnings_list.append(f"Duplicate school name: {name}")
        seen_schools.add(name)
            
        # 2. Establishment Type
        est1 = row.get("establishment")
        est2 = row.get("establishment_type")
        
        if est1 is not None and est2 is not None and est1 != est2:
            warnings_list.append(f"Establishment conflict: {est1} vs {est2}")
            
        est_raw = est1 if est1 else est2
        if est1: used_est_keys.add("establishment")
        if est2: used_est_keys.add("establishment_type")
        
        if not est_raw:
            warnings_list.append(f"Missing establishment for {name}")
            missing_count += 1
            est_raw = "その他"
            
        if isinstance(est_raw, list):
            est = est_raw[0] if est_raw else "その他"
        else:
            est = est_raw
            
        if "国" in est or "国立" in est:
            est = "国"
        elif "公" in est or "公立" in est or "県立" in est or "市立" in est or "町立" in est or "村立" in est or "都立" in est or "道立" in est or "府立" in est:
            est = "公"
        elif "私" in est or "私立" in est:
            est = "私"
        else:
            warnings_list.append(f"Unexpected establishment: {est} for {name}")
            est = "その他"
            
        est_counts[est] += 1
        
        # 3. Municipality
        muni = row.get("municipality")
        if muni and str(muni).strip():
            if muni == pref_name:
                warnings_list.append(f"Suspicious municipality value (equals prefecture name): {muni} for {name}")
            municipalities.add(str(muni).strip())
        else:
            warnings_list.append(f"Missing municipality for {name}")
            
        # 4. School Type
        stype = row.get("school_type")
        if stype:
            school_type_counts[stype] += 1
        else:
            warnings_list.append(f"Missing school_type for {name}")
            
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
        warnings_list.append(f"ERROR: {slug} total mismatch! est {est_total} != {total}")
    if type_total != total:
        warnings_list.append(f"ERROR: {slug} total mismatch! type {type_total} != {total}")
        
    meta = {
        "prefecture": pref_name,
        "slug": slug,
        "total": total,
        "municipality_count": len(municipalities),
        "establishment_counts": {
            "national": est_counts["国"],
            "public": est_counts["公"],
            "private": est_counts["私"],
            "other": est_counts["その他"]
        },
        "school_type_count": len(school_type_counts),
        "school_type_counts": dict(school_type_counts),
        "source_dates": formatted_dates,
        "warnings_count": len(warnings_list),
        "missing_count": missing_count
    }
    
    return meta, warnings_list

def generate_metadata():
    results = []
    
    slug_to_name = {
        "hokkaido": "北海道", "aomori": "青森県", "iwate": "岩手県", "miyagi": "宮城県",
        "akita": "秋田県", "yamagata": "山形県", "fukushima": "福島県", "ibaraki": "茨城県",
        "tochigi": "栃木県", "gunma": "群馬県", "saitama": "埼玉県", "chiba": "千葉県",
        "tokyo": "東京都", "kanagawa": "神奈川県", "niigata": "新潟県", "toyama": "富山県",
        "ishikawa": "石川県", "fukui": "福井県", "yamanashi": "山梨県", "nagano": "長野県",
        "gifu": "岐阜県", "shizuoka": "静岡県", "aichi": "愛知県", "mie": "三重県",
        "shiga": "滋賀県", "kyoto": "京都府", "osaka": "大阪府", "hyogo": "兵庫県",
        "nara": "奈良県", "wakayama": "和歌山県", "tottori": "鳥取県", "shimane": "島根県",
        "okayama": "岡山県", "hiroshima": "広島県", "yamaguchi": "山口県", "tokushima": "徳島県",
        "kagawa": "香川県", "ehime": "愛媛県", "kochi": "高知県", "fukuoka": "福岡県",
        "saga": "佐賀県", "nagasaki": "長崎県", "kumamoto": "熊本県", "oita": "大分県",
        "miyazaki": "宮崎県", "kagoshima": "鹿児島県", "okinawa": "沖縄県"
    }

    all_warnings = {}
    
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

        meta, warnings = process_prefecture_data(data, slug, pref_name)
        results.append(meta)
        if warnings:
            all_warnings[slug] = {
                "pref_name": pref_name,
                "filename": filename,
                "warnings": warnings
            }
        
    out_path = "data/school-database/prefecture-metadata.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    # Generate warnings summary markdown
    summary_lines = [
        "# 学校データベース データ異常検知サマリー",
        "",
        "> [!NOTE]",
        "> 各JSONデータに存在する不整合や欠損を記録しています。",
        "> これらの修正はデータクレンジングとして**別PRにて対応**いたします。",
        ""
    ]
    
    for slug, wdata in all_warnings.items():
        pref = wdata["pref_name"]
        filename = wdata["filename"]
        warns = wdata["warnings"]
        
        summary_lines.append(f"## {pref} ({filename})")
        summary_lines.append(f"- **総Warning件数**: {len(warns)}件")
        
        categorized = defaultdict(list)
        for w in warns:
            categorized[categorize_warning(w)].append(w)
            
        summary_lines.append("- **分類別内訳**:")
        for cat, items in categorized.items():
            summary_lines.append(f"  - {cat}: {len(items)}件")
            
        summary_lines.append("")
        summary_lines.append("### 代表例 (各分類最大3件まで)")
        for cat, items in categorized.items():
            summary_lines.append(f"**{cat}**")
            for item in items[:3]:
                summary_lines.append(f"- {item}")
            summary_lines.append("")
            
    with open("data/school-database/warnings_summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))
        
    print(f"Generated {out_path} for {len(results)} prefectures.")
    print("Total national count:", sum(r['total'] for r in results))
    print("Warnings summary generated at data/school-database/warnings_summary.md")

if __name__ == "__main__":
    generate_metadata()
