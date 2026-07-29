#!/usr/bin/env python3
import pdfplumber
import os
import sys
import re
import unicodedata

sys.stdout.reconfigure(encoding='utf-8')
base_dir = os.path.dirname(__file__)

def normalize_text(val):
    if not val:
        return ""
    t = unicodedata.normalize("NFKC", str(val)).replace("\n", " ").replace("\r", "")
    return re.sub(r'\s+', ' ', t).strip()

phone_map = {}

# 1. Private kindergartens shigaku
p1 = os.path.join(base_dir, 'private_youchien_shigaku.pdf')
if os.path.exists(p1):
    with pdfplumber.open(p1) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    cells = [normalize_text(c) for c in row]
                    if len(cells) > 6 and '028' in cells[5] or '028' in cells[6] or '028' in str(row):
                        for c in cells:
                            if re.search(r'\d{2,4}-\d{2,4}-\d{4}', c):
                                phone = re.search(r'\d{2,4}-\d{2,4}-\d{4}', c).group(0)
                                name = [x for x in cells if '幼稚園' in x or 'こども園' in x]
                                if name and phone:
                                    phone_map[name[0].replace(' ', '')] = phone

print(f"Extracted {len(phone_map)} phones from sample kindergarten PDF")
for k, v in list(phone_map.items())[:10]:
    print(f"  {k}: {v}")
