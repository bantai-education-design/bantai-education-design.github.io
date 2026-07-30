import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
tools_dir = os.path.join(base_dir, "tools", "school-database")

chugoku_prefs = [
    {"en": "tottori", "ja": "鳥取", "code": "31", "url": "https://www.pref.tottori.lg.jp/kyouiku/"},
    {"en": "shimane", "ja": "島根", "code": "32", "url": "https://www.pref.shimane.lg.jp/education/"},
    {"en": "okayama", "ja": "岡山", "code": "33", "url": "https://www.pref.okayama.jp/site/16/"},
    {"en": "yamaguchi", "ja": "山口", "code": "35", "url": "https://www.pref.yamaguchi.lg.jp/sec/5000.html"}
]

# We will read convert_fukui_sources.py
with open(os.path.join(tools_dir, "convert_fukui_sources.py"), "r", encoding="utf-8") as f:
    template_py = f.read()

munis = {
    "tottori": ['鳥取市', '米子市', '倉吉市', '境港市', '岩美郡岩美町', '八頭郡若桜町', '八頭郡智頭町', '八頭郡八頭町', '東伯郡三朝町', '東伯郡湯梨浜町', '東伯郡琴浦町', '東伯郡北栄町', '西伯郡日吉津村', '西伯郡大山町', '西伯郡南部町', '西伯郡伯耆町', '日野郡日南町', '日野郡日野町', '日野郡江府町'],
    "shimane": ['松江市', '浜田市', '出雲市', '益田市', '大田市', '安来市', '江津市', '雲南市', '仁多郡奥出雲町', '飯石郡飯南町', '邑智郡川本町', '邑智郡美郷町', '邑智郡邑南町', '鹿足郡津和野町', '鹿足郡吉賀町', '隠岐郡海士町', '隠岐郡西ノ島町', '隠岐郡知夫村', '隠岐郡隠岐の島町'],
    "okayama": ['岡山市', '倉敷市', '津山市', '玉野市', '笠岡市', '井原市', '総社市', '高梁市', '新見市', '備前市', '瀬戸内市', '赤磐市', '真庭市', '美作市', '浅口市', '和気郡和気町', '都窪郡早島町', '浅口郡里庄町', '小田郡矢掛町', '真庭郡新庄村', '苫田郡鏡野町', '勝田郡勝央町', '勝田郡奈義町', '英田郡西粟倉村', '久米郡久米南町', '久米郡美咲町', '加賀郡吉備中央町'],
    "yamaguchi": ['下関市', '宇部市', '山口市', '萩市', '防府市', '下松市', '岩国市', '光市', '長門市', '柳井市', '美祢市', '周南市', '山陽小野田市', '大島郡周防大島町', '玖珂郡和木町', '熊毛郡上関町', '熊毛郡田布施町', '熊毛郡平生町', '阿武郡阿武町']
}

for pref in chugoku_prefs:
    # Basic replacements
    script = template_py.replace("fukui", pref["en"])
    script = script.replace("福井県", f"{pref['ja']}県")
    script = script.replace("FUKUI", pref["en"].upper())
    
    # Replace the mext filter: "18(福井)"
    script = script.replace('18(福井)', f"{pref['code']}({pref['ja']})")
    
    # Replace municipalities
    muni_list = munis[pref["en"]]
    cities = [m for m in muni_list if m.endswith('市')]
    towns = [m for m in muni_list if not m.endswith('市')]
    
    cities_str = f"{pref['en'].upper()}_CITIES = {repr(cities)}"
    towns_str = f"{pref['en'].upper()}_GUN_TOWNS = {repr(towns)}"
    
    script = re.sub(r'FUKUI_CITIES\s*=\s*\[.*?\]', cities_str, script, flags=re.DOTALL)
    script = re.sub(r'FUKUI_GUN_TOWNS\s*=\s*\[.*?\]', towns_str, script, flags=re.DOTALL)
    
    # Write python script
    out_py = os.path.join(tools_dir, f"convert_{pref['en']}_sources.py")
    with open(out_py, "w", encoding="utf-8", newline='\n') as f:
        f.write(script)

print("Regenerated Python Scripts correctly.")
