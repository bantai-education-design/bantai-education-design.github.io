import os
import csv
import json
import urllib.request
import re

# Define directories in the main worktree
root_dir = r'C:\Users\User\Documents\アプリ\小学校教育計画教務支援システム\_site_work'

urls = {
    '小学校': 'https://www.kyoiku.metro.tokyo.lg.jp/documents/d/kyoiku/r7_shougakkou_address',
    '中学校': 'https://www.kyoiku.metro.tokyo.lg.jp/documents/d/kyoiku/r7_chuugakkou_address',
    '義務教育学校': 'https://www.kyoiku.metro.tokyo.lg.jp/documents/d/kyoiku/r7_gimu_address',
    '高等学校': 'https://www.kyoiku.metro.tokyo.lg.jp/documents/d/kyoiku/r7_koutougakkou_address',
    '中等教育学校': 'https://www.kyoiku.metro.tokyo.lg.jp/documents/d/kyoiku/r7_chuutou_address',
    '特別支援学校': 'https://www.kyoiku.metro.tokyo.lg.jp/documents/d/kyoiku/r7_tokubetsushien_ichiran_address'
}

# Municipality to Hiragana mapping
muni_kana_map = {
    # 23 Wards
    '千代田区': 'ちよだ', '中央区': 'ちゅうおう', '港区': 'みなと', '新宿区': 'しんじゅく',
    '文京区': 'ぶんきょう', '台東区': 'たいとう', '墨田区': 'すみだ', '江東区': 'こうとう',
    '品川区': 'しながわ', '目黒区': 'めぐろ', '大田区': 'おおた', '世田谷区': 'せたがや',
    '渋谷区': 'しぶや', '中野区': 'なかの', '杉並区': 'すぎなみ', '豊島区': 'toshima',
    '北区': 'きた', '荒川区': 'あらかわ', '板橋区': 'いたばし', '練馬区': 'ねりま',
    '足立区': 'あだち', '葛飾区': 'かつしか', '江戸川区': 'えどがわ',
    # Cities
    '八王子市': 'はちおうじ', '立川市': 'たちかわ', '武蔵野市': 'むさしの', '三鷹市': 'みたか',
    '青梅市': 'おうめ', '府中市': 'ふちゅう', '昭島市': 'あきしま', '調布市': 'ちょうふ',
    '町田市': 'まちだ', '小金井市': 'こがねい', '小平市': 'こだいら', '日野市': 'ひの',
    '東村山市': 'ひがしむらやま', '国分寺市': 'こくぶんじ', '国立市': 'くにたち', '福生市': 'ふっさ',
    '狛江市': 'こまえ', '東大和市': 'ひがしやまと', '清瀬市': 'きよせ', '東久留米市': 'ひがしくるめ',
    '武蔵村山市': 'むさしむらやま', '多摩市': 'たま', '稲城市': 'いなぎ', '羽村市': 'はむら',
    'あきる野市': 'あきるの', '西東京市': 'にしとうきょう',
    # Towns & Villages
    '大島町': 'おおしま', '八丈町': 'はちじょう', '瑞穂町': 'みずほ', '日の出町': 'ひので', '奥多摩町': 'おくたま',
    '利島村': 'としま', '新島村': 'にいじま', '神津島村': 'こうづしま', '三宅村': 'みやけ',
    '御蔵島村': 'みくらじま', '青ヶ島村': 'あおがしま', '小笠原村': 'おがさわら', '檜原村': 'ひのはら'
}

def get_kana_prefix(municipality):
    base = muni_kana_map.get(municipality, '')
    if not base:
        return ''
    if municipality.endswith('区'):
        return base + 'くりつ'
    elif municipality.endswith('市'):
        return base + 'しりつ'
    elif municipality.endswith('町'):
        return base + 'まちりつ'
    elif municipality.endswith('村'):
        return base + 'むらりつ'
    return base + 'りつ'

def katakana_to_hiragana(text):
    chars = []
    for char in text:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6:
            chars.append(chr(code - 0x60))
        elif char == 'ー':
            chars.append('ー')
        else:
            chars.append(char)
    return "".join(chars)

schools_dataset = []

headers_request = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

