import os
import re

html_path = "tools/school-database/index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# We need to insert Toyama into the Chubu region list
toyama_card = '''
          <a href="/tools/school-database/toyama/" class="link-card">
            <span class="icon">🔍</span>
            <span class="text">富山県</span>
          </a>'''

# Insert Toyama after Ishikawa (or wherever in Chubu)
if "<!-- 中部 -->" in html:
    # Actually just append before Ishikawa or Niigata
    # Let's just find Ishikawa and insert before it
    html = re.sub(r'(<a href="/tools/school-database/ishikawa/" class="link-card">)', toyama_card + r'\n          \1', html)

# We need to insert Tokushima, Ehime, Kochi into Shikoku region
shikoku_cards = '''
          <a href="/tools/school-database/tokushima/" class="link-card">
            <span class="icon">🔍</span>
            <span class="text">徳島県</span>
          </a>
          <a href="/tools/school-database/ehime/" class="link-card">
            <span class="icon">🔍</span>
            <span class="text">愛媛県</span>
          </a>
          <a href="/tools/school-database/kochi/" class="link-card">
            <span class="icon">🔍</span>
            <span class="text">高知県</span>
          </a>'''

# Shikoku currently only has Kagawa. Find Kagawa and insert after it.
html = re.sub(r'(<a href="/tools/school-database/kagawa/" class="link-card">\s*<span class="icon">🔍</span>\s*<span class="text">香川県</span>\s*</a>)', r'\1' + shikoku_cards, html)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Cards inserted.")
