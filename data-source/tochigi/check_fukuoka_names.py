import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')
df = pd.read_csv('data-source/tochigi/sc_20260529-mxt_chousa01-000011635_4.csv', encoding='cp932', header=1, dtype=str)
df.columns = [c.replace('\n', '').strip() for c in df.columns]
f = df[df['都道府県番号'] == '40(福岡)']
for idx, r in f.iterrows():
    name = r['学校名']
    if '博多高等学園' in name or '大隈城山' in name or '北九州高等学園' in name:
        print(name + ' | ' + r['設置区分'])
