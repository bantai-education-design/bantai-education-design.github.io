#!/usr/bin/env python3
import urllib.request
import re
import ssl
import sys
from urllib.parse import urljoin

sys.stdout.reconfigure(encoding='utf-8')
ssl._create_default_https_context = ssl._create_unverified_context
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

base_url = 'https://www.pref.tochigi.lg.jp/'

def fetch_and_scan(url, depth=1, visited=None):
    if visited is None: visited = set()
    if url in visited or depth < 0: return
    visited.add(url)
    
    print(f"\n--- SCANNING (depth {depth}): {url}")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Find all anchor tags with text and href
            matches = re.findall(r'<a[^>]+href=[\"\']?([^\s\"\'\>]+)[\"\']?[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
            
            sub_urls = []
            for href, text in matches:
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                full_url = urljoin(url, href)
                if any(ext in full_url.lower() for ext in ('.pdf', '.xlsx', '.xls', '.csv', '.zip')):
                    if any(kw in clean_text or kw in full_url for kw in ('学校', '名簿', '統計', '私立', '公立', '幼稚園', '小', '中', '高', '特別支援', '一覧', 'r7', 'r6', '令和')):
                        print(f"   [DATA FILE] {clean_text} -> {full_url}")
                elif any(kw in clean_text for kw in ('学校', '名簿', '一覧', '私立', '公立', '教育委員会', '統計', '義務教育', '高校')):
                    if full_url.startswith('https://www.pref.tochigi.lg.jp/'):
                        print(f"   [PAGE] {clean_text} -> {full_url}")
                        if depth > 0:
                            sub_urls.append(full_url)
                            
            for su in set(sub_urls[:10]):
                fetch_and_scan(su, depth - 1, visited)
                
    except Exception as e:
        print(f"   [ERROR] {e}")

fetch_and_scan('https://www.pref.tochigi.lg.jp/kyouiku/gakkoukyouiku/manabi/index.html', depth=2)
fetch_and_scan('https://www.pref.tochigi.lg.jp/c05/system/honcho/honcho/index.html', depth=1) # statistical section if applicable
