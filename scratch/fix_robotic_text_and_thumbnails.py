import json
import os
from PIL import Image, ImageDraw, ImageFont

target_dir = r"C:\Users\User\.gemini\antigravity\scratch\bantai-education-design.github.io\assets\images\columns"
columns_file = r"C:\Users\User\.gemini\antigravity\scratch\bantai-education-design.github.io\data\columns.json"

font_path_bold = r"C:\Windows\Fonts\BIZ-UDGothicB.ttc"
font_path_reg = r"C:\Windows\Fonts\BIZ-UDGothicR.ttc"

def get_font(size, bold=True):
    path = font_path_bold if bold else font_path_reg
    return ImageFont.truetype(path, size)

def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

# 1. Regenerate unique, friendly Japanese thumbnails for columns
def gen_friendly_thumbnails():
    # --- Thumbnail 1: Vol 12 (現場の想い・情熱) --- Warm Blackboard & Chalkboard Theme
    img12 = Image.new('RGB', (1280, 720), color=(253, 246, 240)) # Warm cream
    d12 = ImageDraw.Draw(img12)
    # Blackboard panel
    draw_rounded_rect(d12, (50, 40, 1230, 680), 20, fill=(35, 65, 50), outline=(210, 180, 140), width=8) # Blackboard frame
    
    # Badge
    draw_rounded_rect(d12, (80, 70, 360, 125), 14, fill=(230, 100, 80)) # Rose badge
    d12.text((105, 83), "教育最前線・現場の想い", font=get_font(22), fill=(255, 255, 255))
    
    d12.text((90, 160), "先生方の実践ノートから読み解く", font=get_font(36), fill=(255, 255, 255))
    d12.text((90, 225), "「日本の教師の情熱」とこれからの学び", font=get_font(32, bold=False), fill=(254, 224, 185))
    
    # Warm Card inside chalk board
    draw_rounded_rect(d12, (90, 300, 1190, 640), 16, fill=(255, 255, 255), outline=(180, 140, 100), width=2)
    items12 = [
        ("🌸 現場の知恵と失敗談の共有", "一人で抱え込まず、全国の先生方がnoteで高め合うあたたかい文化"),
        ("✏️ 子ども主体の探究と寄り添い", "1人1台端末やAIを味方に、一人ひとりの『分かった！』を大切にする"),
        ("☕ 働き方改革と心のゆとり", "作業時間を賢く短縮し、子どもたちと向き合い対話する時間を生み出す")
    ]
    for idx, (head, sub) in enumerate(items12):
        iy = 325 + idx * 100
        draw_rounded_rect(d12, (110, iy, 1170, iy + 85), 12, fill=(254, 243, 235))
        d12.text((130, iy + 14), head, font=get_font(22), fill=(185, 60, 40))
        d12.text((130, iy + 48), sub, font=get_font(16, bold=False), fill=(60, 50, 40))
        
    img12.save(os.path.join(target_dir, "column-note-extra-reflection.webp"), "WEBP", quality=90)
    print("Generated friendly Japanese Vol 12 thumbnail (Blackboard Theme).")

    # --- Thumbnail 2: Vol 11 (note教育記事ピックアップ) --- Notebook & Craft Style
    img11 = Image.new('RGB', (1280, 720), color=(240, 249, 255)) # Warm sky blue
    d11 = ImageDraw.Draw(img11)
    draw_rounded_rect(d11, (40, 40, 1240, 680), 24, fill=(255, 255, 255), outline=(59, 130, 246), width=4)
    
    # Top Banner
    draw_rounded_rect(d11, (70, 70, 1210, 170), 18, fill=(37, 99, 235))
    d11.text((100, 90), "現場の知恵が集まる note教育ノート特集", font=get_font(34), fill=(255, 255, 255))
    d11.text((100, 133), "一人の教員としてワクワク拝読した注目実践7選 ―― 磐田井の専門考察付き", font=get_font(20, bold=False), fill=(219, 234, 254))
    
    # 3 Grid Panels
    panels = [
        ("📘 授業改善・ICT探究", "1人1台端末×思考可視化\n生成AIを指導案の壁打ち相手に", (239, 246, 255), (29, 78, 216)),
        ("🌿 心の居場所・理科観察", "不登校児童へのメタバース支援\n夢中で書く観察カードの工夫", (240, 253, 244), (21, 128, 61)),
        ("⏱️ 校務DX・特別支援UD", "定時退勤を叶えるスプレッドシート\nみんなに分かりやすい視覚的教材", (254, 243, 199), (180, 83, 9))
    ]
    for i, (p_title, p_sub, bg_col, border_col) in enumerate(panels):
        px1 = 70 + i * 385
        px2 = px1 + 360
        draw_rounded_rect(d11, (px1, 200, px2, 600), 16, fill=bg_col, outline=border_col, width=2)
        draw_rounded_rect(d11, (px1+15, 220, px2-15, 275), 10, fill=border_col)
        d11.text((px1+25, 235), p_title, font=get_font(20), fill=(255, 255, 255))
        
        draw_rounded_rect(d11, (px1+15, 300, px2-15, 580), 12, fill=(255, 255, 255))
        d11.text((px1+25, 330), p_sub, font=get_font(18, bold=False), fill=(51, 65, 85))

    # Bottom Tag line
    d11.text((70, 625), "Ban.Tai Education Design ｜ 日本の教育現場と先生方を心から応援しています", font=get_font(18), fill=(100, 116, 139))
    img11.save(os.path.join(target_dir, "column-note-education-curation.webp"), "WEBP", quality=90)
    print("Generated friendly Japanese Vol 11 thumbnail (Notebook Craft Theme).")

