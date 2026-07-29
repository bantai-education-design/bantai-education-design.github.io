#!/usr/bin/env python3
import pandas as pd
import sys
import os
import re

sys.stdout.reconfigure(encoding='utf-8')
base_dir = os.path.dirname(__file__)
csv_path = os.path.join(base_dir, 'tochigi_mext_schools.csv')
df = pd.read_csv(csv_path, dtype=str)

muni_list = [
    "宇都宮市", "足利市", "栃木市", "佐野市", "鹿沼市", "日光市", "小山市", "真岡市",
    "大田原市", "矢板市", "那須塩原市", "さくら市", "那須烏山市", "下野市",
    "河内郡上三川町", "芳賀郡益子町", "芳賀郡茂木町", "芳賀郡市貝町", "芳賀郡芳賀町",
    "下都賀郡壬生町", "下都賀郡野木町",
    "塩谷郡塩谷町", "塩谷郡高根沢町",
    "那須郡那須町", "那須郡那珂川町"
]
muni_sorted = sorted(muni_list, key=len, reverse=True)

unmatched = []
for addr in df['学校所在地'].dropna().unique():
    a = addr.replace('栃木県', '').strip()
    found = False
    for m in muni_sorted:
        if a.startswith(m) or a.startswith(re.sub(r'^.+郡', '', m)):
            found = True
            break
    if not found:
        unmatched.append(a)

if unmatched:
    print("Unmatched addresses:", unmatched)
else:
    print("All addresses perfectly matched one of the 25 Tochigi municipalities!")
