import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io\tools\school-database"
prefectures = {
    "hokkaido": "北海道", "miyagi": "宮城県", "iwate": "岩手県", "fukushima": "福島県",
    "yamagata": "山形県", "aomori": "青森県", "akita": "秋田県", "aichi": "愛知県",
    "niigata": "新潟県", "nagano": "長野県", "yamanashi": "山梨県", "osaka": "大阪府",
    "hiroshima": "広島県", "tottori": "鳥取県", "shimane": "島根県", "kagawa": "香川県",
    "fukuoka": "福岡県", "okinawa": "沖縄県"
}

# Placeholder demographic data (total_m, total_f, school_m, school_f)
demographics = {
    "hokkaido": {"total": {"m": 2400000, "f": 2600000}, "school": {"m": 240000, "f": 230000}},
    "miyagi": {"total": {"m": 1100000, "f": 1200000}, "school": {"m": 110000, "f": 105000}},
    "iwate": {"total": {"m": 580000, "f": 620000}, "school": {"m": 58000, "f": 55000}},
    "fukushima": {"total": {"m": 880000, "f": 920000}, "school": {"m": 88000, "f": 85000}},
    "yamagata": {"total": {"m": 510000, "f": 550000}, "school": {"m": 51000, "f": 49000}},
    "aomori": {"total": {"m": 580000, "f": 630000}, "school": {"m": 58000, "f": 55000}},
    "akita": {"total": {"m": 450000, "f": 500000}, "school": {"m": 45000, "f": 42000}},
    "aichi": {"total": {"m": 3750000, "f": 3750000}, "school": {"m": 375000, "f": 365000}},
    "niigata": {"total": {"m": 1050000, "f": 1120000}, "school": {"m": 105000, "f": 100000}},
    "nagano": {"total": {"m": 990000, "f": 1030000}, "school": {"m": 99000, "f": 95000}},
    "yamanashi": {"total": {"m": 390000, "f": 410000}, "school": {"m": 39000, "f": 37000}},
    "osaka": {"total": {"m": 4200000, "f": 4600000}, "school": {"m": 420000, "f": 410000}},
    "hiroshima": {"total": {"m": 1350000, "f": 1420000}, "school": {"m": 135000, "f": 130000}},
    "tottori": {"total": {"m": 260000, "f": 280000}, "school": {"m": 26000, "f": 25000}},
    "shimane": {"total": {"m": 310000, "f": 340000}, "school": {"m": 31000, "f": 30000}},
    "kagawa": {"total": {"m": 460000, "f": 480000}, "school": {"m": 46000, "f": 44000}},
    "fukuoka": {"total": {"m": 2400000, "f": 2700000}, "school": {"m": 240000, "f": 230000}},
    "okinawa": {"total": {"m": 720000, "f": 740000}, "school": {"m": 72000, "f": 70000}},
}

def generate_html_block(pref_en, pref_ja):
    data = demographics[pref_en]
    t_m, t_f = data["total"]["m"], data["total"]["f"]
    s_m, s_f = data["school"]["m"], data["school"]["f"]
    total_pop = t_m + t_f
    school_pop = s_m + s_f
    school_ratio = (school_pop / total_pop) * 100

    return f"""
    <!-- 人口データセクション -->
    <section class="demographics-section" style="padding: 24px 0; background: #f8fafc; border-bottom: 1px solid #e2e8f0;">
      <div class="container">
        <h2 style="font-size: 1.1rem; color: var(--navy); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
          {pref_ja}の人口・学齢人口データ（※ダミーデータ：実際のデータに要更新）
        </h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
          <div style="background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size: 0.85rem; color: #64748b; font-weight: 700; margin-bottom: 4px;">総人口</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #0f172a;">{total_pop:,} <span style="font-size: 0.9rem; font-weight: normal;">人</span></div>
            <div style="font-size: 0.85rem; color: #475569; margin-top: 8px; display: flex; justify-content: space-between;">
              <span>男性: {t_m:,} 人</span>
              <span>女性: {t_f:,} 人</span>
            </div>
          </div>
          <div style="background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size: 0.85rem; color: #64748b; font-weight: 700; margin-bottom: 4px;">学齢人口 (推定)</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #0f172a;">{school_pop:,} <span style="font-size: 0.9rem; font-weight: normal;">人</span></div>
            <div style="font-size: 0.85rem; color: #475569; margin-top: 8px; display: flex; justify-content: space-between;">
              <span>男性: {s_m:,} 人</span>
              <span>女性: {s_f:,} 人</span>
            </div>
          </div>
          <div style="background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size: 0.85rem; color: #64748b; font-weight: 700; margin-bottom: 4px;">学齢人口の割合</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #0f172a;">{school_ratio:.1f} <span style="font-size: 0.9rem; font-weight: normal;">%</span></div>
            <div style="font-size: 0.85rem; color: #475569; margin-top: 8px; display: flex; justify-content: space-between;">
              <span>総人口に対する比率</span>
            </div>
          </div>
        </div>
      </div>
    </section>
"""

for pref_en, pref_ja in prefectures.items():
    html_path = os.path.join(base_dir, pref_en, "index.html")
    if not os.path.exists(html_path):
        print(f"Skipping {pref_en}, file not found")
        continue

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Avoid adding multiple times
    if "<!-- 人口データセクション -->" in html:
        print(f"Already added to {pref_en}")
        continue

    insertion_target = '<section class="edu-portal-section">'
    replacement = generate_html_block(pref_en, pref_ja) + "\n    " + insertion_target

    if insertion_target in html:
        new_html = html.replace(insertion_target, replacement, 1)
        with open(html_path, "w", encoding="utf-8", newline='\n') as f:
            f.write(new_html)
        print(f"Updated {pref_en}")
    else:
        print(f"Failed to find insertion point in {pref_en}")
