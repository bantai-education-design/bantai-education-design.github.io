#!/usr/bin/env python3
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('data-source/tochigi/sc_20260529-mxt_chousa01-000011635_1.xlsx', header=1, dtype=str)
df.columns = [c.replace('\n', '').strip() for c in df.columns]

yama = df[df['都道府県番号'] == '06(山形)'].copy()
print(f'Total Yamagata records: {len(yama)}')

active = yama[yama['属性情報廃止年月日'].isna() | (yama['属性情報廃止年月日'] == 'nan')]
print(f'Active schools: {len(active)}')
print()
print('School types (active):')
print(active['学校種'].value_counts())
print()
print('Establishment types (active):')
print(active['設置区分'].value_counts())
print()
print('Sample rows:')
for _, r in active.head(10).iterrows():
    print(f"  [{r['設置区分']}][{r['学校種']}] {r['学校名']} | {r['学校所在地']}")
