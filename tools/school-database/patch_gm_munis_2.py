import os
import re

base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"

gifu_munis = ['岐阜市', '大垣市', '高山市', '多治見市', '関市', '中津川市', '美濃市', '瑞浪市', '羽島市', '恵那市', '美濃加茂市', '土岐市', '各務原市', '可児市', '山県市', '瑞穂市', '飛騨市', '本巣市', '郡上市', '下呂市', '海津市', '羽島郡岐南町', '羽島郡笠松町', '養老郡養老町', '不破郡垂井町', '不破郡関ケ原町', '安八郡神戸町', '安八郡輪之内町', '安八郡安八町', '揖斐郡揖斐川町', '揖斐郡大野町', '揖斐郡池田町', '本巣郡北方町', '加茂郡坂祝町', '加茂郡富加町', '加茂郡川辺町', '加茂郡七宗町', '加茂郡八百津町', '加茂郡白川町', '加茂郡東白川村', '可児郡御嵩町', '大野郡白川村']
mie_munis = ['津市', '四日市市', '伊勢市', '松阪市', '桑名市', '鈴鹿市', '名張市', '尾鷲市', '亀山市', '鳥羽市', '熊野市', 'いなべ市', '志摩市', '伊賀市', '桑名郡木曽岬町', '員弁郡東員町', '三重郡菰野町', '三重郡朝日町', '三重郡川越町', '多気郡多気町', '多気郡明和町', '多気郡大台町', '度会郡玉城町', '度会郡度会町', '度会郡大紀町', '度会郡南伊勢町', '北牟婁郡紀北町', '南牟婁郡御浜町', '南牟婁郡紀宝町']

def patch_file(pref, munis):
    path = os.path.join(base_dir, f"tools/school-database/convert_{pref}_sources.py")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    
    muni_str = 'MUNICIPALITIES: list[str] = [\n    ' + ',\n    '.join(f'"{m}"' for m in munis) + '\n]'
    
    pattern = re.compile(r'MUNICIPALITIES\s*:\s*list\[str\]\s*=\s*\[.*?\]', re.DOTALL)
    text = pattern.sub(muni_str, text)
    
    with open(path, "w", encoding="utf-8", newline='\n') as f:
        f.write(text)

patch_file("gifu", gifu_munis)
patch_file("mie", mie_munis)

print("Patched MUNICIPALITIES successfully.")
