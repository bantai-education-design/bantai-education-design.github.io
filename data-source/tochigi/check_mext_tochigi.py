#!/usr/bin/env python3
import pandas as pd
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
base_dir = os.path.dirname(__file__)
excel_path = os.path.join(base_dir, 'sc_221222-mxt-mxt_chousa01-1000011635_1.xlsx')

print("=== READING MEXT SCHOOL DATABASE (EXCEL) ===")
df = pd.read_excel(excel_path, header=1, dtype=str)
# Clean column names by removing newlines and spaces
df.columns = [c.replace('\n', '').strip() for c in df.columns]
print("Cleaned Columns:", list(df.columns))

# Filter Tochigi (prefecture code 09 or Name contains 09)
tochigi_df = df[df['都道府県番号'].astype(str).str.contains('09|栃木', na=False)]
print(f"Total Tochigi records in file: {len(tochigi_df)}")

# Filter active schools (属性情報廃止年月日 is NaN or empty)
active_tochigi = tochigi_df[tochigi_df['属性情報廃止年月日'].isna() | (tochigi_df['属性情報廃止年月日'] == '') | (tochigi_df['属性情報廃止年月日'] == 'nan')]
print(f"Active Tochigi schools: {len(active_tochigi)}")

# Breakdown by school type (学校種) and establishment type (設置区分: 1=国, 2=公, 3=私)
print("\nBreakdown by school type (学校種) and establishment type (設置区分):")
print(active_tochigi.groupby(['学校種', '設置区分']).size())

print("\nSample records:")
for idx, row in active_tochigi.head(10).iterrows():
    print(f"  [{row['学校種']}] (設置区分={row['設置区分']}) {row['学校名']} | 〒{row['郵便番号']} {row['学校所在地']}")

# Save clean Tochigi active school list to CSV for easy inspection
out_csv = os.path.join(base_dir, 'tochigi_mext_schools.csv')
active_tochigi.to_csv(out_csv, index=False, encoding='utf-8-sig')
print(f"Saved active Tochigi schools to {out_csv}")
