import json
import os
import re

# Read raw text
with open('scratch/column_vol5_raw.txt', 'r', encoding='utf-8') as f:
    raw_text = f.read()

# Strip outer user request tags and metadata if present
raw_text = re.sub(r'^<USER_REQUEST>\s*', '', raw_text)
raw_text = re.sub(r'</USER_REQUEST>.*$', '', raw_text, flags=re.DOTALL)
raw_text = re.sub(r'<ADDITIONAL_METADATA>.*$', '', raw_text, flags=re.DOTALL)
raw_text = raw_text.strip()

# Remove 'コラム記事を公式HPのコラム記事に' prefix line if exists
raw_text = re.sub(r'^コラム記事を公式HPのコラム記事に\s*', '', raw_text)

# Remove prompt instructions like 'サムネイル画像と挿入が２枚も入れて'
raw_text = re.sub(r'サムネイル画像と挿入が２枚も入れて\s*', '', raw_text)

# Fix heading format at start if needed
# Standard format:
# 　コラム第5弾
# # 青く光る電卓を買った夜から、パソコンの隣の一台へ
# 
# ## ――電卓の歴史と、新しい技術を使ってみる勇気

if not raw_text.startswith('　コラム第5弾'):
    raw_text = '　コラム第5弾\n' + raw_text

# Insert Inline Image 1 after 'わずか5年で、25kgから1.4kgへ。' or section '小さく、安く――半導体が変えた電卓の姿'
img1_html = '\n\n<img src="/assets/images/columns/column-vintage-calculator-evolution.webp" alt="1960年代〜1970年代の大型電卓からポケット電卓への進歩と小型化の歴史" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">\n\n'

target1 = '運んで設置する機械が、手で持ち運べる道具へと近づいていった。'
if target1 in raw_text:
    raw_text = raw_text.replace(target1, target1 + img1_html)
else:
    print('Warning: target1 not found')

# Insert Inline Image 2 after '驚きが薄れたというより、暮らしの中にすっかり根を下ろしたのだと思う。' or section '画面の中に電卓があっても、手元の一台を使う理由'
img2_html = '\n\n<img src="/assets/images/columns/column-modern-numpad-calculator-ai.webp" alt="現代のデスクで活躍するパソコン用兼用の電卓テンキーとAI開発ツール" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">\n\n'

target2 = '驚きが薄れたというより、暮らしの中にすっかり根を下ろしたのだと思う。'
if target2 in raw_text:
    raw_text = raw_text.replace(target2, target2 + img2_html)
else:
    print('Warning: target2 not found')

vol5_entry = {
    "id": "column-blue-calculator-history",
    "slug": "blue-calculator-history",
    "title": "青く光る電卓を買った夜から、パソコンの隣の一台へ――電卓の歴史と、新しい技術を使ってみる勇気",
    "category": "歴史・PCと想い",
    "categorySlug": "history",
    "date": "2026.09.16",
    "excerpt": "1972年カシオミニと1970年代の青く光る蛍光表示管（VFD）電卓の記憶、1957年カシオ14-Aから電卓小型化・液晶化・太陽電池への進化、PCテンキー一体型電卓、そして現代の生成AI活用へ。計算機50年の歴史と教育への想い。",
    "thumbnail": "/assets/images/columns/column-blue-calculator-history.webp",
    "readTime": "約9分",
    "content": raw_text,
    "tags": [
        "電卓の歴史",
        "カシオミニ",
        "VFD表示",
        "電卓からAIへ",
        "PCの歴史",
        "教育とテクノロジー"
    ]
}

columns_path = 'data/columns.json'
with open(columns_path, 'r', encoding='utf-8') as f:
    columns_data = json.load(f)

# Check if entry already exists (prevent duplicate)
columns_data = [c for c in columns_data if c["id"] != vol5_entry["id"]]
columns_data.insert(0, vol5_entry)

with open(columns_path, 'w', encoding='utf-8') as f:
    json.dump(columns_data, f, ensure_ascii=False, indent=2)

print("Successfully added Column Vol 5 to data/columns.json")
