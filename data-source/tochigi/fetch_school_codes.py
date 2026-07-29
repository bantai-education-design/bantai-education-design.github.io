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

pages = [
    'https://www.mext.go.jp/b_menu/toukei/mext_01087.html',
    'https://www.mext.go.jp/a_menu/other/data_00001.htm'
]

for url in pages:
    print(f"\n================ PAGE: {url} ================")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            html = res.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'<a[^>]+href=[\"\']?([^\s\"\'\>]+)[\"\']?[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
            for href, text in matches:
                clean = re.sub(r'<[^>]+>', '', text).strip()
                clean = re.sub(r'\s+', ' ', clean)
                full = urljoin(url, unquote(href))
                if any(ext in full.lower() for ext in ('.xlsx', '.xls', '.csv', '.zip')):
                    print(f"  [FILE] {clean} -> {full}")
                    if any(kw in clean or kw in full for kw in ('学校', 'コード', '一覧', '全国', '施設', '01087', 'chousa', 'shoto')):
                        fname = os.path.basename(full).split('?')[0]
                        out_path = os.path.join(os.path.dirname(__file__), f"sc_{fname}")
                        if not os.path.exists(out_path):
                            try:
                                print(f"       Downloading to {out_path}...")
                                req_file = urllib.request.Request(full, headers=headers)
                                with urllib.request.urlopen(req_file, timeout=30) as fres, open(out_path, 'wb') as f:
                                    f.write(fres.read())
                                print(f"       -> SUCCESS ({os.path.getsize(out_path)} bytes)")
                            except Exception as de:
                                print(f"       -> ERROR: {de}")
                        else:
                            print(f"       Already exists: {out_path}")
    except Exception as e:
        print(f"  [ERROR] {e}")
