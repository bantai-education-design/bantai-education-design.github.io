import os
import re

html_path = "tools/school-database/index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# Insert Toyama before Ishikawa
toyama_card = '''          <!-- 富山県カード -->
          <a class="pref-card active-card" href="/tools/school-database/toyama/" aria-label="富山県学校データベースを開く">
            <div class="pref-card-header">
              <span class="pref-badge" style="background:#27ae60;">NEW</span>
              <span style="font-size:0.8rem; color:#718096;">令和5年度版</span>
            </div>
            <h2>富山県</h2>
            <div class="pref-count">収録数: 333 校・園</div>
            <ul class="pref-features">
              <li>国公私立の幼稚園・小中高・特別支援</li>
              <li>市部・郡部（郡名付き）・校種・設置区分検索</li>
              <li>宛名コピー・CSV・Google Maps連携</li>
            </ul>
          </a>
'''
if "<!-- 石川県カード -->" in html and "富山県" not in html:
    html = html.replace("<!-- 石川県カード -->", toyama_card + "\n          <!-- 石川県カード -->")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Toyama inserted.")

# Fix BOE URLs
prefs = {
    "toyama": "https://www.pref.toyama.jp/",
    "kagawa": "https://www.pref.kagawa.lg.jp/",
    "tokushima": "https://www.pref.tokushima.lg.jp/",
    "ehime": "https://www.pref.ehime.jp/",
    "kochi": "https://www.pref.kochi.lg.jp/"
}

for pref, url in prefs.items():
    pref_html_path = f"tools/school-database/{pref}/index.html"
    if os.path.exists(pref_html_path):
        with open(pref_html_path, "r", encoding="utf-8") as f:
            p_html = f.read()
        
        # Replace the BOE URL (it's the first button with target="_blank" usually, or just regex)
        p_html = re.sub(r'<a href="https?://www\.pref\.[^"]+" target="_blank" class="boe-link">', f'<a href="{url}" target="_blank" class="boe-link">', p_html)
        
        with open(pref_html_path, "w", encoding="utf-8") as f:
            f.write(p_html)

print("BOE URLs updated.")
