import os
import glob
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

# 1. Update JS files
js_files = glob.glob(os.path.join(base_dir, 'assets', 'js', 'school-database', 'search-*.js'))
for f in js_files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace('学校宛先データベース', '学校データベース')
    with open(f, 'w', encoding='utf-8', newline='\n') as file:
        file.write(content)

# 2. Update HTML files
html_files = glob.glob(os.path.join(base_dir, 'tools', 'school-database', '*', 'index.html'))
html_files.append(os.path.join(base_dir, 'tools', 'school-database', 'index.html'))

for f in html_files:
    if not os.path.isfile(f):
        continue
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Text replacements
    content = content.replace('学校宛先データベース', '学校データベース')
    content = content.replace('>学校宛先DB<', '>全国学校DB<')

    # Fix URLs for Kagawa
    if 'kagawa' in f:
        content = content.replace('https://kyoiku.pref.kagawa.jp/', 'https://www.pref.kagawa.lg.jp/kyouiku/')
        content = content.replace('https://kyoiku.pref.kagawa.jp/about/survey/school-list/', 'https://www.pref.kagawa.lg.jp/kyouiku/soumu/shoukai/link/gakkou.html')
        content = content.replace('https://kyoiku.pref.kagawa.jp/gakko/private-schools/', 'https://www.pref.kagawa.lg.jp/shigaku/shigakukyouiku/index.html')

    # Fix URLs for Okinawa
    if 'okinawa' in f:
        content = content.replace('https://kyoiku.pref.okinawa.jp/', 'https://www.pref.okinawa.jp/edu/')
        content = content.replace('https://kyoiku.pref.okinawa.jp/about/survey/school-list/', 'https://www.pref.okinawa.jp/edu/kyoiku/shichoson/gakkouichiran.html')
        content = content.replace('https://kyoiku.pref.okinawa.jp/gakko/private-schools/', 'https://www.pref.okinawa.jp/edu/shigaku/')

    with open(f, 'w', encoding='utf-8', newline='\n') as file:
        file.write(content)

print("Updated text and URLs in all files.")
