import json
import os
import re

columns_file = r"C:\Users\User\.gemini\antigravity\scratch\bantai-education-design.github.io\data\columns.json"
style_file = r"C:\Users\User\.gemini\antigravity\scratch\bantai-education-design.github.io\assets\style.css"

# 1. Update columns.json: Replace table with responsive cards in Vol 11, remove internal comment template text, update author bio to 小・中・高校教員
def update_columns_json():
    with open(columns_file, "r", encoding="utf-8") as f:
        columns = json.load(f)

    for c in columns:
        content = c.get("content", "")
        excerpt = c.get("excerpt", "")
        
        # Remove internal comment codeblocks/sections from public article content
        content = re.sub(r'#+\s*note掲載著者様への御礼・コメント送信方針[\s\S]*?(?=#+|$)', '', content)
        content = re.sub(r'#+\s*著者様へお送りしている御礼コメントの文例[\s\S]*?(?=#+|$)', '', content)
        content = re.sub(r'```text[\s\S]*?```', '', content)
        content = re.sub(r'📌\s*著者様へお送りしている御礼コメントの文例[\s\S]*?(?=\n\n|\n#|$)', '', content)
        
        # Update author bio to explicitly state 小・中・高校教員 (Elementary, JHS, HS experience)
        content = content.replace("元教員（現場指導40年）", "元小・中・高校教員（指導歴40年）")
        content = content.replace("元小中学校教員", "元小・中・高校教員")
        excerpt = excerpt.replace("元教員（現場指導40年）", "元小・中・高校教員（指導歴40年）")
        excerpt = excerpt.replace("元小中学校教員", "元小・中・高校教員")
        
        c["content"] = content
        c["excerpt"] = excerpt

    # Vol 11 Responsive Card List formatting (replace wide table with crisp cards)
    vol11_content = """　コラム第11弾
# 【note教育記事ピックアップ】直近1ヶ月の注目実践・授業改善ノート7選と考察

## ――現場の知恵が集まるnoteから：共感と学びに満ちた注目ノート7選＆磐田井の専門考察

　全国の小・中・高等学校や特別支援学校で子どもたちと向き合う先生方が、日々の授業実践や心温まるエピソードを綴られているWebノート（note.com）。

　Ban.Tai Education Designでは、今週より「週刊・note教育ノート特集」をお届けいたします。今回は初回として、直近1ヶ月間に投稿された数多くの素敵な文章の中から、私・磐田井（元小・中・高校教員・指導歴40年）が一人の教員として深く感銘を受けた**注目の7実践**をご紹介させていただきます。

---

# 全国の先生方が綴られた注目教育ノート7選

### 1. 『1人1台端末で作る小学校国語「思考を可視化する」授業デザイン』
* **著者**: 小学校教員・T先生 (note.com)
* **実践の要点**: クラウド共有キャンバスとシンキングツールを用いた児童の意見可視化
* **磐田井の感想**: 「全員の考えが画面上に並ぶことで、普段発言が苦手な児童の思考が可視化され、根拠に基づく記述力が大きく向上しています。子ども同士が画面を覗き込みながら嬉しそうに話し合う姿が目に浮かびます。」

---

### 2. 『生成AIを授業設計の「壁打ち相手」にするプロンプト技法5選』
* **著者**: 高校情報科・K教諭 (note.com)
* **実践の要点**: 発達段階に応じた問いかけ作成や、つまずき予測のアイデア出し手順
* **磐田井の感想**: 「指導案作成の時間を大幅に短縮するだけでなく、教員一人では思いつかない多角的な視点を授業に組み込める優れた活用法です。」

---

### 3. 『不登校児童へのオンライン居場所づくりと学習伴走の記録』
* **著者**: フリースクール代表・M氏 (note.com)
* **実践の要点**: メタバース空間とチャットを活用した無理のない寄り添いと学習支援
* **磐田井の感想**: 「『学校に来させる』ことだけを目指すのではなく『心の安心と学びの機会を届ける』という、多様な学びの選択肢を提示する温かい取り組みです。」

---

### 4. 『子供が夢中になって書く！理科観察カードの枠組みと問いかけ』
* **著者**: 理科専科・S先生 (note.com)
* **実践の要点**: スモールステップのチェック欄と自由スケッチ枠を組み合わせたワークシート工夫
* **磐田井の感想**: 「選択肢チェックボックスで書くハードルを下げつつ、最後の疑問記述欄で深い気づきを生み出すレイアウトの工夫が非常に秀逸です。」

---

### 5. 『教員の定時退勤を実現した校務DX：通知表・週案の自動化』
* **著者**: 中学校主幹・H教諭 (note.com)
* **実践の要点**: クラウドスプレッドシート関数やテンプレートを活用した校務集計の高速化
* **磐田井の感想**: 「事務作業の時間を半減させ、生まれた貴重な時間を生徒たちと直接お話しする時間に向答えている点に、学校DXの真の価値があります。」

---

### 6. 『地域連携・探究学習プロジェクトで失敗から学んだこと』
* **著者**: 探究コーディネーター・Y氏 (note.com)
* **実践の要点**: 地元企業・自治体と連携する際の合意形成と生徒の主体性サポート
* **磐田井の感想**: 「大人の都合や出来レースにならず、生徒自身が失敗を乗り越えて主人公となる探究プロセスの作り方に深感服いたしました。」

---

### 7. 『特別支援学級でのユニバーサルデザイン教材と視覚的支援』
* **著者**: 特支学校・N先生 (note.com)
* **実践の要点**: 色使い・アイコン・手順カード・UDフォントを合わせた安心できる学習環境
* **磐田井の感想**: 「特別な支援が必要な子だけでなく、クラス全員にとって分かりやすい『ユニバーサルデザイン授業』の原点です。」

---

# ノートを拝読して見えてきた3つの素晴らしい潮流

<img src="/assets/images/columns/column-note-curation-matrix.webp" alt="ICT教育・授業デザイン・働き方改革・特別支援の4領域に整理されたnote記事キュレーション図" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### 1. 「子どもの思い」を引き出すデジタルツールの活用（No.1, No.2, No.4）
　端末をただ使うのではなく、「子どもの頭の中にある思考を表に引き出し、友達と見せ合えるようにする」という目的を持って工夫されている点が大変素晴らしいと感じました。

### 2. 先生の心と体にゆとりを生む校務の工夫（No.5）
　ルーティン作業をデジタルで賢く短縮し、定時退勤やリフレッシュの時間を確保することは、巡り巡って子どもたちへの優しい笑顔と丁寧な指導につながります。

---

# おわりに

　小・中・高校の現場で先生方が生み出される知恵や心温まる言葉は、これからの教育を照らす大きな宝物です。

　これからも毎週日曜日、全国の先生方の実践ノートを楽しく拝読し、ご紹介してまいります。同時公開の**【教育最前線・現場の想い】**も併せてぜひお読みください。

### 関連リンク
* [Vol 12: 【教育最前線・現場の想い】noteの実践から読み解く日本の教師の情熱](https://bantai-education-design.github.io/columns/)
* [Ban.Tai Education Design 公式ツール一覧](https://bantai-education-design.github.io/products/)"""

    for i, c in enumerate(columns):
        if c.get("id") == "column-note-education-monthly-curation-vol11":
            columns[i]["content"] = vol11_content
            columns[i]["excerpt"] = "小・中・高校の先生方がnoteに投稿された教育ノートの中から、授業改善や学級経営に役立つ注目の7実践をご紹介。指導歴40年（小中高経験）の磐田井による温かい共感コメントを掲載。"

    with open(columns_file, "w", encoding="utf-8") as f:
        json.dump(columns, f, ensure_ascii=False, indent=2)

    print("Updated columns.json: Removed internal templates, formatted Vol 11 as responsive card lists, updated bio to 小・中・高校教員.")

