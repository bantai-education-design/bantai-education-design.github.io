import json
import re

html_path = "tools/school-database/index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

meta_path = "data/school-database/prefecture-metadata.json"
with open(meta_path, "r", encoding="utf-8") as f:
    metadata = json.load(f)

meta_map = {m['slug']: m for m in metadata}
meta_map['tokyo-school-address'] = meta_map['tokyo']

def replace_card(match):
    full_match = match.group(0)
    slug = match.group(1)
    
    m = meta_map.get(slug)
    if not m:
        return full_match # unchanged
        
    est_parts = []
    if m['establishment_counts']['national'] > 0: est_parts.append(f"国{m['establishment_counts']['national']}")
    if m['establishment_counts']['public'] > 0: est_parts.append(f"公{m['establishment_counts']['public']}")
    if m['establishment_counts']['private'] > 0: est_parts.append(f"私{m['establishment_counts']['private']}")
    if m['establishment_counts']['other'] > 0: est_parts.append(f"他{m['establishment_counts']['other']}")
    
    est_str = "・".join(est_parts) if est_parts else "ー"
    total_str = f"{m['total']:,}"
    muni_str = f"{m['municipality_count']:,}"
    stype_str = f"{m['school_type_count']}"
    
    new_inner = f"""
            <div class="pref-meta-grid">
              <div class="meta-row"><span class="meta-label">収録校・園</span><span class="meta-value">{total_str}</span></div>
              <div class="meta-row"><span class="meta-label">対象地域</span><span class="meta-value">{muni_str}</span></div>
              <div class="meta-row"><span class="meta-label">設置区分</span><span class="meta-value">{est_str}</span></div>
              <div class="meta-row"><span class="meta-label">校種</span><span class="meta-value">{stype_str}<span class="meta-unit">種類</span></span></div>
            </div>
          """
    
    # We replace everything from <div class="pref-count"> or <div class="pref-meta-grid"> to the </a>
    # Actually, it's safer to find the <h2>(.*?)</h2> and replace everything after it until </a>
    
    # regex inside the card
    h2_end = full_match.find('</h2>') + 5
    if h2_end < 5: return full_match
    
    prefix = full_match[:h2_end]
    return prefix + new_inner + "\n          </a>"

# We use re.sub with a custom function.
# The card starts with <a class="pref-card... and ends with </a>
# We must capture the slug inside href
pattern = r'<a class="[^"]*pref-card[^"]*".*?href=".*?/([^/]+)/?".*?<h2>.*?</h2>.*?</a>'
new_html = re.sub(pattern, replace_card, html, flags=re.DOTALL)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(new_html)

print("Updated index.html")
