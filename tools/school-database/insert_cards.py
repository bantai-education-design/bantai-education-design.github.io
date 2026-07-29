import os
import json

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
index_html_path = os.path.join(base_dir, "tools", "school-database", "index.html")

def get_count(pref):
    with open(os.path.join(base_dir, "data", "school-database", f"{pref}.json"), "r", encoding="utf-8") as f:
        return len(json.load(f))

text = open(index_html_path, "r", encoding="utf-8").read()

# Insert Ishikawa and Fukui before Kinki
chubu_end_marker = "<!-- ===== 近畿地方（大阪を先頭） ===== -->"
chubu_append = f'''
          <!-- 石川県カード -->
          <a class="pref-card active-card" href="/tools/school-database/ishikawa/" aria-label="石川県学校データベースを開く">
            <div class="pref-card-header">
              <span class="pref-badge" style="background:#27ae60;">NEW</span>
              <span style="font-size:0.8rem; color:#718096;">令和8年度版</span>
            </div>
            <h2>石川県</h2>
            <div class="pref-count">収録数: {{ishikawa_count}} 校・園</div>
            <ul class="pref-features">
              <li>国公私立の幼稚園・小中高・特別支援</li>
              <li>市町村・校種・設置区分で検索</li>
              <li>宛名コピー・CSV・Google Maps連携</li>
            </ul>
          </a>

          <!-- 福井県カード -->
          <a class="pref-card active-card" href="/tools/school-database/fukui/" aria-label="福井県学校データベースを開く">
            <div class="pref-card-header">
              <span class="pref-badge" style="background:#27ae60;">NEW</span>
              <span style="font-size:0.8rem; color:#718096;">令和8年度版</span>
            </div>
            <h2>福井県</h2>
            <div class="pref-count">収録数: {{fukui_count}} 校・園</div>
            <ul class="pref-features">
              <li>国公私立の幼稚園・小中高・特別支援</li>
              <li>市町村・校種・設置区分で検索</li>
              <li>宛名コピー・CSV・Google Maps連携</li>
            </ul>
          </a>

          '''

# Insert Shiga before Chugoku
kinki_end_marker = "<!-- ===== 中国地方（広島を先頭に） ===== -->"
kinki_append = f'''
          <!-- 滋賀県カード -->
          <a class="pref-card active-card" href="/tools/school-database/shiga/" aria-label="滋賀県学校データベースを開く">
            <div class="pref-card-header">
              <span class="pref-badge" style="background:#27ae60;">NEW</span>
              <span style="font-size:0.8rem; color:#718096;">令和8年度版</span>
            </div>
            <h2>滋賀県</h2>
            <div class="pref-count">収録数: {{shiga_count}} 校・園</div>
            <ul class="pref-features">
              <li>国公私立の幼稚園・小中高・特別支援</li>
              <li>市町村・校種・設置区分で検索</li>
              <li>宛名コピー・CSV・Google Maps連携</li>
            </ul>
          </a>

          '''

if "石川県カード" not in text:
    # Need to defer replacing count until JSON is ready
    text = text.replace(chubu_end_marker, chubu_append + chubu_end_marker)
    text = text.replace(kinki_end_marker, kinki_append + kinki_end_marker)
    open(index_html_path, "w", encoding="utf-8", newline='\n').write(text)
    print("Inserted placeholders.")
else:
    print("Already inserted.")
