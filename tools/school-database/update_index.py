import json
import re
import os

html_path = "tools/school-database/index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Parse existing badges to preserve them
badges = {}
for m in re.finditer(r'<a.*?href=".*?/([^/]+)/?".*?<span class="pref-badge"[^>]*>(.*?)</span>\s*<span[^>]*>(.*?)</span>', html, re.DOTALL):
    slug = m.group(1)
    if slug == 'tokyo-school-address':
        slug = 'tokyo'
    badge_html_match = re.search(r'(<div class="pref-card-header">.*?</div>)', m.group(0), re.DOTALL)
    if badge_html_match:
        badges[slug] = badge_html_match.group(1).strip()

# 2. Inject CSS if missing
css = """
      /* 地方別見出しスタイル */
      .region-header {
        width: 100%;
        margin: 40px 0 20px;
        padding-left: 12px;
        font-size: 1.4rem;
        font-weight: 700;
        color: #2d3748;
        border-left: 4px solid var(--region-color, #718096);
        display: flex;
        align-items: center;
      }
      .region-header::after {
        content: "";
        flex-grow: 1;
        height: 1px;
        background: #e2e8f0;
        margin-left: 16px;
      }
      
      /* 地方ごとのカラー定義 */
      .region-hokkaido { --region-color: #78909c; } /* アイスブルー */
      .region-tohoku   { --region-color: #1565c0; } /* 深い青 */
      .region-kanto    { --region-color: #cfb53b; } /* ゴールド */
      .region-chubu    { --region-color: #00838f; } /* 青緑 */
      .region-kinki    { --region-color: #6a1b9a; } /* 紫 */
      .region-chugoku  { --region-color: #8d6e63; } /* 赤茶 */
      .region-shikoku  { --region-color: #689f38; } /* 若草色 */
      .region-kyushu   { --region-color: #f57c00; } /* 橙色 */

      /* カードの地方別装飾 */
      .pref-card.region-hokkaido { border-top: 3px solid var(--region-color); }
      .pref-card.region-tohoku   { border-top: 3px solid var(--region-color); }
      .pref-card.region-kanto    { border-top: 3px solid var(--region-color); }
      .pref-card.region-chubu    { border-top: 3px solid var(--region-color); }
      .pref-card.region-kinki    { border-top: 3px solid var(--region-color); }
      .pref-card.region-chugoku  { border-top: 3px solid var(--region-color); }
      .pref-card.region-shikoku  { border-top: 3px solid var(--region-color); }
      .pref-card.region-kyushu   { border-top: 3px solid var(--region-color); }

      /* hover時の繊細な発光 */
      .pref-card.region-hokkaido:hover { box-shadow: 0 10px 25px -5px rgba(120, 144, 156, 0.3), 0 8px 10px -6px rgba(120, 144, 156, 0.1); }
      .pref-card.region-tohoku:hover   { box-shadow: 0 10px 25px -5px rgba(21, 101, 192, 0.3), 0 8px 10px -6px rgba(21, 101, 192, 0.1); }
      .pref-card.region-kanto:hover    { box-shadow: 0 10px 25px -5px rgba(207, 181, 59, 0.3), 0 8px 10px -6px rgba(207, 181, 59, 0.1); }
      .pref-card.region-chubu:hover    { box-shadow: 0 10px 25px -5px rgba(0, 131, 143, 0.3), 0 8px 10px -6px rgba(0, 131, 143, 0.1); }
      .pref-card.region-kinki:hover    { box-shadow: 0 10px 25px -5px rgba(106, 27, 154, 0.3), 0 8px 10px -6px rgba(106, 27, 154, 0.1); }
      .pref-card.region-chugoku:hover  { box-shadow: 0 10px 25px -5px rgba(141, 110, 99, 0.3), 0 8px 10px -6px rgba(141, 110, 99, 0.1); }
      .pref-card.region-shikoku:hover  { box-shadow: 0 10px 25px -5px rgba(104, 159, 56, 0.3), 0 8px 10px -6px rgba(104, 159, 56, 0.1); }
      .pref-card.region-kyushu:hover   { box-shadow: 0 10px 25px -5px rgba(245, 124, 0, 0.3), 0 8px 10px -6px rgba(245, 124, 0, 0.1); }
"""

if "/* 地方別見出しスタイル */" not in html:
    html = html.replace("</style>", css + "\n    </style>")

