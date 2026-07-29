#!/usr/bin/env python3
import urllib.request
import re
import ssl
import sys
import os
from urllib.parse import urljoin, unquote

sys.stdout.reconfigure(encoding='utf-8')
ssl._create_default_https_context = ssl._create_unverified_context
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def download_file(url, fname):
    out_path = os.path.join(os.path.dirname(__file__), fname)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res, open(out_path, 'wb') as f:
            f.write(res.read())
        print(f"DOWNLOAD SUCCESS: {fname} ({os.path.getsize(out_path)} bytes)")
    except Exception as e:
        print(f"DOWNLOAD FAIL: {fname} -> {e}")

download_file('https://www.pref.tochigi.lg.jp/e06/welfare/kodomo/youchien/documents/02shigaku.pdf', 'private_youchien_shigaku.pdf')
download_file('https://www.pref.tochigi.lg.jp/e06/welfare/kodomo/youchien/documents/03shisetsugata.pdf', 'private_youchien_shisetsu.pdf')

pages_to_check = [
    'https://www.pref.tochigi.lg.jp/kyouiku/gakkoukyouiku/shou-chuugakkou/index.html',
    'https://www.pref.tochigi.lg.jp/kyouiku/gakkoukyouiku/koutougakkou/index.html',
    'https://www.pref.tochigi.lg.jp/kyouiku/gakkoukyouiku/shienkyouiku/index.html',
    'https://www.pref.tochigi.lg.jp/c04/pref/toukei/toukei/top.html',
    'https://www.pref.tochigi.lg.jp/c04/system/honcho/honcho/h29_kaku_toukei/r07/r07_houkokusho.html',
    'https://www.pref.tochigi.lg.jp/c04/system/honcho/honcho/h29_kaku_toukei/r07/r07_sokuhou.html',
    'https://www.pref.tochigi.lg.jp/c04/pref/toukei/toukei/r07gakkou_kekka.html'
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
                if any(ext in full.lower() for ext in ('.xlsx', '.xls', '.pdf', '.csv')):
                    print(f"  [FILE] {clean_text} -> {full}")
                elif any(kw in clean_text or kw in full for kw in ('幼稚園', '学校', '統計', '一覧', '名簿', '基本調査', '公立', '教育委員会', '小', '中', '高', '義務', '特別', '報告書', '結果')):
                    if not full.startswith('javascript:'):
                        print(f"  [LINK] {clean_text} -> {full}")
    except Exception as e:
        print(f"  [ERROR] {e}")
