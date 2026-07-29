#!/usr/bin/env python3
"""山形県データを詳細分析する"""
import pandas as pd
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('data-source/tochigi/sc_20260529-mxt_chousa01-000011635_1.xlsx', header=1, dtype=str)
df.columns = [c.replace('\n', '').strip() for c in df.columns]
yama = df[df['都道府県番号'] == '06(山形)'].copy()
active = yama[yama['属性情報廃止年月日'].isna() | (yama['属性情報廃止年月日'] == 'nan')]

# Scope: include only these school types (exclude 専修, 各種, こども園)
TARGET_TYPES = {
    'A1(幼稚園)': '幼稚園',
    'B1(小学校)': '小学校',
    'C1(中学校)': '中学校',
    'C2(義務)': '義務教育学校',
    'D1(高校)': '高等学校',
    'D2(中等)': '中等教育学校',
    'E1(特支盲)': '特別支援学校',
    'E1(特支聾)': '特別支援学校',
    'E1(養護)': '特別支援学校',
}

target = active[active['学校種'].isin(TARGET_TYPES.keys())].copy()
print(f'Target records (within scope): {len(target)}')
print()
print('By school type:')
print(target['学校種'].value_counts())
print()
print('By establishment:')
print(target['設置区分'].value_counts())
print()

# Extract all municipalities
def extract_muni(addr):
    if not isinstance(addr, str):
        return ''
    addr = addr.replace('山形県', '').strip()
    # Match 市・町・村 (with or without gun prefix)
    m = re.match(r'^([\u90e1\u533a\u5e02\u753a\u6751\u7530\u5ddd\u5c71\u4e2d\u6771\u897f\u5357\u5317\u6700\u4e0a\u8d37\u6751\u5c71\u5c3c\u6751]+(?:市|町|村))', addr)
    if m:
        return m.group(1)
    return addr[:10]

munis = set()
for addr in target['学校所在地'].dropna():
    m_raw = addr.replace('山形県', '').strip()
    m = re.match(r'^(.+?(?:市|町|村))', m_raw)
    if m:
        munis.add(m.group(1))
    
print('Municipalities found:')
for mu in sorted(munis):
    print(f'  {mu}')
print(f'Total: {len(munis)}')
