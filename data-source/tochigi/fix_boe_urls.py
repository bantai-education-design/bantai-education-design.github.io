import os
import glob

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

# Fix Kagawa
kagawa_file = os.path.join(base_dir, 'tools', 'school-database', 'kagawa', 'index.html')
if os.path.exists(kagawa_file):
    with open(kagawa_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # Kagawa BOE
    content = content.replace('https://www.pref.kagawa.lg.jp/kyouiku/', 'https://www.pref.kagawa.lg.jp/')
    content = content.replace('https://www.pref.kagawa.lg.jp/kyouiku/soumu/shoukai/link/gakkou.html', 'https://www.pref.kagawa.lg.jp/')
    content = content.replace('https://www.pref.kagawa.lg.jp/shigaku/shigakukyouiku/index.html', 'https://www.pref.kagawa.lg.jp/')
    with open(kagawa_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

# Fix Okinawa
okinawa_file = os.path.join(base_dir, 'tools', 'school-database', 'okinawa', 'index.html')
if os.path.exists(okinawa_file):
    with open(okinawa_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # Okinawa BOE
    content = content.replace('https://www.pref.okinawa.jp/edu/', 'https://www.pref.okinawa.jp/edu/index.html')
    content = content.replace('https://www.pref.okinawa.jp/edu/kyoiku/shichoson/gakkouichiran.html', 'https://www.pref.okinawa.jp/edu/index.html')
    content = content.replace('https://www.pref.okinawa.jp/edu/shigaku/', 'https://www.pref.okinawa.jp/edu/index.html')
    with open(okinawa_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

# Fix Fukuoka
fukuoka_file = os.path.join(base_dir, 'tools', 'school-database', 'fukuoka', 'index.html')
if os.path.exists(fukuoka_file):
    with open(fukuoka_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # Fukuoka BOE
    content = content.replace('https://www.pref.fukuoka.lg.jp/life/5/41/192/', 'https://www.pref.fukuoka.lg.jp/life/5/')
    content = content.replace('https://www.pref.fukuoka.lg.jp/life/5/41/193/', 'https://www.pref.fukuoka.lg.jp/life/5/')
    with open(fukuoka_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

print("Fixed links for Kagawa, Okinawa, Fukuoka")
