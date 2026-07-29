#!/usr/bin/env python3
import urllib.request
import re
import ssl
import sys
from urllib.parse import urljoin, unquote
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding='utf-8')
ssl._create_default_https_context = ssl._create_unverified_context
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def check_page(url):
    print(f"\n================ PAGE: {url} ================")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            html = res.read().decode('utf-8', errors='ignore')
            # Look for all links and print those with interesting text or extensions
            matches = re.findall(r'<a[^>]+href=[\"\']?([^\s\"\'\>]+)[\"\']?[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
            for href, text in matches:
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                clean_text = re.sub(r'\s+', ' ', clean_text)
                full = urljoin(url, unquote(href))
                if any(ext in full.lower() for ext in ('.xlsx', '.xls', '.pdf', '.csv', '.zip')):
                    print(f"  [FILE] {clean_text} -> {full}")
                elif any(kw in clean_text or kw in full for kw in ('学校', '名簿', '一覧', '調査', '統計', 'コード', '初等', '中等', '幼稚園', 'こども', '公立', '私立', '県立', '市立', '義務', '特別支援', '令和', 'R6', 'R7', 'r6', 'r7')):
                    if not full.startswith('javascript:'):
                        print(f"  [LINK] {clean_text} -> {full}")
    except Exception as e:
        print(f"  [ERROR] {e}")

check_page('https://www.pref.tochigi.lg.jp/b05/education/gakkoukyouiku/ichiran/1181888873983.html')
check_page('https://www.mext.go.jp/a_menu/shotou/zyouhou/index.htm')
check_page('https://www.pref.tochigi.lg.jp/c05/index.html')
check_page('https://www.pref.tochigi.lg.jp/c05/kouhou/toukei/index.html')
