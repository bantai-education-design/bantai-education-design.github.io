import os
import shutil

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

# 1. Create convert_kagawa_sources.py
kagawa_convert = os.path.join(base_dir, "tools", "school-database", "convert_kagawa_sources.py")
yamagata_convert = os.path.join(base_dir, "tools", "school-database", "convert_yamagata_sources.py")

with open(yamagata_convert, "r", encoding="utf-8") as f:
    content = f.read()

# Replace specific words
content = content.replace("山形県", "香川県")
content = content.replace("山形", "香川")
content = content.replace("yamagata", "kagawa")
content = content.replace("YAMAGATA", "KAGAWA")
content = content.replace('06(香川)', '37(香川)') # the script replaced 山形 with 香川 so 06(山形) became 06(香川)

# Replace Cities
kagawa_cities = '    "高松市", "丸亀市", "坂出市", "善通寺市", "観音寺市", "さぬき市", "東かがわ市", "三豊市",\n'
import re
content = re.sub(r'KAGAWA_CITIES = \[.*?\]', f'KAGAWA_CITIES = [\n{kagawa_cities}]', content, flags=re.DOTALL)

# Replace Guns
kagawa_guns = '''    # 小豆郡
    "小豆郡土庄町", "小豆郡小豆島町",
    # 木田郡
    "木田郡三木町",
    # 香川郡
    "香川郡直島町",
    # 綾歌郡
    "綾歌郡宇多津町", "綾歌郡綾川町",
    # 仲多度郡
    "仲多度郡琴平町", "仲多度郡多度津町", "仲多度郡まんのう町",'''
content = re.sub(r'KAGAWA_GUN_TOWNS = \[.*?\]', f'KAGAWA_GUN_TOWNS = [\n{kagawa_guns}\n]', content, flags=re.DOTALL)

# Also fix the input file path for Kagawa
# Since it might be in _1, _2, _3, let's just make it look in _3 since we found it there.
content = content.replace('sc_20260529-mxt_chousa01-000011635_1.xlsx', 'sc_20260529-mxt_chousa01-000011635_3.xlsx')

with open(kagawa_convert, "w", encoding="utf-8") as f:
    f.write(content)

print("Created convert_kagawa_sources.py")
