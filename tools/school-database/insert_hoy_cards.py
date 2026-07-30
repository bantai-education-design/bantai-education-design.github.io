import os
import json

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
index_html_path = os.path.join(base_dir, "tools", "school-database", "index.html")

def get_count(pref):
    with open(os.path.join(base_dir, "data", "school-database", f"{pref}.json"), "r", encoding="utf-8") as f:
        return len(json.load(f))

text = open(index_html_path, "r", encoding="utf-8").read()

def card(pref_en, pref_ja):
    return f'''
          <!-- {pref_ja}県カード -->
          <a class="pref-card active-card" href="/tools/school-database/{pref_en}/" aria-label="{pref_ja}県学校データベースを開く">
            <div class="pref-card-header">
              <span class="pref-badge" style="background:#27ae60;">NEW</span>
              <span style="font-size:0.8rem; color:#718096;">令和6年度版</span>
            </div>
            <h2>{pref_ja}県</h2>
            <div class="pref-count" id="count-{pref_en}">収録数: 取得中... 校・園</div>
            <ul class="pref-features">
              <li>国公私立・幼稚園・小中高・特別支援</li>
              <li>市町村・校種・設置区分で検索</li>
              <li>宛名コピー・CSV・Google Maps連携</li>
            </ul>
          </a>
'''

hyogo_card = card("hyogo", "兵庫")
okayama_card = card("okayama", "岡山")
yamaguchi_card = card("yamaguchi", "山口")

if "兵庫県カード" not in text:
    text = text.replace("<!-- ===== 中国地方（広島を先頭に） ===== -->", hyogo_card + "\n          <!-- ===== 中国地方（広島を先頭に） ===== -->")
if "岡山県カード" not in text:
    text = text.replace("<!-- ===== 四国地方 ===== -->", okayama_card + yamaguchi_card + "\n          <!-- ===== 四国地方 ===== -->")

for pref_en in ["hyogo", "okayama", "yamaguchi"]:
    try:
        count = get_count(pref_en)
        text = text.replace(f'<div class="pref-count" id="count-{pref_en}">収録数: 取得中... 校・園</div>', f'<div class="pref-count">収録数: {count} 校・園</div>')
    except Exception as e:
        print(f"Could not get count for {pref_en}: {e}")

open(index_html_path, "w", encoding="utf-8", newline='\n').write(text)
print("Inserted cards for Hyogo, Okayama, Yamaguchi.")
