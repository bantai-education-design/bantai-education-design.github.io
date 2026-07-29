#!/usr/bin/env python3
import urllib.request
import urllib.parse
import re
import ssl
import sys
import os
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
ssl._create_default_https_context = ssl._create_unverified_context
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# 1. Check if any downloaded statistical PDF actually contains individual school names!
for pdf_name in ('dl_r6_gakkoukihon_toukeihyou.pdf', 'private_schools.pdf', 'private_youchien_shigaku.pdf', 'private_youchien_shisetsu.pdf'):
    p = os.path.join(os.path.dirname(__file__), pdf_name)
    if os.path.exists(p):
        print(f"=== CHECKING PDF: {pdf_name} ===")
        with pdfplumber.open(p) as doc:
            print(f"Total pages: {len(doc.pages)}")
            text = doc.pages[0].extract_text() or ""
            print("Page 1 sample:", text[:300].replace('\n', ' '))
            if len(doc.pages) > 2:
                t2 = doc.pages[2].extract_text() or ""
                print("Page 3 sample:", t2[:300].replace('\n', ' '))

# 2. Check m04 link for high schools / special needs
url = 'https://www.pref.tochigi.lg.jp/m04/education/gakkoukyouiku/ichiran/1184201648717.html'
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as res:
        html = res.read().decode('utf-8', errors='ignore')
        print(f"\n=== LINKS IN {url} ===")
        for href, text in re.findall(r'<a[^>]+href=[\"\']?([^\s\"\'\>]+)[\"\']?[^>]*>(.*?)</a>', html, re.I | re.S):
            clean = re.sub(r'<[^>]+>', '', text).strip()
            full = urllib.parse.urljoin(url, href)
            if any(ext in full.lower() for ext in ('.xlsx', '.xls', '.pdf', '.csv', '.doc', '.docx')) or 'school' in full or 'tochigi-edu' in full or 'gakkou' in full:
                print(f"  [{clean}] -> {full}")
except Exception as e:
    print(f"ERROR: {e}")

# 3. Search DuckDuckGo HTML for school code Excel or Tochigi elementary list
def search_ddg(query):
    print(f"\n=== DUCKDUCKGO SEARCH: {query} ===")
    u = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            html = res.read().decode('utf-8', errors='ignore')
            for m in re.findall(r'<a class=\"result__url\" href=\"([^\"]+)\"[^>]*>(.*?)</a>', html, re.I | re.S):
                clean_url = re.sub(r'<[^>]+>', '', m[0]).strip()
                clean_url = re.sub(r'\s+', '', clean_url)
                if 'mext.go.jp' in clean_url or 'tochigi.lg.jp' in clean_url or 'e-stat' in clean_url or 'mlit' in clean_url or 'xlsx' in clean_url or 'xls' in clean_url:
                    print(f"  FOUND: {clean_url}")
    except Exception as e:
        print(f"SEARCH ERROR: {e}")

search_ddg("文部科学省 学校コード一覧 excel OR xlsx OR xls 令和7年 OR 令和6年")
search_ddg("site:pref.tochigi.lg.jp 学校一覧 小学校 中学校 xlsx OR xls OR csv OR pdf")
search_ddg("栃木県 公立小・中学校名簿 OR 所在地表 filetype:pdf OR filetype:xlsx OR filetype:xls")
