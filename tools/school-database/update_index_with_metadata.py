import json
import re

CSS_PATH = "assets/css/school-database.css"
HTML_PATH = "tools/school-database/index.html"
META_PATH = "data/school-database/prefectures_meta.json"

def update_css():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        css = f.read()

    new_css = """
/* Prefecture Statistics Styles */
.pref-stats {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed rgba(7, 27, 54, 0.1);
}
.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  line-height: 1.2;
}
.stat-label {
  font-size: 0.75rem;
  color: #718096;
}
.stat-value {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--navy, #0c1b33);
}
.stat-unit {
  font-size: 0.7rem;
  font-weight: 400;
  margin-left: 2px;
  color: #718096;
}
"""
    if ".pref-stats" not in css:
        with open(CSS_PATH, "w", encoding="utf-8") as f:
            f.write(css + new_css)
        print("CSS updated.")

def update_html():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()
        
    with open(META_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    # Create mapping of URL slug to metadata
    # The URL slug in index.html is like href="/tools/school-database/tokyo/"
    # The meta json keys are slugs like "tokyo"
    
    card_pattern = r'(<a class="pref-card[^>]*href="/tools/school-database/([^/]+)/".*?<div class="pref-count">.*?</div>\s*)(<ul class="pref-features">.*?</ul>)(\s*</a>)'
    
    def repl(m):
        prefix = m.group(1)
        slug = m.group(2)
        ul_content = m.group(3)
        suffix = m.group(4)
        
        if slug in meta:
            s = meta[slug]
            date_str = s["primary_data_date"]
            if "-" in date_str:
                parts = date_str.split("-")
                date_str = f"{parts[0]}年{parts[1].lstrip('0')}月{parts[2].lstrip('0')}日"
                
            munis = f"{s['municipalities_count']:,}"
            public = f"{s['establishment_counts'].get('公立', 0):,}"
            private = f"{s['establishment_counts'].get('私立', 0):,}"
            national = s['establishment_counts'].get('国立', 0) + s['establishment_counts'].get('組合立', 0) + s['establishment_counts'].get('株式会社立', 0)
            national_str = f"{national:,}"
            
            stats_html = f"""<div class="pref-stats">
              <div class="stat-row">
                <span class="stat-label">データ基準日</span>
                <span class="stat-value">{date_str}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">対象エリア</span>
                <span class="stat-value">{munis}<span class="stat-unit">市区町村</span></span>
              </div>
              <div class="stat-row">
                <span class="stat-label">公立校</span>
                <span class="stat-value">{public}<span class="stat-unit">校</span></span>
              </div>
              <div class="stat-row">
                <span class="stat-label">私立校</span>
                <span class="stat-value">{private}<span class="stat-unit">校</span></span>
              </div>
              <div class="stat-row">
                <span class="stat-label">国立等</span>
                <span class="stat-value">{national_str}<span class="stat-unit">校</span></span>
              </div>
            </div>"""
            return prefix + stats_html + suffix
        else:
            return m.group(0) # unchanged
            
    new_html = re.sub(card_pattern, repl, html, flags=re.DOTALL)
    
    # Add common description before the cards grid if not present
    common_desc = """
        <div class="common-features-notice" style="background:#fff; border:1px solid rgba(7,27,54,0.1); border-radius:12px; padding:20px; margin-bottom:30px;">
          <h3 style="margin-top:0; font-size:1.1rem; color:var(--navy,#0c1b33); display:flex; align-items:center; gap:8px;">
            <i class="fas fa-info-circle" style="color:var(--gold,#c5a059);"></i> 全都道府県データベースの共通機能
          </h3>
          <p style="margin:0; font-size:0.9rem; color:#4a5568; line-height:1.6;">
            各都道府県版では、国公私立の学校検索、設置区分・校種フィルター、宛名コピー、CSV出力、Google Maps連携を利用できます。
          </p>
        </div>"""
        
    if "common-features-notice" not in new_html:
        new_html = new_html.replace('<div class="region-section">', common_desc + '\n        <div class="region-section">', 1)
        
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_html)
    print("HTML updated.")

if __name__ == "__main__":
    update_css()
    update_html()
