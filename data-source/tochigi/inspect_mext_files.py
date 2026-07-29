#!/usr/bin/env python3
import glob
import os
import csv
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')
base_dir = os.path.dirname(__file__)

files = sorted(glob.glob(os.path.join(base_dir, 'sc_*.csv')) + glob.glob(os.path.join(base_dir, 'sc_*.xlsx')))

for f in files:
    fname = os.path.basename(f)
    print(f"\n================ FILE: {fname} ({os.path.getsize(f)} bytes) ================")
    try:
        if f.endswith('.csv'):
            # Try different encodings
            for enc in ('cp932', 'utf-8-sig', 'shift_jis'):
                try:
                    df = pd.read_csv(f, encoding=enc, nrows=10, dtype=str)
                    print(f"Read CSV with {enc}. Columns:")
                    print("  ", list(df.columns))
                    # Read all to filter Tochigi if '09' or '栃木' exists
                    df_all = pd.read_csv(f, encoding=enc, dtype=str)
                    tochigi_rows = []
                    for col in df_all.columns:
                        m = df_all[df_all[col].astype(str).str.contains('栃木', na=False)]
                        if len(m) > 0:
                            tochigi_rows = m
                            break
                    if len(tochigi_rows) > 0:
                        print(f"  Found {len(tochigi_rows)} rows containing '栃木'")
                        print("  Sample row:")
                        print("    ", tochigi_rows.iloc[0].to_dict())
                    break
                except Exception:
                    continue
        elif f.endswith('.xlsx'):
            df = pd.read_excel(f, nrows=5, dtype=str)
            print("Read EXCEL. Columns:")
            print("  ", list(df.columns))
            # Try to see if Tochigi exists
            df_all = pd.read_excel(f, dtype=str)
            for col in df_all.columns:
                m = df_all[df_all[col].astype(str).str.contains('栃木', na=False)]
                if len(m) > 0:
                    print(f"  Found {len(m)} rows containing '栃木' in column {col}")
                    print("  Sample row:")
                    print("    ", m.iloc[0].to_dict())
                    break
    except Exception as e:
        print(f"Error reading {fname}: {e}")
