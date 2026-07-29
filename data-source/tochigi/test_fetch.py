#!/usr/bin/env python3
import urllib.request
import re
import ssl
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
ssl._create_default_https_context = ssl._create_unverified_context
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3'
}

# Known potential Tochigi Prefecture official pages and statistical portals
urls_to_test = [
    'https://www.pref.tochigi.lg.jp/c05/kouhou/toukei/school/r07sokuhou.html',
    'https://www.pref.tochigi.lg.jp/c05/system/honcho/honcho/h29_kaku_toukei/r07/r07_houkokusho.html',
    'https://www.pref.tochigi.lg.jp/c05/system/honcho/honcho/h29_kaku_toukei/r06/r06_houkokusho.html',
    'https://www.pref.tochigi.lg.jp/m03/education/gakkoukyouiku/tokubetsushien/ichiran.html',
    'https://www.pref.tochigi.lg.jp/m04/education/school/koukou/koukou-list.html',
    'https://www.pref.tochigi.lg.jp/m04/system/honcho/honcho/m04/highschool.html',
    'https://www.pref.tochigi.lg.jp/a01/education/shigaku/shiritsugakkou-ichiran.html',
    'https://www.pref.tochigi.lg.jp/c03/education/shigaku/ichiran.html',
    'https://www.pref.tochigi.lg.jp/m03/education/school/shochu/index.html',
    'https://www.pref.tochigi.lg.jp/f06/welfare/kodomo/kosodate/youchien.html',
    'https://www.pref.tochigi.lg.jp/'
]

for url in urls_to_test:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            print(f'SUCCESS: {url} (status: {response.status})')
            # Extract links
            links = re.findall(r'href=[\"\']?([^\s\"\'\>]+)', html)
            for l in set(links):
                if any(l.lower().endswith(ext) for ext in ('.pdf', '.xlsx', '.xls', '.csv')):
                    print('   DATA LINK:', l)
                elif any(kw in l for kw in ('school', 'ichiran', 'toukei', 'gakkou', 'shochu', 'koukou', 'shigaku')):
                    print('   PAGE LINK:', l)
    except Exception as e:
        print(f'FAIL: {url} -> {e}')
