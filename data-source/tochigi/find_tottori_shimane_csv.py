# -*- coding: utf-8 -*-
import pandas as pd
import glob

files = glob.glob('data-source/tochigi/mext_20260529-mxt_chousa01-000011635_*.csv')

for f in files:
    try:
        df = pd.read_csv(f, dtype=str, skiprows=1, encoding='cp932')
        pref_codes = df.iloc[:, 2].dropna().unique().tolist()
        print(f"{f}: (contains 31? {'31' in pref_codes}, contains 32? {'32' in pref_codes})")
    except Exception as e:
        print(f"Err {f}: {e}")
