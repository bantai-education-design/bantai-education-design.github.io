import os
import csv
import json

# ==========================================
# 1. Dummy CSV Generation (for test phase)
# ==========================================
DUMMY_CENSUS = "data-source/statistics/dummy_census_2020.csv"
DUMMY_SCHOOL = "data-source/statistics/dummy_school_2023.csv"
OUTPUT_JSON = "data/school-database/prefecture-statistics.json"

TARGET_PREFS = {
    "04": {"ja": "宮城県", "slug": "miyagi"},
    "07": {"ja": "福島県", "slug": "fukushima"},
    "11": {"ja": "埼玉県", "slug": "saitama"},
    "12": {"ja": "千葉県", "slug": "chiba"},
    "13": {"ja": "東京都", "slug": "tokyo"},
    "14": {"ja": "神奈川県", "slug": "kanagawa"}
}

def generate_dummy_csv():
    os.makedirs("data-source/statistics", exist_ok=True)
    
    # 1. Census CSV: pref_code, pref_name, age, total, male, female
    # We generate population for ages 0 to 18, and a "Total" row.
    with open(DUMMY_CENSUS, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["pref_code", "pref_name", "age", "total", "male", "female"])
        for code, info in TARGET_PREFS.items():
            base_pop = 10000000 if code == "13" else 5000000
            # Total row (age="Total")
            writer.writerow([code, info["ja"], "Total", base_pop, base_pop//2, base_pop//2])
            for age in range(20):
                age_pop = int(base_pop * 0.008) # roughly 0.8% per age
                writer.writerow([code, info["ja"], str(age), age_pop, age_pop//2, age_pop//2])
                
    # 2. School Survey CSV: pref_code, pref_name, kindergarten, elem, jh, comp, hs, sec, special
    with open(DUMMY_SCHOOL, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["pref_code", "pref_name", "kindergarten", "elementary", "junior_high", "compulsory_education", "high_school", "secondary", "special_support"])
        for code, info in TARGET_PREFS.items():
            base = 100000 if code == "13" else 50000
            writer.writerow([code, info["ja"], base, base*6, base*3, 1000, base*3, 500, 2000])

# ==========================================
# 2. Conversion Logic
# ==========================================
def run_conversion():
    results = []
    
    # Read School Data
    school_data = {}
    with open(DUMMY_SCHOOL, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            school_data[row["pref_code"]] = {
                "kindergarten": int(row["kindergarten"]) if row["kindergarten"] else None,
                "elementary": int(row["elementary"]) if row["elementary"] else None,
                "junior_high": int(row["junior_high"]) if row["junior_high"] else None,
                "compulsory_education": int(row["compulsory_education"]) if row["compulsory_education"] else None,
                "high_school": int(row["high_school"]) if row["high_school"] else None,
                "secondary": int(row["secondary"]) if row["secondary"] else None,
                "special_support": int(row["special_support"]) if row["special_support"] else None,
            }
            
    # Read Census Data
    census_data = {}
    with open(DUMMY_CENSUS, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["pref_code"]
            if code not in TARGET_PREFS:
                continue
            
            if code not in census_data:
                census_data[code] = {
                    "total": 0, "male": 0, "female": 0,
                    "ages": {}
                }
                
            if row["age"] == "Total":
                census_data[code]["total"] = int(row["total"])
                census_data[code]["male"] = int(row["male"])
                census_data[code]["female"] = int(row["female"])
            else:
                age = int(row["age"])
                census_data[code]["ages"][age] = {
                    "total": int(row["total"]),
                    "male": int(row["male"]),
                    "female": int(row["female"])
                }
                
    # Build final JSON
    for code, info in TARGET_PREFS.items():
        c = census_data.get(code)
        s = school_data.get(code)
        if not c or not s:
            print(f"Missing data for {info['ja']}")
            continue
            
        def sum_ages(start, end):
            t, m, f = 0, 0, 0
            for a in range(start, end + 1):
                if a in c["ages"]:
                    t += c["ages"][a]["total"]
                    m += c["ages"][a]["male"]
                    f += c["ages"][a]["female"]
            return {"total": t, "male": m, "female": f}
            
        age_3_5 = sum_ages(3, 5)
        age_6_11 = sum_ages(6, 11)
        age_12_14 = sum_ages(12, 14)
        age_15_17 = sum_ages(15, 17)
        
        comp_age_pop = age_6_11["total"] + age_12_14["total"]
        comp_ratio = round((comp_age_pop / c["total"]) * 100, 1) if c["total"] > 0 else 0.0
        
        # Verify male + female == total
        assert c["total"] == c["male"] + c["female"]
        assert age_6_11["total"] == age_6_11["male"] + age_6_11["female"]
        
        stat_item = {
            "prefecture_code": code,
            "slug": info["slug"],
            "prefecture": info["ja"],
            "statistics_date": "2020-10-01",
            "total_population": c["total"],
            "male_population": c["male"],
            "female_population": c["female"],
            "age_population": {
                "age_3_5": age_3_5,
                "age_6_11": age_6_11,
                "age_12_14": age_12_14,
                "age_15_17": age_15_17
            },
            "compulsory_school_age_population": comp_age_pop,
            "compulsory_school_age_ratio": comp_ratio,
            "enrollment": s,
            "source": {
                "population_name": "令和2年国勢調査 人口等基本集計",
                "population_url": "https://www.e-stat.go.jp/",
                "population_date": "2020-10-01",
                "enrollment_name": "令和5年度 学校基本調査",
                "enrollment_url": "https://www.e-stat.go.jp/",
                "enrollment_date": "2023-05-01"
            }
        }
        results.append(stat_item)
        
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Generated {OUTPUT_JSON} with {len(results)} records.")

if __name__ == "__main__":
    generate_dummy_csv()
    run_conversion()