# 3. Safely replace old cards with markers
if "<!-- DATABASE_CARDS_START -->" not in html:
    match_start = re.search(r'<!-- ===== 北海道・東北地方 ===== -->.*?<a class="pref-card', html, re.DOTALL)
    if not match_start:
        match_start = re.search(r'<a class="pref-card', html)
    start_idx = match_start.start()
    
    okinawa_idx = html.find('沖縄県学校データベースを開く')
    end_a = html.find('</a>', okinawa_idx) + 4
    
    html = html[:start_idx] + "\n<!-- DATABASE_CARDS_START -->\n<!-- DATABASE_CARDS_END -->\n" + html[end_a:]

# 4. Read metadata
meta_path = "data/school-database/prefecture-metadata.json"
with open(meta_path, "r", encoding="utf-8") as f:
    metadata = json.load(f)

meta_map = {m['prefecture']: m for m in metadata}

regions = [
    {"name": "関東地方", "class": "region-kanto", "prefectures": ["東京都", "神奈川県", "埼玉県", "千葉県", "茨城県", "栃木県", "群馬県"]},
    {"name": "北海道地方", "class": "region-hokkaido", "prefectures": ["北海道"]},
    {"name": "東北地方", "class": "region-tohoku", "prefectures": ["宮城県", "青森県", "岩手県", "秋田県", "山形県", "福島県"]},
    {"name": "中部地方", "class": "region-chubu", "prefectures": ["愛知県", "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県"]},
    {"name": "近畿地方", "class": "region-kinki", "prefectures": ["大阪府", "三重県", "滋賀県", "京都府", "兵庫県", "奈良県", "和歌山県"]},
    {"name": "中国地方", "class": "region-chugoku", "prefectures": ["広島県", "鳥取県", "島根県", "岡山県", "山口県"]},
    {"name": "四国地方", "class": "region-shikoku", "prefectures": ["香川県", "徳島県", "愛媛県", "高知県"]},
    {"name": "九州・沖縄地方", "class": "region-kyushu", "prefectures": ["福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"]}
]

cards_html = ""

for region in regions:
    cards_html += f'\n          <h3 class="region-header {region["class"]}">{region["name"]}</h3>\n'
    cards_html += '          <div class="pref-grid">\n'
    
    for pref in region["prefectures"]:
        m = meta_map.get(pref)
        if not m:
            continue
            
        slug = m['slug']
        if slug == "tokyo":
            link = "/tools/tokyo-school-address/"
        else:
            link = f"/tools/school-database/{slug}/"
            
        est_parts = []
        if m['establishment_counts']['national'] > 0: est_parts.append(f"国{m['establishment_counts']['national']:,}")
        if m['establishment_counts']['public'] > 0: est_parts.append(f"公{m['establishment_counts']['public']:,}")
        if m['establishment_counts']['private'] > 0: est_parts.append(f"私{m['establishment_counts']['private']:,}")
        if m['establishment_counts']['other'] > 0: est_parts.append(f"他{m['establishment_counts']['other']:,}")
        
        est_str = "・".join(est_parts) if est_parts else "ー"
        total_str = f"{m['total']:,}"
        muni_str = f"{m['municipality_count']:,}"
        stype_str = f"{m['school_type_count']}"
        
        badge_html = badges.get(slug)
        if not badge_html:
            badge_html = f'''<div class="pref-card-header">
              <span class="pref-badge" style="background:#27ae60;">NEW</span>
              <span style="font-size:0.8rem; color:#718096;">令和8年度版</span>
            </div>'''
            
        card = f'''
          <!-- {pref}カード -->
          <a class="pref-card active-card {region["class"]}" href="{link}" aria-label="{pref}学校データベースを開く">
            {badge_html}
            <h2>{pref}</h2>
            <div class="pref-meta-grid">
              <div class="meta-row"><span class="meta-label">収録校・園</span><span class="meta-value">{total_str}</span></div>
              <div class="meta-row"><span class="meta-label">対象地域</span><span class="meta-value">{muni_str}</span></div>
              <div class="meta-row"><span class="meta-label">設置区分</span><span class="meta-value">{est_str}</span></div>
              <div class="meta-row"><span class="meta-label">校種</span><span class="meta-value">{stype_str}<span class="meta-unit">種類</span></span></div>
            </div>
          </a>
'''
        cards_html += card
        
    cards_html += '          </div>\n'

# 5. Inject back into HTML
pattern = r'<!-- DATABASE_CARDS_START -->.*?<!-- DATABASE_CARDS_END -->'
new_html = re.sub(pattern, f'<!-- DATABASE_CARDS_START -->\n{cards_html}\n          <!-- DATABASE_CARDS_END -->', html, flags=re.DOTALL)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(new_html)

print("HTML generated successfully with region grids.")
