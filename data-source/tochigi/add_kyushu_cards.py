import os

html_path = r"C:\Users\User\Documents\bantai-education-design.github.io\tools\school-database\index.html"

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

saga_card = """          <!-- 佐賀県カード -->
          <a class="pref-card active-card" href="/tools/school-database/saga/" aria-label="佐賀県学校データベースを開く">
            <div class="pref-card-header">
              <span class="pref-badge" style="background:#27ae60;">NEW</span>
              <span style="font-size:0.8rem; color:#718096;">令和8年度版</span>
            </div>
            <h2>佐賀県</h2>
            <div class="pref-count">収録数: 510 校・園</div>
            <ul class="pref-features">
              <li>国公私立の幼稚園・小中高・特別支援</li>
              <li>市町村・校種・設置区分で検索</li>
              <li>宛名コピー・CSV・Google Maps連携</li>
            </ul>
          </a>

"""

nagasaki_card = """          <!-- 長崎県カード -->
          <a class="pref-card active-card" href="/tools/school-database/nagasaki/" aria-label="長崎県学校データベースを開く">
            <div class="pref-card-header">
              <span class="pref-badge" style="background:#27ae60;">NEW</span>
              <span style="font-size:0.8rem; color:#718096;">令和8年度版</span>
            </div>
            <h2>長崎県</h2>
            <div class="pref-count">収録数: 901 校・園</div>
            <ul class="pref-features">
              <li>国公私立の幼稚園・小中高・特別支援</li>
              <li>市町村・校種・設置区分で検索</li>
              <li>宛名コピー・CSV・Google Maps連携</li>
            </ul>
          </a>

"""

kumamoto_card = """          <!-- 熊本県カード -->
          <a class="pref-card active-card" href="/tools/school-database/kumamoto/" aria-label="熊本県学校データベースを開く">
            <div class="pref-card-header">
              <span class="pref-badge" style="background:#27ae60;">NEW</span>
              <span style="font-size:0.8rem; color:#718096;">令和8年度版</span>
            </div>
            <h2>熊本県</h2>
            <div class="pref-count">収録数: 953 校・園</div>
            <ul class="pref-features">
              <li>国公私立の幼稚園・小中高・特別支援</li>
              <li>市町村・校種・設置区分で検索</li>
              <li>宛名コピー・CSV・Google Maps連携</li>
            </ul>
          </a>

"""

# Insert before Okinawa card to keep Fukuoka first
content = content.replace("          <!-- 沖縄県カード -->", saga_card + nagasaki_card + kumamoto_card + "          <!-- 沖縄県カード -->")

with open(html_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
print("Added cards to index.html")
