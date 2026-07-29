# -*- coding: utf-8 -*-
import pandas as pd
import glob

files = glob.glob('data-source/tochigi/sc_20260529-mxt_chousa01-000011635_*.*')

for f in files:
    if f.endswith('.xlsx'):
        df = pd.read_excel(f, dtype=str, skiprows=1)
    elif f.endswith('.csv'):
        df = pd.read_csv(f, dtype=str, skiprows=1, encoding='cp932')
    else:
        continue
    
    # We want to find column index 2.
    pref_codes = sorted(df.iloc[:, 2].dropna().unique().tolist())
    print(f"{f[-10:]} column 2 has {len(pref_codes)} codes: {pref_codes}")