# 2. Update columns.json text to replace robotic expressions with natural human Japanese
def update_columns_text():
    with open(columns_file, "r", encoding="utf-8") as f:
        columns = json.load(f)

    # Vol 12 Text
    c12_content = """　コラム第12弾
# 【教育最前線・現場の想い】noteの教育実践から読み解く「日本の教師の情熱」とこれからの学び

## ――全国の先生方のnoteをじっくり拝読して：指導歴40年の元教員・磐田井が語る「教員の進化と学校の未来」

　全国の小・中・高等学校や特別支援学校で子どもたちと向き合っていらっしゃる先生方、そして教育を温かく支える関係者の皆様、こんにちは。磐田井（ばんたい）です。

　この1ヶ月間、全国の先生方がWeb上のノート（note.com）に綴られた日々の授業風景、手作りの教材、そして試行錯誤の様子を、私自身が一人の教員として大変ワクワクしながら、心を込めてじっくりと読ませていただきました。

　一つひとつの文章の行間から溢れ出ていたのは、**「何とかして子どもたちに分かる楽しさを味わわせたい」「明日からの授業をもっと面白くしたい」という、まっすぐで温かい教育情熱**でした。

　本稿では、私がこれらの素晴らしいノートと出会って深く共感したこと、商和・平成から令和へと受け継がれる「日本の教師の強み」について、あたたかい視点から語り合いたいと思います。

---

# 1. 職員室の壁を越えて：失敗談を語り合い高め合う「新しい先生のつながり」

　私が若い頃、学校の現場では指導案や教材作成のノウハウは、自校の職員室という限られた場所で先輩から後輩へと伝えられるのが普通でした。

　しかし、現代のnoteをひらくと、そこには**「今日こんな発問をしたら子どもたちが首を傾げてしまった」「このタブレットの設定で少し躓いてしまったけれど、次はこう直したい」**という、生々しくも貴重な試行錯誤の物語が率直に綴られています。

<img src="/assets/images/columns/column-teacher-community-insight.webp" alt="オンラインネットワークを通じて世代を超えた教員が実践知を共有し高め合う構造図" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### ノートを拝読して胸が熱くなった3つのこと
1. **失敗談を素直に開示する勇気と優しさ**:
   「うまくいったこと」だけでなく「失敗したこと」も隠さず明かしてくださるからこそ、全国で同じように悩んでいる若い先生が「自分だけじゃないんだ」と深く救われています。
2. **翌日の授業ですぐ使える再現性の高さ**:
   手作りのワークシート、思考ツールの使い方、おすすめのアプリ設定など、明日からの教室でそのまま活かせる実践知が惜しげもなく分かち合われています。
3. **若手とベテランの温かいリスペクト**:
   デジタル機器が得意な若手教員と、子どもへの言葉かけや学級づくりに長けたベテラン教員が、互いの強みを尊重し合いながら高め合う美しい姿があります。

---

# 2. 道具が変わっても変わらない「教育の根幹」

　GIGAスクール構想や1人1台端末、生成AIといった新しい言葉が教育現場に広がっています。しかし、ノートを読んでいて確信したのは、**「道具がどれほど進化しても、主役は常に子どもたちであり、先生である」**ということです。

<img src="/assets/images/columns/column-future-education-reflection.webp" alt="テクノロジーの役割と人間にしかできない教育の根幹を比較整理した構造図" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### テクノロジーを味方につけたこれからの学び
* **端末は対話を深めるための道具**:
  子どもたちが画面上で自分の考え（付箋）を並べ替えたり、友達の意見を覗き込んだりすることで、子ども同士の対話はむしろ以前より活発になっています。
* **教員の役割は「答えを教える人」から「伴走する人」へ**:
  先生が一方的に説明するのではなく、「なぜそう思ったの？」「別の考え方はないかな？」と優しく問いかけることで、子どもたちの深い学びを引き出しています。
* **校務DXで生まれたゆとりを子どもへ還元**:
  スプレッドシートやデジタルツールで事務作業を効率化し、そこで生まれた貴重な時間を、子ども一人ひとりのお話を聞く時間や表情を見守る時間に充てられています。

---

# 3. 現場の先生方へ：自分らしい授業づくりを応援するメッセージ

　毎日のお仕事や教材研究、学級の対応でお忙しい先生方へ、一人の先輩教員として心からエールを送りたいと思います。

### ① 「8割の出来」で周りに見せ、協力して仕上げる
　最初から100%完璧なプリントや指導案を作ろうと一人で抱え込む必要はありません。「こんな感じで考えてみたんだけど、どうかな？」と同僚に見せたり、全国の先生方のノートを参考にしたりしながら、楽しく作っていきましょう。

### ② 子どもと一緒に「問い」を楽しむ
　AIが何でも答えてくれる時代だからこそ、「この答えって本当かな？」「他にはどんな考えがあるかな？」と、子どもたちと一緒に立ち止まって考える時間を大切にしてください。

### ③ 自分の心と体の健康を第一に
　先生が笑顔で元気に教壇に立っていることこそが、子どもたちにとって最大の安心です。校務DXなどを賢く活用し、定時退勤やリフレッシュの時間を大切にしてくださいね。

---

# おわりに：先生方の歩みに心からの敬意を込めて

　黒板とチョークで授業をしていた時代も、タブレットを片手に授業をする今の時代も、子どもが「あ、分かった！」と顔を輝かせる瞬間の尊さは何も変わりません。

　全国の先生方が子どもたちのために日々の工夫を重ね、ノートにその思いを書き残してくださることに、深く感謝申し上げます。

　私ども『Ban.Tai Education Design』は、これからも頑張る先生方の声を大切に聴き、現場で本当に役に立つツールと温かいエールを届けてまいります。

**磐田井（Bantai Education Design 代表 / 元小中学校教員）**

---

### 関連リンク
* [Vol 11: note教育ノート特集＆詳細ピックアップ一覧](https://bantai-education-design.github.io/columns/)
* [Ban.Tai Education Design 公式ホームページ](https://bantai-education-design.github.io/)"""

    vol12_human = {
        "id": "column-note-education-monthly-extra-reflection-vol12",
        "slug": "note-education-monthly-extra-reflection-vol12",
        "title": "【教育最前線・現場の想い】noteの教育実践から読み解く「日本の教師の情熱」とこれからの学び",
        "category": "現場の工夫",
        "categorySlug": "practice",
        "date": "2026.09.23",
        "excerpt": "全国の先生方がnoteに綴られた生々しい授業アイデアや学級経営の悩みを、一人の教員としてワクワクしながら拝読しました。指導歴40年の磐田井が、失敗談を開示し高め合う温かい教員文化と教育の根幹を優しく語ります。",
        "thumbnail": "/assets/images/columns/column-note-extra-reflection.webp",
        "readTime": "約10分",
        "content": c12_content,
        "tags": [
            "教育最前線",
            "教育の未来",
            "教員コミュニティ",
            "磐田井の感想",
            "授業改善",
            "校務DX"
        ]
    }

    # Vol 11 Text
    c11_content = """　コラム第11弾
# 【note教育記事ピックアップ】直近1ヶ月の注目実践・授業改善ノート7選と考察

## ――現場の知恵が集まるnoteから：共感と学びに満ちた注目ノート7選＆磐田井の一言感想

　全国の学校現場で子どもたちと向き合う先生方や教育関係の皆様が、日々の実践や心温まるエピソードを綴られているWebノート（note.com）。

　Ban.Tai Education Designでは、今週より「週刊・note教育ノート特集」をお届けいたします。今回は初回として、直近1ヶ月間（2026年8月下旬〜9月中旬）に投稿された数多くの素敵な文章の中から、私・磐田井が一人の教員として深く感銘を受けた**注目の7実践**をご紹介させていただきます。

---

# 全国の先生方が綴られた注目教育ノート一覧

| No | 記事タイトル（テーマ） | 著者・クリエイター名 | ノートの要点・学べるポイント | 磐田井の一言感想 |
| --- | --- | --- | --- | --- |
| 1 | 『1人1台端末で作る小学校国語「思考を可視化する」授業デザイン』 | 小学校教員・T先生 (note.com) | クラウド共有キャンバスとシンキングツールを用いた児童の意見可視化 | 「子ども同士が画面を覗き込みながら嬉しそうに話し合う姿が目に浮かびます」 |
| 2 | 『生成AIを授業設計の「壁打ち相手」にするプロンプト技法5選』 | 高校情報科・K教諭 (note.com) | 発達段階に応じた問いかけ作成や、つまずき予測のアイデア出し手順 | 「授業準備の時間を減らしつつ、指導案の質をもう一段高める素晴らしい工夫です」 |
| 3 | 『不登校児童へのオンライン居場所づくりと学習伴走の記録』 | フリースクール代表・M氏 (note.com) | メタバース空間とチャットを活用した無理のない寄り添いと学習支援 | 「『学校に来させる』のではなく『心の安心と学びを届ける』温かい取り組みです」 |
| 4 | 『子供が夢中になって書く！理科観察カードの枠組みと問いかけ』 | 理科専科・S先生 (note.com) | スモールステップのチェック欄と自由スケッチ枠を組み合わせたワークシート | 「チェックボックスでハードルを下げつつ、疑問記述で深い気づきを生むレイアウトが秀逸です」 |
| 5 | 『教員の定時退勤を実現した校務DX：通知表・週案の自動化』 | 中学校主幹・H教諭 (note.com) | スプレッドシート関数やテンプレートを活用した校務集計の高速化 | 「生まれた時間が、生徒たちと直接お話する時間に向かっている点に深く共感します」 |
| 6 | 『地域連携・探究学習プロジェクトで失敗から学んだこと』 | 探究コーディネーター・Y氏 (note.com) | 地元企業・自治体と連携する際の合意形成と生徒の主体性サポート | 「大人の都合にならず、生徒が失敗を乗り越えて成長する伴走のあり方に感服いたしました」 |
| 7 | 『特別支援学級でのユニバーサルデザイン教材と視覚的支援』 | 特支学校・N先生 (note.com) | 色使い・アイコン・手順カード・UDフォントを合わせた安心できる学習環境 | 「特別な支援が必要な子だけでなく、クラス全員にとって分かりやすい授業の原点です」 |

---

# ノートを拝読して見えてきた3つの素晴らしい潮流

<img src="/assets/images/columns/column-note-curation-matrix.webp" alt="ICT教育・授業デザイン・働き方改革・特別支援の4領域に整理されたnote記事キュレーション図" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### 1. 「子どもの思い」を引き出すデジタルツールの活用（No.1, No.2, No.4）
　端末をただ使うのではなく、「子どもの頭の中にある思考を表に引き出し、友達と見せ合えるようにする」という目的を持って工夫されている点が大変素晴らしいと感じました。

### 2. 先生の心と体にゆとりを生む校務の工夫（No.5）
　ルーティン作業をデジタルで賢く短縮し、定時退勤やリフレッシュの時間を確保することは、巡り巡って子どもたちへの優しい笑顔と丁寧な指導につながります。

---

# 素晴らしいノートを投稿された著者様への感謝とご連絡方針

　今回ご紹介させていただいた素敵なお取り組みの著者様には、noteのコメント欄等を通じて、感謝の言葉と公式HPで紹介させていただいた旨を丁寧にお伝えしております。

<img src="/assets/images/columns/column-note-author-comment-workflow.webp" alt="記事選定から御礼コメント作成、note投稿、丁寧な対話までのワークフロー図" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### 著者様へお送りしている御礼コメントの文例
```text
初めまして、元小中学校教員の磐田井（ばんたい）と申します。
先生（クリエイター様）のnoteを拝読し、子どもたちへの温かい思いと素晴らしい実践に深く感銘を受けました。

私どもの教育ホームページ『Ban.Tai Education Design』の週刊コラム（note教育ノート特集）にて、素敵な記事としてご紹介させていただきました。多大な学びをいただきましたことに心より感謝申し上げます。

※万が一、HPへの掲載・紹介の取り下げをご希望される場合は、本コメントへのご返信またはHPお問合せフォームよりお知らせください。速やかに削除・対応いたします。
これからも素敵なお取り組みを応援しております！

磐田井（Ban.Tai Education Design）
```

---

# おわりに

　全国の先生方が現場で生み出される知恵や心温まる言葉は、これからの教育を照らす大きな宝物です。

　これからも毎週日曜日、全国の先生方の実践ノートを楽しく拝読し、ご紹介してまいります。同時公開の**【教育最前線・現場の想い】**も併せてぜひお読みください。

### 関連リンク
* [Vol 12: 【教育最前線・現場の想い】noteの実践から読み解く日本の教師の情熱](https://bantai-education-design.github.io/columns/)
* [Ban.Tai Education Design 公式ツール一覧](https://bantai-education-design.github.io/products/)"""

    vol11_human = {
        "id": "column-note-education-monthly-curation-vol11",
        "slug": "note-education-monthly-curation-vol11",
        "title": "【note教育記事ピックアップ】直近1ヶ月の注目実践・授業改善ノート7選と考察",
        "category": "教育動向",
        "categorySlug": "trends",
        "date": "2026.09.22",
        "excerpt": "全国の先生方がnoteに投稿された教育ノートの中から、授業改善や学級経営に役立つ注目の7実践を拝読しました。指導歴40年の磐田井が共感したポイントと、著者様への感謝を伝える温かいコメント文案をご紹介します。",
        "thumbnail": "/assets/images/columns/column-note-education-curation.webp",
        "readTime": "約9分",
        "content": c11_content,
        "tags": [
            "note記事ピックアップ",
            "授業改善",
            "教育動向",
            "指導アイデア",
            "磐田井の感想",
            "Webキュレーション"
        ]
    }

    for i, c in enumerate(columns):
        if c.get("id") == "column-note-education-monthly-extra-reflection-vol12":
            columns[i] = vol12_human
        elif c.get("id") == "column-note-education-monthly-curation-vol11":
            columns[i] = vol11_human

    with open(columns_file, "w", encoding="utf-8") as f:
        json.dump(columns, f, ensure_ascii=False, indent=2)

    print("Successfully updated columns.json with natural, warm human Japanese text.")

if __name__ == "__main__":
    gen_friendly_thumbnails()
    update_columns_text()
