import os
import shutil
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

okinawa_convert = os.path.join(base_dir, "tools", "school-database", "convert_okinawa_sources.py")
yamagata_convert = os.path.join(base_dir, "tools", "school-database", "convert_yamagata_sources.py")

with open(yamagata_convert, "r", encoding="utf-8") as f:
    content = f.read()

# Replace specific words
content = content.replace("山形県", "沖縄県")
content = content.replace("山形", "沖縄")
content = content.replace("yamagata", "okinawa")
content = content.replace("YAMAGATA", "OKINAWA")
content = content.replace('06(沖縄)', '47(沖縄)')

# Replace Cities
okinawa_cities = '    "那覇市", "宜野湾市", "石垣市", "浦添市", "名護市", "糸満市", "沖縄市", "豊見城市", "うるま市", "宮古島市", "南城市",\n'
content = re.sub(r'OKINAWA_CITIES = \[.*?\]', f'OKINAWA_CITIES = [\n{okinawa_cities}]', content, flags=re.DOTALL)

# Replace Guns
okinawa_guns = '''    # 国頭郡
    "国頭郡国頭村", "国頭郡大宜味村", "国頭郡東村", "国頭郡今帰仁村", "国頭郡本部町", "国頭郡恩納村", "国頭郡宜野座村", "国頭郡金武町", "国頭郡伊江村",
    # 中頭郡
    "中頭郡読谷村", "中頭郡嘉手納町", "中頭郡北谷町", "中頭郡北中城村", "中頭郡中城村", "中頭郡西原町",
    # 島尻郡
    "島尻郡与那原町", "島尻郡南風原町", "島尻郡渡嘉敷村", "島尻郡座間味村", "島尻郡粟国村", "島尻郡渡名喜村", "島尻郡南大東村", "島尻郡北大東村", "島尻郡伊平屋村", "島尻郡伊是名村", "島尻郡八重瀬町", "島尻郡久米島町",
    # 宮古郡
    "宮古郡多良間村",
    # 八重山郡
    "八重山郡竹富町", "八重山郡与那国町",'''
content = re.sub(r'OKINAWA_GUN_TOWNS = \[.*?\]', f'OKINAWA_GUN_TOWNS = [\n{okinawa_guns}\n]', content, flags=re.DOTALL)

# Fix input file to use the CSV we just used
content = content.replace("pd.read_excel(MEXT_DATA_FILE,", "pd.read_csv(MEXT_DATA_FILE, encoding='cp932',")
content = content.replace("sc_20260529-mxt_chousa01-000011635_1.xlsx", "sc_20260529-mxt_chousa01-000011635_4.csv")

with open(okinawa_convert, "w", encoding="utf-8") as f:
    f.write(content)

print("Created convert_okinawa_sources.py")
