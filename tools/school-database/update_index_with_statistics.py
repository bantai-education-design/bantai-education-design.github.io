import json
import re

CSS_PATH = "assets/css/school-database.css"
HTML_PATH = "tools/school-database/index.html"
STATS_PATH = "data/school-database/prefecture-statistics.json"

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
.stat-notice {
  font-size: 0.8rem;
  color: #718096;
  text-align: center;
  margin-top: 40px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
}
.stat-notice a {
  color: var(--gold, #c5a059);
  text-decoration: underline;
}
"""
    if ".pref-stats" not in css:
        with open(CSS_PATH, "w", encoding="utf-8") as f:
            f.write(css + new_css)
        print("CSS updated.")

def update_html():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()
        
    with open(STATS_PATH, "r", encoding="utf-8") as f:
        stats = json.load(f)
        
    # Create a mapping of prefecture names to their HTML blocks
    stat_map = {s["prefecture"]: s for s in stats}
    
    # We will regex replace the <ul class="pref-features">...</ul> inside the cards that have stats
    # For prefectures without stats, we leave them as is for now? 
    # The instruction says "現在公開済みの県で試験実装してください。"
    
    # Find all pref cards
    card_pattern = r'(<a class="pref-card[^>]*>.*?<h2>(.*?)</h2>.*?<div class="pref-count">.*?</div>\s*)(<ul class="pref-features">.*?</ul>)(\s*</a>)'
    
    def repl(m):
        prefix = m.group(1)
        pref_name = m.group(2)
        ul_content = m.group(3)
        suffix = m.group(4)
        
        if pref_name in stat_map:
            s = stat_map[pref_name]
            total_pop = f"{s['total_population']:,}"
            elem = f"{s['enrollment']['elementary']:,}"
            jh = f"{s['enrollment']['junior_high']:,}"
            hs = f"{s['enrollment']['high_school']:,}"
            ratio = s['compulsory_school_age_ratio']
            
            stats_html = f"""<div class="pref-stats">
              <div class="stat-row">
                <span class="stat-label">総人口</span>
                <span class="stat-value">{total_pop}<span class="stat-unit">人</span></span>
              </div>
              <div class="stat-row">
                <span class="stat-label">小学校児童</span>
                <span class="stat-value">{elem}<span class="stat-unit">人</span></span>
              </div>
              <div class="stat-row">
                <span class="stat-label">中学校生徒</span>
                <span class="stat-value">{jh}<span class="stat-unit">人</span></span>
              </div>
              <div class="stat-row">
                <span class="stat-label">高校生徒</span>
                <span class="stat-value">{hs}<span class="stat-unit">人</span></span>
              </div>
              <div class="stat-row">
                <span class="stat-label">義務教育年代</span>
                <span class="stat-value">総人口の{ratio}<span class="stat-unit">％</span></span>
              </div>
            </div>"""
            return prefix + stats_html + suffix
        else:
            return m.group(0) # unchanged
            
    new_html = re.sub(card_pattern, repl, html, flags=re.DOTALL)
    
    # Add common description and notice
    # 1. Add common description before the cards grid if not present
    common_desc = """
        <div class="common-features-notice" style="background:#fff; border:1px solid rgba(7,27,54,0.1); border-radius:12px; padding:20px; margin-bottom:30px;">
          <h3 style="margin-top:0; font-size:1.1rem; color:var(--navy,#0c1b33); display:flex; align-items:center; gap:8px;">
            <i class="fas fa-info-circle" style="color:var(--gold,#c5a059);"></i> 各都道府県版の共通機能
          </h3>
          <p style="margin:0; font-size:0.9rem; color:#4a5568; line-height:1.6;">
            各都道府県版では、国公私立の学校検索、設置区分・校種フィルター、宛名コピー、CSV出力、Google Maps連携を利用できます。各カードの数値は都道府県固有の人口・教育規模の統計情報です。
          </p>
        </div>"""
        
    if "common-features-notice" not in new_html:
        # insert before <div class="region-section">
        new_html = new_html.replace('<div class="region-section">', common_desc + '\n        <div class="region-section">', 1)
        
    # 2. Add notice at the bottom
    notice_html = """
        <div class="stat-notice">
          人口（令和2年国勢調査）・在学者数（令和5年学校基本調査）は公的統計に基づきます。<br>
          学校収録数とは基準日が異なる場合や、進学による越境などにより学齢人口と在学者数が一致しない場合があります。<br>
          <a href="/docs/school-database/statistics/source-manifest.md">詳細な出典と基準日はこちら（統計出典ページ）</a>
        </div>"""
        
    if "stat-notice" not in new_html:
        # insert before </section> inside db-grid-section
        new_html = new_html.replace('      </div>\n    </section>', '      </div>\n' + notice_html + '\n    </section>')
        
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_html)
    print("HTML updated.")

if __name__ == "__main__":
    update_css()
    update_html()
