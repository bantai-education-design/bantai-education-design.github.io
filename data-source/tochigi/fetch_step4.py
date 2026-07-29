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
}

pages_to_check = [
    'https://www.pref.tochigi.lg.jp/c04/pref/toukei/toukei/gakkoukihon.html',
    'https://www.pref.tochigi.lg.jp/kyouiku/gakkoukyouiku/shou-chuugakkou/index.html',
    'https://www.pref.tochigi.lg.jp/m05/education/gakkoukyouiku/tokubetsu/1182860815595.html',
    'https://www.pref.tochigi.lg.jp/m04/education/gakkoukyouiku/koutou/koukougaido2020.html',
    'https://www.pref.tochigi.lg.jp/m03/education/gakkoukyouiku/shouchuu/kyouikukatei.html'
]

for url in pages_to_check:
    print(f"\n================ PAGE: {url} ================")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            html = res.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'<a[^>]+href=[\"\']?([^\s\"\'\>]+)[\"\']?[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
            for href, text in matches:
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                clean_text = re.sub(r'\s+', ' ', clean_text)
                full = urljoin(url, unquote(href))
                if any(ext in full.lower() for ext in ('.xlsx', '.xls', '.pdf', '.csv', '.zip')):
                    print(f"  [FILE] {clean_text} -> {full}")
                elif any(kw in clean_text or kw in full for kw in ('令和', 'R7', 'R6', '報告', '一覧', '学校', '小', '中', '高', '特別', '名簿', '市町', '教育委員会')):
                    if not full.startswith('javascript:'):
                        print(f"  [LINK] {clean_text} -> {full}")
    except Exception as e:
        print(f"  [ERROR] {e}")
