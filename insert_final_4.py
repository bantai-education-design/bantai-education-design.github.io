import os
import json

prefs_info = [
    {"en": "wakayama", "ja": "和歌山県", "region": "近畿地方（大阪を先頭）", "url": "https://www.pref.wakayama.lg.jp/"},
    {"en": "oita", "ja": "大分県", "region": "九州・沖縄地方", "url": "https://www.pref.oita.jp/"},
    {"en": "miyazaki", "ja": "宮崎県", "region": "九州・沖縄地方", "url": "https://www.pref.miyazaki.lg.jp/"},
    {"en": "kagoshima", "ja": "鹿児島県", "region": "九州・沖縄地方", "url": "https://www.pref.kagoshima.jp/"}
]

# 1. Create JS files
for p in prefs_info:
    json_path = f"data/school-database/{p['en']}.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    muni_set = set()
    for row in data:
        if row.get("municipality"):
            muni_set.add(row["municipality"])
            
    # Naive sorting: Cities first, then guns
    cities = sorted([m for m in muni_set if m.endswith("市")])
    others = sorted([m for m in muni_set if not m.endswith("市")])
    muni_order = cities + others
    
    js_content = f"""// {p['ja']}の市町村一覧（行政表示順に近い並び）
const MUNICIPALITY_ORDER = {json.dumps(muni_order, ensure_ascii=False)};

document.addEventListener('DOMContentLoaded', () => {{
    const searchApp = new SchoolSearchApp('{p['en']}', '{p['ja']}');
    searchApp.setMunicipalityOrder(MUNICIPALITY_ORDER);
    searchApp.init();
}});
"""
    with open(f"assets/js/school-database/search-{p['en']}.js", "w", encoding="utf-8") as f:
        f.write(js_content)


# 2. Create HTML files
html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ja} 学校データベース（名簿作成・CSVダウンロード対応） | 先生のための便利帳</title>
    <meta name="description" content="{ja}の幼稚園・小学校・中学校・高校・特別支援学校のデータベース。学校長名での宛名作成、CSVダウンロード、Google Maps連携など、教職員の業務を効率化する無料ツールです。">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="/assets/css/school-database.css">
</head>
<body class="school-database-page">

<header class="site-header">
    <div class="header-container">
        <a href="/" class="site-logo">
            <i class="fas fa-chalkboard-teacher"></i>
            <span>先生のための便利帳</span>
        </a>
        <nav class="header-nav">
            <ul>
                <li><a href="/tools/">ツール一覧</a></li>
                <li><a href="/templates/">テンプレート</a></li>
                <li><a href="/about/">このサイトについて</a></li>
            </ul>
        </nav>
    </div>
</header>

<main class="main-content">
    <div class="db-header">
        <div class="db-header-inner">
            <div class="breadcrumbs">
                <a href="/"><i class="fas fa-home"></i> ホーム</a> &gt; 
                <a href="/tools/">ツール一覧</a> &gt; 
                <a href="/tools/school-database/">学校データベース一覧</a> &gt; 
                <span>{ja}</span>
            </div>
            
            <h1 class="db-title">{ja} 学校データベース</h1>
            <p class="db-description">
                {ja}内の学校（幼稚園・小中高・特別支援）を検索し、宛名のコピーやCSVダウンロードが可能です。
                <br>※データは令和5年度 文部科学省「学校コード一覧」を元に加工しています。
            </p>

            <div class="external-links">
                <a href="{url}" target="_blank" class="boe-link">
                    <i class="fas fa-external-link-alt"></i> {ja} 教育委員会の情報を見る
                </a>
            </div>
        </div>
    </div>

    <!-- ここに検索UI・結果テーブルが入る（共通JSで描画） -->
    <div id="school-search-app" class="app-container">
        <!-- JSでロード表示・UI構築 -->
        <div class="loading-state">
            <i class="fas fa-spinner fa-spin"></i> データベースを読み込んでいます...
        </div>
    </div>
</main>

<footer class="site-footer">
    <!-- 共通フッター -->
</footer>

<script src="/assets/js/school-database/search-core.js"></script>
<script src="/assets/js/school-database/search-{en}.js"></script>
</body>
</html>"""

for p in prefs_info:
    os.makedirs(f"tools/school-database/{p['en']}", exist_ok=True)
    with open(f"tools/school-database/{p['en']}/index.html", "w", encoding="utf-8") as f:
        f.write(html_template.format(**p))


# 3. Update index.html
with open("tools/school-database/index.html", "r", encoding="utf-8") as f:
    index_html = f.read()

def insert_card(pref, target_region):
    global index_html
    with open(f"data/school-database/{pref['en']}.json", "r", encoding="utf-8") as f:
        count = len(json.load(f))
    
    card = f"""          <!-- {pref['ja']}カード -->
          <a class="pref-card active-card" href="/tools/school-database/{pref['en']}/" aria-label="{pref['ja']}学校データベースを開く">
            <div class="pref-card-header">
              <span class="pref-badge" style="background:#27ae60;">NEW</span>
              <span style="font-size:0.8rem; color:#718096;">令和5年度版</span>
            </div>
            <h2>{pref['ja']}</h2>
            <div class="pref-count">収録数: {count} 校・園</div>
            <ul class="pref-features">
              <li>国公私立の幼稚園・小中高・特別支援</li>
              <li>市部・郡部（郡名付き）・校種・設置区分検索</li>
              <li>宛名コピー・CSV・Google Maps連携</li>
            </ul>
          </a>
"""
    if pref['ja'] not in index_html:
        marker = f"<!-- ===== {pref['region']} ===== -->"
        if marker in index_html:
            index_html = index_html.replace(marker, marker + "\n" + card)

for p in prefs_info:
    insert_card(p, p['region'])

with open("tools/school-database/index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

print("Insertion complete.")
