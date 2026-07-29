import os
import shutil

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
yamagata_convert = os.path.join(base_dir, "tools", "school-database", "convert_yamagata_sources.py")
aomori_convert = os.path.join(base_dir, "tools", "school-database", "convert_aomori_sources.py")
akita_convert = os.path.join(base_dir, "tools", "school-database", "convert_akita_sources.py")

with open(yamagata_convert, "r", encoding="utf-8") as f:
    content = f.read()

# Replace for Aomori
aomori_c = content.replace("山形県", "青森県")
aomori_c = aomori_c.replace("山形", "青森")
aomori_c = aomori_c.replace("yamagata", "aomori")
aomori_c = aomori_c.replace("YAMAGATA", "AOMORI")
aomori_c = aomori_c.replace('06(青森)', '02(青森)') # Yamagata is 06, Aomori is 02

# We modify infer_municipality to handle Gun properly for Aomori
infer_aomori = """
import re

AOMORI_CITIES = [
    "青森市", "鰺ヶ沢町", "板柳町", "今別町", "おいらせ町", "大間町", "大鰐町", "風間浦村", "黒石市", "五所川原市", 
    "五戸町", "佐井村", "三戸町", "七戸町", "新郷村", "外ヶ浜町", "田子町", "つがる市", "鶴田町", "十和田市", 
    "東北町", "田舎館村", "中泊町", "南部町", "西目屋村", "野辺地町", "八戸市", "階上町", "弘前市", "平川市", 
    "平内町", "東通村", "深浦町", "藤崎町", "三沢市", "むつ市", "蓬田村", "横浜町", "六戸町", "六ヶ所村"
]
AOMORI_ORDER = sorted(AOMORI_CITIES, key=len, reverse=True)

def infer_municipality(address: str) -> str:
    text = address
    if text.startswith("青森県"):
        text = text[len("青森県"):]
    # Remove Gun name
    text = re.sub(r'^.+?郡', '', text)
    for cand in AOMORI_ORDER:
        if text.startswith(cand):
            return cand
    return ""
"""
import re
aomori_c = re.sub(r'_MUNI_CANDIDATES = .*?return ""', infer_aomori.strip(), aomori_c, flags=re.DOTALL)
with open(aomori_convert, "w", encoding="utf-8") as f:
    f.write(aomori_c)


# Replace for Akita
akita_c = content.replace("山形県", "秋田県")
akita_c = akita_c.replace("山形", "秋田")
akita_c = akita_c.replace("yamagata", "akita")
akita_c = akita_c.replace("YAMAGATA", "AKITA")
akita_c = akita_c.replace('06(秋田)', '05(秋田)') # Yamagata is 06, Akita is 05

infer_akita = """
import re

AKITA_CITIES = [
    "秋田市", "能代市", "横手市", "大館市", "男鹿市", "湯沢市", "鹿角市", "由利本荘市", "潟上市", "大仙市", "北秋田市", "にかほ市", "仙北市",
    "小坂町", "藤里町", "三種町", "八峰町", "五城目町", "八郎潟町", "井川町", "美郷町", "羽後町",
    "上小阿仁村", "大潟村", "東成瀬村"
]
AKITA_ORDER = sorted(AKITA_CITIES, key=len, reverse=True)

def infer_municipality(address: str) -> str:
    text = address
    if text.startswith("秋田県"):
        text = text[len("秋田県"):]
    # Remove Gun name
    text = re.sub(r'^.+?郡', '', text)
    for cand in AKITA_ORDER:
        if text.startswith(cand):
            return cand
    return ""
"""
akita_c = re.sub(r'_MUNI_CANDIDATES = .*?return ""', infer_akita.strip(), akita_c, flags=re.DOTALL)
with open(akita_convert, "w", encoding="utf-8") as f:
    f.write(akita_c)

print("Generated convert_aomori_sources.py and convert_akita_sources.py")