for school_type, url in urls.items():
    print(f"Downloading and processing {school_type} data...")
    req = urllib.request.Request(url, headers=headers_request)
    try:
        with urllib.request.urlopen(req) as res:
            lines = res.read().decode('shift-jis').splitlines()
            reader = csv.reader(lines)
            header = next(reader)
            
            # Dynamically find column indices based on header names
            col_muni = header.index('所在地区市町村') if '所在地区市町村' in header else header.index('設置者')
            col_name = header.index('学校名')
            col_zip = header.index('郵便番号')
            col_addr = header.index('住所')
            col_tel = header.index('電話番号')
            col_kana = header.index('学校名(フリガナ)')
            
            count = 0
            for row in reader:
                if not row or len(row) < 5:
                    continue
                
                muni_raw = row[col_muni].strip()
                name_raw = row[col_name].strip()
                zip_code = row[col_zip].strip()
                addr_raw = row[col_addr].strip()
                tel = row[col_tel].strip()
                kana_raw = row[col_kana].strip()
                
                # Determine establishment and formal names based on school type
                establishment_type = "公立" # Currently all public
                
                if school_type in ['小学校', '中学校', '義務教育学校']:
                    # Existing logic
                    if muni_raw == '東京都':
                        formal_name = name_raw
                        if school_type == '小学校' and not (formal_name.endswith('小学校') or formal_name.endswith('学校')):
                            formal_name += '小学校'
                        elif school_type == '中学校' and not (formal_name.endswith('中学校') or formal_name.endswith('学校')):
                            formal_name += '中学校'
                        elif school_type == '義務教育学校' and not (formal_name.endswith('学園') or formal_name.endswith('学校') or formal_name.endswith('義務教育学校')):
                            formal_name += '義務教育学校'
                        
                        formal_name = f"東京都立{formal_name}"
                        
                        # Kana formatting
                        kana_hira = katakana_to_hiragana(kana_raw)
                        if school_type == '小学校' and not (kana_hira.endswith('しょうがっこう') or kana_hira.endswith('がっこう')):
                            kana_hira += 'しょうがっこう'
                        elif school_type == '中学校' and not (kana_hira.endswith('ちゅうがっこう') or kana_hira.endswith('がっこう')):
                            kana_hira += 'ちゅうがっこう'
                        elif school_type == '義務教育学校' and not (kana_hira.endswith('がくえん') or kana_hira.endswith('がっこう') or kana_hira.endswith('ぎむきょういくがっこう')):
                            kana_hira += 'ぎむきょういくがっこう'
                            
                        school_name_kana = f"とうきょうとりつ{kana_hira}"
                        full_address = f"東京都{addr_raw}"
                        
                        m_match = re.match(r'^([^市区町村]+[市区町村])', addr_raw)
                        physical_muni = m_match.group(1) if m_match else '東京都'
                    else:
                        formal_name = name_raw
                        if school_type == '小学校' and not (formal_name.endswith('小学校') or formal_name.endswith('学園') or formal_name.endswith('学校')):
                            formal_name += '小学校'
                        elif school_type == '中学校' and not (formal_name.endswith('中学校') or formal_name.endswith('学園') or formal_name.endswith('学校')):
                            formal_name += '中学校'
                        elif school_type == '義務教育学校' and not (formal_name.endswith('学園') or formal_name.endswith('学校') or formal_name.endswith('義務教育学校')):
                            formal_name += '義務教育学校'
                            
                        formal_name = f"{muni_raw}立{formal_name}"
                        
                        kana_prefix = get_kana_prefix(muni_raw)
                        kana_hira = katakana_to_hiragana(kana_raw)
                        if school_type == '小学校' and not (kana_hira.endswith('しょうがっこう') or kana_hira.endswith('学園') or kana_hira.endswith('がっこう')):
                            kana_hira += 'しょうがっこう'
                        elif school_type == '中学校' and not (kana_hira.endswith('ちゅうがっこう') or kana_hira.endswith('学園') or kana_hira.endswith('がっこう')):
                            kana_hira += 'ちゅうがっこう'
                        elif school_type == '義務教育学校' and not (kana_hira.endswith('がくえん') or kana_hira.endswith('がっこう') or kana_hira.endswith('ぎむきょういくがっこう')):
                            kana_hira += 'ぎむきょういくがっこう'
                            
                        school_name_kana = f"{kana_prefix}{kana_hira}"
                        full_address = f"東京都{muni_raw}{addr_raw}"
                        physical_muni = muni_raw

                elif school_type == '高等学校':
                    # All are metropolitan public high schools (東京都立)
                    formal_name = name_raw
                    if not (formal_name.endswith('高等学校') or formal_name.endswith('高校') or formal_name.endswith('学校')):
                        formal_name += '高等学校'
                    formal_name = f"東京都立{formal_name}"
                    
                    kana_hira = katakana_to_hiragana(kana_raw)
                    if not (kana_hira.endswith('こうとうがっこう') or kana_hira.endswith('こうこう') or kana_hira.endswith('がっこう')):
                        kana_hira += 'こうとうがっこう'
                    school_name_kana = f"とうきょうとりつ{kana_hira}"
                    
                    physical_muni = muni_raw
                    
                    # Address prefixing
                    if addr_raw.startswith('東京都'):
                        full_address = addr_raw
                    elif addr_raw.startswith(physical_muni):
                        full_address = f"東京都{addr_raw}"
                    else:
                        full_address = f"東京都{physical_muni}{addr_raw}"
                        
                elif school_type == '中等教育学校':
                    # Municipal or Metropolitan
                    formal_name = name_raw
                    if not formal_name.endswith('中等教育学校'):
                        formal_name += '中等教育学校'
                    
                    if muni_raw == '東京都':
                        formal_name = f"東京都立{formal_name}"
                        kana_hira = katakana_to_hiragana(kana_raw)
                        if not kana_hira.endswith('ちゅうとうきょういくがっこう'):
                            kana_hira += 'ちゅうとうきょういくがっこう'
                        school_name_kana = f"とうきょうとりつ{kana_hira}"
                        
                        m_match = re.match(r'^([^市区町村]+[市区町村])', addr_raw)
                        physical_muni = m_match.group(1) if m_match else '東京都'
                    else:
                        formal_name = f"{muni_raw}立{formal_name}"
                        kana_prefix = get_kana_prefix(muni_raw)
                        kana_hira = katakana_to_hiragana(kana_raw)
                        if not kana_hira.endswith('ちゅうとうきょういくがっこう'):
                            kana_hira += 'ちゅうとうきょういくがっこう'
                        school_name_kana = f"{kana_prefix}{kana_hira}"
                        physical_muni = muni_raw
                    
                    if addr_raw.startswith('東京都'):
                        full_address = addr_raw
                    elif addr_raw.startswith(physical_muni):
                        full_address = f"東京都{addr_raw}"
                    else:
                        full_address = f"東京都{physical_muni}{addr_raw}"

                elif school_type == '特別支援学校':
                    # Municipal or Metropolitan. Names already end in 盲学校/ろう学校/特別支援学校/学園
                    formal_name = name_raw
                    if muni_raw == '東京都':
                        formal_name = f"東京都立{formal_name}"
                        kana_hira = katakana_to_hiragana(kana_raw)
                        school_name_kana = f"とうきょうとりつ{kana_hira}"
                        
                        m_match = re.match(r'^([^市区町村]+[市区町村])', addr_raw)
                        physical_muni = m_match.group(1) if m_match else '東京都'
                    else:
                        formal_name = f"{muni_raw}立{formal_name}"
                        kana_prefix = get_kana_prefix(muni_raw)
                        kana_hira = katakana_to_hiragana(kana_raw)
                        school_name_kana = f"{kana_prefix}{kana_hira}"
                        physical_muni = muni_raw
                        
                    if addr_raw.startswith('東京都'):
                        full_address = addr_raw
                    elif addr_raw.startswith(physical_muni):
                        full_address = f"東京都{addr_raw}"
                    else:
                        full_address = f"東京都{physical_muni}{addr_raw}"
                
                # Cleanup potential duplicate prefix of municipality name in full_address
                if physical_muni != '東京都':
                    dup_pattern = f"東京都{physical_muni}{physical_muni}"
                    if full_address.startswith(dup_pattern):
                        full_address = full_address.replace(dup_pattern, f"東京都{physical_muni}", 1)

                record = {
                    "school_type": school_type,
                    "establishment_type": establishment_type,
                    "municipality": physical_muni,
                    "school_name": formal_name,
                    "school_name_kana": school_name_kana,
                    "postal_code": zip_code,
                    "address": full_address,
                    "phone": tel,
                    "addressee_default": f"{formal_name} 御中",
                    "source": "東京都教育委員会「令和7年度 公立学校統計調査報告書【東京都公立学校一覧】」",
                    "data_date": "2025-05-01",
                    "address_date": "2025-05-01"
                }
                
                schools_dataset.append(record)
                count += 1
            print(f"Loaded {count} schools for {school_type}.")
    except Exception as e:
        print(f"Error processing {school_type}: {e}")
        import sys
        sys.exit(1)

# Save JSON file
json_output_path = os.path.join(root_dir, 'data', 'tokyo_public_schools_address_2025.json')
os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
with open(json_output_path, 'w', encoding='utf-8') as f:
    json.dump(schools_dataset, f, ensure_ascii=False, indent=2)
print(f"\nSaved {len(schools_dataset)} schools to JSON: {json_output_path}")

# Save CSV file (UTF-8 BOM) for the complete default package download
csv_output_path = os.path.join(root_dir, 'downloads', 'tokyo_public_schools_address_2025.csv')
os.makedirs(os.path.dirname(csv_output_path), exist_ok=True)
with open(csv_output_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['学校種別', '設置区分', '区市町村', '学校名', '学校名（ふりがな）', '郵便番号', '所在地', '電話番号', 'デフォルト宛名'])
    for r in schools_dataset:
        writer.writerow([
            r['school_type'],
            r['establishment_type'],
            r['municipality'],
            r['school_name'],
            r['school_name_kana'],
            r['postal_code'],
            r['address'],
            r['phone'],
            r['addressee_default']
        ])
print(f"Saved CSV (UTF-8 BOM): {csv_output_path}")
