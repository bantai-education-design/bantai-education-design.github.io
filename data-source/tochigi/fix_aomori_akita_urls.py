import os

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

# Fix Aomori
aomori_file = os.path.join(base_dir, 'tools', 'school-database', 'aomori', 'index.html')
with open(aomori_file, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('https://kyoiku.pref.aomori.jp/', 'https://www.pref.aomori.lg.jp/')
content = content.replace('https://www.pref.aomori.lg.jp/about/survey/school-list/', 'https://www.pref.aomori.lg.jp/')
content = content.replace('https://www.pref.aomori.lg.jp/gakko/private-schools/', 'https://www.pref.aomori.lg.jp/')

with open(aomori_file, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

# Fix Akita
akita_file = os.path.join(base_dir, 'tools', 'school-database', 'akita', 'index.html')
with open(akita_file, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('https://kyoiku.pref.akita.jp/', 'https://www.pref.akita.lg.jp/')
content = content.replace('https://www.pref.akita.lg.jp/about/survey/school-list/', 'https://www.pref.akita.lg.jp/')
content = content.replace('https://www.pref.akita.lg.jp/gakko/private-schools/', 'https://www.pref.akita.lg.jp/')

with open(akita_file, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("Fixed Aomori and Akita URLs")
