import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Aomori (Pref code 02)
df = pd.read_excel('data-source/tochigi/mext_20260529-mxt_chousa01-000011635_1.xlsx', dtype=str, skiprows=1)
df.columns = [c.replace('\n', '').strip() for c in df.columns]

m_aomori = df[df['都道府県コード'] == '02']['市区町村名'].unique().tolist()
m_akita = df[df['都道府県コード'] == '05']['市区町村名'].unique().tolist()

print('Aomori:', m_aomori)
print('Akita:', m_akita)
