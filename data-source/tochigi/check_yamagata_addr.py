#!/usr/bin/env python3
"""山形県の市区町村と住所のパターンを精密チェックする"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('data-source/tochigi/sc_20260529-mxt_chousa01-000011635_1.xlsx', header=1, dtype=str)
df.columns = [c.replace('\n', '').strip() for c in df.columns]
yama = df[df['都道府県番号'] == '06(山形)'].copy()
active = yama[yama['属性情報廃止年月日'].isna() | (yama['属性情報廃止年月日'] == 'nan')]

TARGET_TYPES = {
    'A1(幼稚園)': '幼稚園', 'B1(小学校)': '小学校', 'C1(中学校)': '中学校',
    'C2(義務)': '義務教育学校', 'D1(高校)': '高等学校', 'D2(中等)': '中等教育学校',
    'E1(特支盲)': '特別支援学校', 'E1(特支聾)': '特別支援学校', 'E1(養護)': '特別支援学校',
}
target = active[active['学校種'].isin(TARGET_TYPES.keys())].copy()

# Show addresses that don't start with 市 in canonical municipalities
print("=== Full address samples to identify tricky patterns ===")
for addr in sorted(target['学校所在地'].dropna().unique()):
    txt = addr.replace('山形県', '').strip()
    # Check if it starts with a郡 or plain 市
    if re.match(r'^(最上郡|東田川郡|東置賜郡|西置賜郡|飽海郡)', txt):
        print(f"  郡: {txt[:40]}")
    elif txt.startswith('北村') or txt.startswith('東村') or txt.startswith('西村'):
        print(f"  PROBLEM: {addr[:50]}")
