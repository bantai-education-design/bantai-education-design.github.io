import json
import os

article_vol9 = """　コラム第9弾
# 【授業改善・教材配布】デジタル方眼紙・五線譜・観察カードで作る「伝わるプリント」設計術

## ――レイアウト・文字サイズ・イラスト図解をふんだんに使ったワークシート実践

　毎日の授業で児童生徒に手渡す「ワークシート」や「配布プリント」。

　文字の大きさ、余白、罫線の種類、そして図やイラストの配置をほんの少し工夫するだけで、子供たちの理解度や学習への集中力は驚くほど変わります。

　今週の授業改善コラムでは、現場の先生方が明日からの授業プリント作成ですぐに活用できる「伝わる教材デザイン」の原則と、Ban.Tai Education Designが提供するデジタル方眼紙・五線譜・観察カードツールの具体的な活用法を図解満載でお届けします。

---

# 1. 見やすいワークシートをつくる「視覚デザイン4大原則」

| 原則 | 具体的な工夫 | 期待できる効果 |
| --- | --- | --- |
| ① 整列 (Alignment) | 見出し・本文・解答欄の開始位置を左揃えで整える | 視線の迷いがなくなり、次にどこへ書けばよいかが一目で伝わる |
| ② 近接 (Proximity) | 関連する質問文と解答欄の余白を詰め、別の大問とは十分な余白（10px以上）を開ける | どの問題に答えるべきか直感的に理解できる |
| ③ コントラスト (Contrast) | 太字見出し、枠線、背景色（淡いグレー）を活かして優先度を明快にする | 重要な指示やヒントが読み飛ばされない |
| ④ 反復 (Repetition) | 全ページでフォントサイズ（本文14pt/見出し18pt）と解答枠の装飾を統一する | 安心して学習手順に集中できる |

---

# 2. 理科・生活科で活躍する「観察カード」のレイアウト図解

　理科の植物観察や生活科の探究活動では、言葉による説明と絵・図のスケッチを組み合わせるレイアウトが不可欠です。

<img src="/assets/images/columns/column-observation-card-sample.webp" alt="小中学校の理科・生活科でそのまま使える観察カードのデジタルレイアウト事例" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### 観察カード作成の3ステップ
* **ステップ1：大きなスケッチ枠**: 児童の手元で大きく自由に描けるよう、用紙中央または左側に枠を確保。
* **ステップ2：選択式チェック項目**: 「天気」「気温」「色」「触った手触り」などはチェックボックス形式で心理的負担を軽減。
* **ステップ3：気づき・疑問の記述欄**: 「驚いたこと」「なぜだろうと思ったこと」を2〜3行で書ける余白を設定。

---

# 3. 音楽科・算数科での「五線譜・方眼紙」活用法

　音楽の旋律づくりや算数の図形・グラフ学習では、自由度の高い罫線用紙が学習効果を高めます。

<img src="/assets/images/columns/column-worksheet-layout-diagram.webp" alt="ユニバーサルデザインを取り入れた五線譜・方眼紙プリントの配置構造図解" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### 五線譜メーカー・方眼紙ツールのメリット
* **五線譜の幅変更**: 低学年向けには太く広い五線譜、高学年や部活動向けには標準幅をミリ単位で調整。
* **マス目（グリッド）の表示切り替え**: 算数の立体図形描画や筆算練習用に、点線グリッドや濃淡ラインを選択。
* **PDF一元出力**: 印刷サイズ（A4/B5）に合わせた最適解像度で瞬時に作成可能。

---

# まとめ：美しいプリントが子供たちの「書く意欲」を引き出す

　整った美しいプリントを受け取ったとき、子供たちは「丁寧に書こう」「最後まで取り組もう」という気持ちになります。

　先生方のプリント作成時間を削減しつつ、最高の教材を子供たちへ届けるために、デジタルツールの力をぜひご活用ください。

### 今週の教材作成関連ツール
* [五線譜・楽譜作成メーカー](https://bantai-education-design.github.io/products/)
* [デジタル方眼紙・プリント作成ツール](https://bantai-education-design.github.io/products/)"""

