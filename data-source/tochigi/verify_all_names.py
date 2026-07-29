#!/usr/bin/env python3
import pandas as pd
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
base_dir = os.path.dirname(__file__)
csv_path = os.path.join(base_dir, 'tochigi_mext_schools.csv')
df = pd.read_csv(csv_path, dtype=str)

valid_types = {
    'A1(幼稚園)': '幼稚園',
    'B1(小学校)': '小学校',
    'C1(中学校)': '中学校',
    'C2(義務)': '義務教育学校',
    'D1(高校)': '高等学校',
    'D2(中等)': '中等教育学校',
    'E1(特支盲)': '特別支援学校',
    'E1(特支聾)': '特別支援学校',
    'E1(養護)': '特別支援学校'
}

target_df = df[df['学校種'].isin(valid_types.keys())].copy()
target_df['mapped_type'] = target_df['学校種'].map(valid_types)

print("Checking National Schools:")
for idx, r in target_df[target_df['設置区分'] == '1(国)'].iterrows():
    print(f"  {r['学校名']}")

print("\nChecking Public Schools without '立':")
no_tatsu = target_df[(target_df['設置区分'] == '2(公)') & (~target_df['学校名'].str.contains('立'))]
for idx, r in no_tatsu.iterrows():
    print(f"  [{r['学校種']}] {r['学校名']}")

print("\nChecking Public Schools not ending with expected suffixes:")
suffixes = ('幼稚園', '小学校', '中学校', '義務教育学校', '高等学校', '中等教育学校', '特別支援学校', '盲学校', '聾学校', '養護学校', '学園', '分校', '分教室')
bad_suffix = target_df[~target_df['学校名'].str.endswith(suffixes)]
for idx, r in bad_suffix.iterrows():
    print(f"  [{r['設置区分']}] [{r['学校種']}] {r['学校名']}")
