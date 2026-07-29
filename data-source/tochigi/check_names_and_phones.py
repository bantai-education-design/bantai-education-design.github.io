#!/usr/bin/env python3
import pandas as pd
import sys
import os
import pdfplumber
import re

sys.stdout.reconfigure(encoding='utf-8')
base_dir = os.path.dirname(__file__)
csv_path = os.path.join(base_dir, 'tochigi_mext_schools.csv')

df = pd.read_csv(csv_path, dtype=str)

# Filter valid school types for Ban.Tai (幼稚園, 小学校, 中学校, 義務教育学校, 高等学校, 中等教育学校, 特別支援学校)
valid_types = ['A1(幼稚園)', 'B1(小学校)', 'C1(中学校)', 'C2(義務)', 'D1(高校)', 'D2(中等)', 'E1(特支盲)', 'E1(特支聾)', 'E1(養護)']
target_df = df[df['学校種'].isin(valid_types)].copy()
print(f"Total target schools before filtering/merging: {len(target_df)}")

# Check public kindergartens (2(公) and A1)
print("Public kindergartens in dataset:")
pub_youchien = target_df[(target_df['学校種'] == 'A1(幼稚園)') & (target_df['設置区分'] == '2(公)')]
for idx, r in pub_youchien.iterrows():
    print(f"  {r['学校名']}")

# Check school names for any potential abbreviations in public schools
print("\nSample public elementary schools:")
pub_sho = target_df[(target_df['学校種'] == 'B1(小学校)') & (target_df['設置区分'] == '2(公)')]
for idx, r in pub_sho.head(10).iterrows():
    print(f"  {r['学校名']} | {r['学校所在地']}")

# Check if any public elementary or junior high school name does NOT start with a municipality name or Prefecture
print("\nPublic schools that might need official name construction or check:")
pub_all = target_df[target_df['設置区分'] == '2(公)']
for idx, r in pub_all.iterrows():
    name = r['学校名']
    if not any(name.startswith(m) for m in ('宇都宮', '足利', '栃木', '佐野', '鹿沼', '日光', '小山', '真岡', '大田原', '矢板', '那須', 'さくら', '下野', '上三川', '益子', '茂木', '市貝', '芳賀', '壬生', '野木', '塩谷', '高根沢', '塩那', '阿久津')):
        print(f"  [{r['学校種']}] {name} | {r['学校所在地']}")

# Check high schools (D1) and duplicates by address/name
print("\nPublic High Schools (D1) count:", len(target_df[(target_df['学校種'] == 'D1(高校)') & (target_df['設置区分'] == '2(公)')]))
hs_pub = target_df[(target_df['学校種'] == 'D1(高校)') & (target_df['設置区分'] == '2(公)')]
for idx, r in hs_pub.head(15).iterrows():
    print(f"  {r['学校名']} | 〒{r['郵便番号']} {r['学校所在地']}")
