import os
import shutil
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

fukuoka_convert = os.path.join(base_dir, "tools", "school-database", "convert_fukuoka_sources.py")
yamagata_convert = os.path.join(base_dir, "tools", "school-database", "convert_yamagata_sources.py")

with open(yamagata_convert, "r", encoding="utf-8") as f:
    content = f.read()

# Replace specific words
content = content.replace("山形県", "福岡県")
content = content.replace("山形", "福岡")
content = content.replace("yamagata", "fukuoka")
content = content.replace("YAMAGATA", "FUKUOKA")
content = content.replace('06(福岡)', '40(福岡)')

# Replace Cities
fukuoka_cities = '    "福岡市", "北九州市", "久留米市", "大牟田市", "直方市", "飯塚市", "田川市", "柳川市", "八女市", "筑後市", "大川市", "行橋市", "豊前市", "中間市", "小郡市", "筑紫野市", "春日市", "大野城市", "宗像市", "太宰府市", "古賀市", "福津市", "うきは市", "宮若市", "嘉麻市", "朝倉市", "みやま市", "糸島市", "那珂川市",\n'
content = re.sub(r'FUKUOKA_CITIES = \[.*?\]', f'FUKUOKA_CITIES = [\n{fukuoka_cities}]', content, flags=re.DOTALL)

# Replace Guns
fukuoka_guns = '''    # 糟屋郡
    "糟屋郡宇美町", "糟屋郡篠栗町", "糟屋郡志免町", "糟屋郡須恵町", "糟屋郡新宮町", "糟屋郡久山町", "糟屋郡粕屋町",
    # 遠賀郡
    "遠賀郡芦屋町", "遠賀郡水巻町", "遠賀郡岡垣町", "遠賀郡遠賀町",
    # 鞍手郡
    "鞍手郡小竹町", "鞍手郡鞍手町",
    # 嘉穂郡
    "嘉穂郡桂川町",
    # 朝倉郡
    "朝倉郡筑前町", "朝倉郡東峰村",
    # 三井郡
    "三井郡大刀洗町",
    # 三潴郡
    "三潴郡大木町",
    # 八女郡
    "八女郡広川町",
    # 田川郡
    "田川郡香春町", "田川郡添田町", "田川郡糸田町", "田川郡川崎町", "田川郡大任町", "田川郡赤村", "田川郡福智町",
    # 京都郡
    "京都郡苅田町", "京都郡みやこ町",
    # 築上郡
    "築上郡吉富町", "築上郡上毛町", "築上郡築上町",'''
content = re.sub(r'FUKUOKA_GUN_TOWNS = \[.*?\]', f'FUKUOKA_GUN_TOWNS = [\n{fukuoka_guns}\n]', content, flags=re.DOTALL)

# Fix input file to use the CSV we just used
content = content.replace("pd.read_excel(MEXT_DATA_FILE,", "pd.read_csv(MEXT_DATA_FILE, encoding='cp932',")
content = content.replace("sc_20260529-mxt_chousa01-000011635_1.xlsx", "sc_20260529-mxt_chousa01-000011635_4.csv")

with open(fukuoka_convert, "w", encoding="utf-8") as f:
    f.write(content)

print("Created convert_fukuoka_sources.py")
