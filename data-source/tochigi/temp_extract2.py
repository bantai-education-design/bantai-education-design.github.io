# -*- coding: utf-8 -*-
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 02: Aomori, 05: Akita
df = pd.read_excel('data-source/tochigi/mext_20260529-mxt_chousa01-000011635_1.xlsx', dtype=str, skiprows=1)

# col 0 = pref code, col 4 = municipality name
m_aomori = df[df.iloc[:, 0] == '02'].iloc[:, 4].unique().tolist()
m_akita = df[df.iloc[:, 0] == '05'].iloc[:, 4].unique().tolist()

import json
with open('data-source/tochigi/temp_out.json', 'w', encoding='utf-8') as f:
    json.dump({'aomori': m_aomori, 'akita': m_akita}, f, ensure_ascii=False)
print("done")
