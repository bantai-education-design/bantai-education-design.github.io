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

url = 'https://www.pref.tochigi.lg.jp/m03/education/gakkoukyouiku/shouchuu/gakkouitiranntou.html'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10) as res:
    html = res.read().decode('utf-8', errors='ignore')

print(f"=== LINKS IN {url} ===")
matches = re.findall(r'<a[^>]+href=[\"\']?([^\s\"\'\>]+)[\"\']?[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
for href, text in matches:
    clean_text = re.sub(r'<[^>]+>', '', text).strip()
    clean_text = re.sub(r'\s+', ' ', clean_text)
    full = urljoin(url, unquote(href))
    if any(ext in full.lower() for ext in ('.xlsx', '.xls', '.pdf', '.csv', '.doc', '.docx')):
        print(f"  [FILE] {clean_text} -> {full}")
    elif 'pref.tochigi.lg.jp' in full and not any(kw in full for kw in ('banner', 'chosakuken', 'shinchaku')):
        print(f"  [PAGE] {clean_text} -> {full}")
    elif 'tochigi-edu.ed.jp' in full or 'ed.jp' in full or 'city.' in full or 'town.' in full:
        print(f"  [EXT] {clean_text} -> {full}")
