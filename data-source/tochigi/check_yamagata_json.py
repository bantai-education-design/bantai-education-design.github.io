#!/usr/bin/env python3
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/school-database/yamagata.json', encoding='utf-8') as f:
    data = json.load(f)

print('=== 国立 (4件) ===')
for r in [d for d in data if d['establishment'] == '国立']:
    print(f"  {r['municipality']} | {r['name']}")

print()
print('=== 公立幼稚園 (サンプル) ===')
for r in [d for d in data if d['establishment'] == '公立' and d['school_type'] == '幼稚園'][:5]:
    print(f"  {r['municipality']} | {r['name']}")

print()
print('=== 公立高校 (サンプル) ===')
for r in [d for d in data if d['establishment'] == '公立' and d['school_type'] == '高等学校'][:8]:
    print(f"  {r['municipality']} | {r['name']}")

print()
print('=== 特別支援学校 ===')
for r in [d for d in data if d['school_type'] == '特別支援学校']:
    print(f"  [{r['establishment']}] {r['municipality']} | {r['name']}")

print()
print('=== 郡部 北村山郡大石田町チェック ===')
for r in [d for d in data if '大石田' in r['municipality'] or '大石田' in r['name']]:
    print(f"  {r['municipality']} | {r['name']} | {r['address'][:40]}")

print()
print('=== municipality 空欄チェック ===')
empty_muni = [d for d in data if not d['municipality']]
print(f'  空欄: {len(empty_muni)}件')
for r in empty_muni:
    print(f"    {r['name']} | {r['address']}")

print()
print('=== 私立幼稚園 サンプル ===')
for r in [d for d in data if d['establishment'] == '私立' and d['school_type'] == '幼稚園'][:5]:
    print(f"  {r['municipality']} | {r['name']}")