article_vol10 = """　コラム第10弾
# 【授業改善・ICT活用】1人1台端末で深まる探究学習とデジタル思考ツール活用法

## ――シンキングツール・クラウド共有・動画教材を組み込んだ授業デザイン

　GIGAスクール端末の普及により、授業の中で児童生徒が自分で調べ、考え、まとめる「探究学習」が日常化しています。

　しかし、「端末で検索させて終わりになってしまう」「調べた情報をまとめる段階で手が止まってしまう」という悩みを抱える先生方も少なくありません。

　今週の第2弾コラムでは、思考を可視化する「シンキングツール」と端末の共同編集、視覚的動画教材を組み合わせた最新の授業デザインを図解とともに解説します。

---

# 1. 探究を加速させる「3大シンキングツール」と場面別活用

| 思考ツール名 | 構造・特徴 | 授業での効果的な使用場面 |
| --- | --- | --- |
| クラゲチャート | 頭部に結論、足の部分に理由や根拠を並べる | 国語の意見文作成、社会の歴史的事件の要因分析 |
| Yチャート | 思考を「見えたこと」「聞こえたこと」「感じたこと」に3分割 | 生活科・総合的な学習の体験活動後の振返り |
| ベン図 (Venn Diagram) | 2つ以上の対象の「共通点」と「相違点」を円の重なりで表現 | 理科の生物比較、英語の文化比較、算数の図形分類 |

---

# 2. デジタル思考ツールとリアルタイムクラウド共有の授業風景

　端末の画面上で思考ツールを操作し、グループ内でリアルタイムに付箋を動かし合うことで、多様な意見が活発に飛び交う協働学習が実現します。

<img src="/assets/images/columns/column-thinking-tools-inquiry-diagram.webp" alt="デジタルタブレット上でベン図やクラゲチャートを用いて探究学習を進める児童生徒の図解" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### 授業展開のポイント
* **個人思考タイム（3分）**: まずは各自でタブレット上に自分のアイデア付箋を書き出す。
* **グループ共有タイム（7分）**: 班のキャンバスに集め、似た意見をグループ化（KJ法）。
* **全体発表・クラス共有**: 画面を拡大提示しながら、他の班の工夫や発見を相互参照。

---

# 3. 視覚的アニメーション・動画解説の提示効果

　テキストや静止画だけでは伝わりにくい動的な概念（理科の天体運動、算数の立体展開図、体育の技のフォームなど）は、短尺の動画やアニメーション教材を提示することが極めて効果的です。

<img src="/assets/images/columns/column-classroom-digital-presentation.webp" alt="インタラクティブ大型ディスプレイに思考プロセスと動的教材を表示して発表する授業風景" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### 動画・視覚教材活用のコツ
* **15秒〜30秒の短尺提示**: 長い動画を見せるのではなく、ポイントとなる数秒間を繰り返し再生。
* **生徒によるスロー再生**: 端末手元で生徒自ら再生速度を落とし、動作や変化の瞬間をじっくり観察。

---

# まとめ：ツールを使いこなし「深まりのある学び」へ

　ICT機器やシンキングツールは、子供たちの頭の中にある「目に見えない思考」を表に引き出すための足場（スキャフォールディング）です。

　形だけのICT利用から一歩踏み出し、子供たちが生き生きと議論し納得解を導き出す授業づくりを応援しています。

### 関連リンク
* [Ban.Tai Education Design 授業改善ツール一覧](https://bantai-education-design.github.io/products/)
* [コラム一覧ページ](https://bantai-education-design.github.io/columns/)"""

entry_vol9 = {
    "id": "column-weekly-lesson-practice-worksheet-templates",
    "slug": "weekly-lesson-practice-worksheet-templates",
    "title": "【授業改善・教材配布】デジタル方眼紙・五線譜・観察カードで作る「伝わるプリント」設計術",
    "category": "現場の工夫",
    "categorySlug": "practice",
    "date": "2026.09.20",
    "excerpt": "小学校・中学校の授業ですぐ使えるデジタルプリント作成術。五線譜メーカー・原稿用紙・方眼紙・理科観察カードのレイアウト図解、見やすいユニバーサルデザインフォント、イラスト配置の工夫を豊富なビジュアルで徹底解説。",
    "thumbnail": "/assets/images/columns/column-weekly-lesson-worksheet-design.webp",
    "readTime": "約9分",
    "content": article_vol9,
    "tags": [
        "現場の工夫",
        "授業改善",
        "ワークシート",
        "プリント作成",
        "観察カード",
        "五線譜メーカー"
    ]
}

entry_vol10 = {
    "id": "column-weekly-lesson-ict-inquiry-tools",
    "slug": "weekly-lesson-ict-inquiry-tools",
    "title": "【授業改善・ICT活用】1人1台端末で深まる探究学習とデジタル思考ツール活用法",
    "category": "ICT教育",
    "categorySlug": "ict",
    "date": "2026.09.21",
    "excerpt": "GIGAスクール端末を活用した探究学習の実践ガイド。クラゲチャートやYチャートなどの思考ツール、児童生徒のクラウド共同編集、視覚的アニメーション・動画教材を取り入れた授業展開のポイントを図解と豊富な画像で紹介。",
    "thumbnail": "/assets/images/columns/column-weekly-lesson-ict-inquiry.webp",
    "readTime": "約8分",
    "content": article_vol10,
    "tags": [
        "ICT教育",
        "探究学習",
        "1人1台端末",
        "シンキングツール",
        "授業デザイン",
        "協働学習"
    ]
}

columns_file = "data/columns.json"
with open(columns_file, "r", encoding="utf-8") as f:
    columns = json.load(f)

# Prepend Vol 9 and Vol 10 (Vol 10 latest date 2026.09.21 first, then Vol 9 2026.09.20)
columns = [c for c in columns if c["id"] not in (entry_vol9["id"], entry_vol10["id"])]
columns.insert(0, entry_vol9)
columns.insert(0, entry_vol10)

with open(columns_file, "w", encoding="utf-8") as f:
    json.dump(columns, f, ensure_ascii=False, indent=2)

print("Successfully added Vol 9 and Vol 10 Lesson Improvement columns to data/columns.json")
