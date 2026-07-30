import os
import glob

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

gifu_url = "https://www.pref.gifu.lg.jp/site/edu/0001814.html"
mie_url = "https://www.pref.mie.lg.jp/KYOI/HP/m0043800049.htm"

gifu_path = os.path.join(base_dir, "tools/school-database/gifu/index.html")
mie_path = os.path.join(base_dir, "tools/school-database/mie/index.html")

# Gifu
with open(gifu_path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace('href="https://kyoiku.pref.gifu.jp/"', f'href="{gifu_url}"')
text = text.replace('href="https://kyoiku.pref.gifu.jp/about/survey/school-list/"', f'href="{gifu_url}"')
text = text.replace('href="https://kyoiku.pref.gifu.jp/gakko/private-schools/"', f'href="{gifu_url}"')

with open(gifu_path, "w", encoding="utf-8", newline='\n') as f:
    f.write(text)

# Mie
with open(mie_path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace('href="https://kyoiku.pref.mie.jp/"', f'href="{mie_url}"')
text = text.replace('href="https://kyoiku.pref.mie.jp/about/survey/school-list/"', f'href="{mie_url}"')
text = text.replace('href="https://kyoiku.pref.mie.jp/gakko/private-schools/"', f'href="{mie_url}"')

with open(mie_path, "w", encoding="utf-8", newline='\n') as f:
    f.write(text)

print("Links patched successfully.")
