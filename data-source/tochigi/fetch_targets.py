#!/usr/bin/env python3
import urllib.request
import re
import ssl
import sys
from urllib.parse import urljoin, unquote

sys.stdout.reconfigure(encoding='utf-8')
ssl._create_default_https_context = ssl._create_unverified_context
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

urls = [
    'https://www.pref.tochigi.lg.jp/b05/education/gakkoukyouiku/ichiran/1181888873983.html',
    'https://www.pref.tochigi.lg.jp/m04/education/gakkoukyouiku/koutou/koukougaido2020.html',
    'https://www.pref.tochigi.lg.jp/m03/index.html', # 義務教育課
    'https://www.pref.tochigi.lg.jp/m04/index.html', # 高校教育課
    'https://www.pref.tochigi.lg.jp/b05/index.html', # 文書学事課
    'https://www.mext.go.jp/a_menu/shotou/zyouhou/detail/1418706.htm',
    'https://www.mext.go.jp/a_menu/shotou/schoolcode/index.htm',
    'https://www.mext.go.jp/'
]

for url in urls:
    print(f"\n================ {url} ================")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            print(f"STATUS: {res.status}")
            html = res.read().decode('utf-8', errors='ignore')
            # Look for links
            links = re.findall(r'href=[\"\']?([^\s\"\'\>]+)', html, re.IGNORECASE)
            for l in links:
                l_unquoted = unquote(l)
                full = urljoin(url, l)
                if any(ext in full.lower() for ext in ('.xlsx', '.xls', '.pdf', '.csv')):
                    print(f"  FILE: {l_unquoted} -> {full}")
                elif any(kw in l_unquoted for kw in ('ichiran', 'meibo', 'school', 'gakkou', 'tochigi', 'code', 'shotou', 'shogakkou', 'chugakkou', 'koutougakkou', 'youchien')):
                    print(f"  LINK: {l_unquoted} -> {full}")
    except Exception as e:
        print(f"ERROR: {e}")
