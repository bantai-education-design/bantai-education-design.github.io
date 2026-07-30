import os

html_path = "tools/school-database/index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

def make_card(en, ja, count):
    return f'''
          <!-- {ja}県カード -->
          <a class="pref-card active-card" href="/tools/school-database/{en}/" aria-label="{ja}県学校データベースを開く">
            <div class="pref-card-header">
              <span class="pref-badge" style="background:#27ae60;">NEW</span>
              <span style="font-size:0.8rem; color:#718096;">令和5年度版</span>
            </div>
            <h2>{ja}県</h2>
            <div class="pref-count">収録数: {count} 校・園</div>
            <ul class="pref-features">
              <li>国公私立の幼稚園・小中高・特別支援</li>
              <li>市部・郡部（郡名付き）・校種・設置区分検索</li>
              <li>宛名コピー・CSV・Google Maps連携</li>
            </ul>
          </a>
'''

toyama_card = make_card("toyama", "富山", "333")
tokushima_card = make_card("tokushima", "徳島", "401")
ehime_card = make_card("ehime", "愛媛", "582")
kochi_card = make_card("kochi", "高知", "430")

# Insert Toyama after Ishikawa
# Or just before "<!-- ===== 近畿地方 ===== -->"
kinki_marker = "<!-- ===== 近畿地方 ===== -->"
if kinki_marker in html:
    html = html.replace(kinki_marker, toyama_card + "\n          " + kinki_marker)

# Insert Tokushima, Ehime, Kochi after Kagawa
# Or before "<!-- ===== 九州・沖縄地方 ===== -->"
kyushu_marker = "<!-- ===== 九州・沖縄地方 ===== -->"
if kyushu_marker in html:
    html = html.replace(kyushu_marker, tokushima_card + ehime_card + kochi_card + "\n          " + kyushu_marker)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("HTML modified successfully.")
