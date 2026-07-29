#!/usr/bin/env python3
"""問題のある学校のMEXTデータでの元の名称を確認する"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('data-source/tochigi/sc_20260529-mxt_chousa01-000011635_1.xlsx', header=1, dtype=str)
df.columns = [c.replace('\n', '').strip() for c in df.columns]
yama = df[df['都道府県番号'] == '06(山形)'].copy()
active = yama[yama['属性情報廃止年月日'].isna() | (yama['属性情報廃止年月日'] == 'nan')]

keywords = ['市立商業', '致道館', '東桜学館', '村山特別', '楯岡特別', '新庄神室', '新庄志誠', '米沢養護']
for kw in keywords:
    found = active[active['学校名'].str.contains(kw, na=False)]
    for _, r in found.iterrows():
        print(f"[{r['設置区分']}][{r['学校種']}] 元名称: '{r['学校名']}' | 住所: {r['学校所在地'][:50]}")
