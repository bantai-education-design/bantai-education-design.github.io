import os

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

gifu_url_old = "https://www.pref.gifu.lg.jp/site/edu/0001814.html"
mie_url_old = "https://www.pref.mie.lg.jp/KYOI/HP/m0043800049.htm"

gifu_url_new = "https://www.pref.gifu.lg.jp/page/9378.html"
mie_url_new = "https://www.pref.mie.lg.jp/KYOIKU/"

gifu_path = os.path.join(base_dir, "tools/school-database/gifu/index.html")
mie_path = os.path.join(base_dir, "tools/school-database/mie/index.html")

with open(gifu_path, "r", encoding="utf-8") as f:
    text = f.read()
text = text.replace(gifu_url_old, gifu_url_new)
with open(gifu_path, "w", encoding="utf-8", newline='\n') as f:
    f.write(text)

with open(mie_path, "r", encoding="utf-8") as f:
    text = f.read()
text = text.replace(mie_url_old, mie_url_new)
with open(mie_path, "w", encoding="utf-8", newline='\n') as f:
    f.write(text)

print("URLs fixed!")
