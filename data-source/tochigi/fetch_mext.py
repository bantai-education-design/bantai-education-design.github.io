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

mext_urls = [
    'https://www.mext.go.jp/b_menu/toukei/mext_01087.html',
    'https://www.mext.go.jp/a_menu/other/data_00001.htm',
    'https://www.mext.go.jp/b_menu/toukei/mext_00004.html',
    'https://www.mext.go.jp/b_menu/toukei/002/002b/1417059_00009.htm'
]

for url in mext_urls:
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
                if any(ext in full.lower() for ext in ('.xlsx', '.xls', '.csv', '.zip')):
                    print(f"  [EXCEL/ZIP] {clean_text} -> {full}")
                    # If it looks like a school code / school list file, download it!
                    if any(kw in clean_text or kw in full for kw in ('コード', '一覧', '学校', '全国', '施設', '幼稚園', '小', '中', '高', '2025', '2024', 'r7', 'r6', '0000', 'mext')):
                        fname = os.path.basename(full).split('?')[0]
                        out_path = os.path.join(os.path.dirname(__file__), f"mext_{fname}")
                        try:
                            req_file = urllib.request.Request(full, headers=headers)
                            with urllib.request.urlopen(req_file, timeout=20) as fres, open(out_path, 'wb') as f:
                                f.write(fres.read())
                            print(f"       -> DOWNLOADED {out_path} ({os.path.getsize(out_path)} bytes)")
                        except Exception as de:
                            print(f"       -> DOWNLOAD ERROR: {de}")
                elif not full.startswith('javascript:'):
                    if any(kw in clean_text or kw in full for kw in ('コード', '学校', '統計', '一覧', '名簿', '初等', '中等')):
                        print(f"  [LINK] {clean_text} -> {full}")
    except Exception as e:
        print(f"  [ERROR] {e}")
