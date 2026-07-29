import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/school-database/fukuoka.json', encoding='utf-8') as f:
    data = json.load(f)

print('=== All unique municipalities ===')
munis = sorted(set(d['municipality'] for d in data))
for m in munis:
    cnt = sum(1 for d in data if d['municipality'] == m)
    print(f"  {m}: {cnt}件")

print()
print('=== 問題のある名称（重複「県立+市立」「サフィックス二重」） ===')
for r in data:
    n = r['name']
    if '県立' in n and '市立' in n:
        print(f"  [県立+市立重複] {r['municipality']} | {n}")
    if n.count('特別支援学校') > 1:
        print(f"  [特支重複] {r['municipality']} | {n}")
    if n.count('高等学校') > 1:
        print(f"  [高校重複] {r['municipality']} | {n}")
    if n.count('養護学校') > 1:
        print(f"  [養護重複] {r['municipality']} | {n}")