# 2. Add Responsive & No-Horizontal-Scroll CSS to style.css
def update_style_css():
    with open(style_file, "r", encoding="utf-8") as f:
        css = f.read()

    modal_responsive_css = """

/* === Column Modal Responsive & No Horizontal Scroll Fix === */
.column-modal-dialog {
  overflow-x: hidden !important;
  max-width: 860px;
}

.column-modal-text {
  overflow-x: hidden !important;
  word-break: break-word;
  overflow-wrap: break-word;
}

.column-modal-text pre,
.column-modal-text code {
  max-width: 100%;
  white-space: pre-wrap !important;
  word-break: break-word !important;
  overflow-x: hidden !important;
  background: #f1f5f9;
  border-radius: 6px;
  padding: 12px;
  font-family: inherit;
}

.column-table-responsive {
  width: 100%;
  overflow-x: auto;
  margin: 1.5rem 0;
  -webkit-overflow-scrolling: touch;
}

.column-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
  table-layout: fixed;
  word-break: break-word;
}

.column-table th,
.column-table td {
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  vertical-align: top;
  word-break: break-word;
  white-space: normal;
}

@media (max-width: 640px) {
  .column-table {
    display: block;
    width: 100%;
  }
  .column-table tr {
    display: block;
    margin-bottom: 1rem;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px;
  }
  .column-table td, .column-table th {
    display: block;
    border: none;
    padding: 4px 6px;
  }
}
"""

    if "/* === Column Modal Responsive & No Horizontal Scroll Fix === */" not in css:
        css += modal_responsive_css
        with open(style_file, "w", encoding="utf-8") as f:
            f.write(css)
        print("Updated style.css with responsive no-horizontal-scroll modal rules.")
    else:
        print("style.css already contains modal responsive rules.")

if __name__ == "__main__":
    update_columns_json()
    update_style_css()
