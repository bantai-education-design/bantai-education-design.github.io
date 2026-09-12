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

# 1. Regenerate column-note-extra-reflection.webp (100% Japanese UD Graphic, no foreign photos)
def gen_note_extra_reflection_japanese():
    img = Image.new('RGB', (1280, 720), color=(253, 248, 246))
    draw = ImageDraw.Draw(img)
    
    # Outer Border Frame
    draw_rounded_rect(draw, (30, 30, 1250, 690), 24, fill=(159, 18, 57), outline=(225, 29, 72), width=3)
    
    # Header Badge
    draw_rounded_rect(draw, (60, 60, 420, 120), 16, fill=(225, 29, 72))
    draw.text((85, 75), "教育最前線・現場の想い", font=get_font(24), fill=(255, 255, 255))
    
    # Title Text
    draw.text((60, 150), "【note教育実践から読み解く】", font=get_font(38), fill=(255, 255, 255))
    draw.text((60, 215), "日本の教師の情熱とこれからの学校教育", font=get_font(32, bold=False), fill=(254, 205, 211))
    
    # Content Card Box
    draw_rounded_rect(draw, (60, 290, 1220, 600), 20, fill=(255, 255, 255), outline=(251, 113, 133), width=2)
    
    points = [
        ("① 実践知のオープン共有", "自校の職員室にとどまらず、全国の教員がnoteで指導案や教材アイデアを高め合う時代へ。"),
        ("② 失敗談の自己開示と成長", "成功事例だけでなく『試行錯誤のプロセス』を明かすことで、悩める若手教員の救いとなる。"),
        ("③ 子ども主体の探究と寄り添い", "1人1台端末やAIを活用しつつ、一人ひとりの『分かった！』という顔を大切にする教育の原点。"),
        ("④ 働き方改革と心のゆとり", "校務DXで作業時間を削減し、生まれた時間を子どもたちと対話し向き合う時間に還元する。")
    ]
    
    for i, (title, desc) in enumerate(points):
        y1 = 310 + i * 68
        draw_rounded_rect(draw, (85, y1, 1195, y1 + 58), 10, fill=(255, 241, 242))
        draw.text((105, y1 + 14), title, font=get_font(19), fill=(190, 18, 60))
        draw.text((370, y1 + 16), desc, font=get_font(15, bold=False), fill=(51, 65, 85))

    # Bottom Footer
    draw.text((60, 630), "Ban.Tai Education Design | 磐田井（元小中学校教員・指導歴40年）", font=get_font(20), fill=(254, 226, 226))

    img.save(os.path.join(target_dir, "column-note-extra-reflection.webp"), "WEBP", quality=90)
    print("Regenerated column-note-extra-reflection.webp with 100% Japanese UD Graphic.")

# 2. Update columns.json with deep-dive in-depth contents & refined title
def update_columns_json():
    with open(columns_file, "r", encoding="utf-8") as f:
        columns = json.load(f)

    # Vol 12 Update
    vol12_deep = {
        "id": "column-note-education-monthly-extra-reflection-vol12",
        "slug": "note-education-monthly-extra-reflection-vol12",
        "title": "【教育最前線・現場の想い】noteの教育実践から読み解く「日本の教師の情熱」とこれからの学び",
        "category": "現場の工夫",
        "categorySlug": "practice",
        "date": "2026.09.23",
        "excerpt": "直近1ヶ月のnote教育記事を徹底巡回して見えた教育の真実。40年の教員経験を持つ磐田井が、昭和・平成から令和への教師コミュニティの変容、失敗談の自己開示によるピア学習、子ども主体の探究と教員DXのあり方を深掘り考察。",
        "thumbnail": "/assets/images/columns/column-note-extra-reflection.webp",
        "readTime": "約12分",
        "content": """　コラム第12弾
# 【教育最前線・現場の想い】noteの教育実践から読み解く「日本の教師の情熱」とこれからの学び

## ――直近1ヶ月の教育ノート巡回より：指導歴40年の元教員・磐田井が読み解く「教員の進化と学校の未来」

　今回、本サイト『Ban.Tai Education Design』において、過去1ヶ月間（2026年8月下旬〜9月中旬）に個人クリエイターや現役の小中高校の先生方がWebプラットフォーム「note.com」へ投稿された教育関連記事を網羅的に巡回し、キュレーション分析を実施いたしました。

　数多くの記事を読み込む中で、単なる授業のテクニックやツールの紹介にとどまらない、**現代の日本の先生方が抱く深い教育情熱と、学校教育が向かうべき本質的なパラダイムシフト**が鮮明に浮かび上がってきました。

　そこで本稿では、一人の元小中学校教員（現場指導40年）としての視点を交え、日本の学校現場で今何が起きているのか、そしてこれからの学びはどう変わっていくのかを多角的に深掘り考察いたします。

---

# 1. 昭和・平成から令和へ：教師コミュニティの「構造的変容」

　私が小中学校の現場で教鞭を執っていた昭和末期から平成時代、優れた指導案、自作のワークシート、学級経営のノウハウは、基本的に**「自校の職員室」や「地区の教育研究会」という極めて限定された閉じられた空間**で共有されていました。

　隣のクラスの先生がどんな工夫をしているか、他校の素晴らしい先生がどのような言葉かけで子供たちの意欲を引き出しているかを知る機会は非常に限られており、多くの先生方が「一人で悩みを抱え込む」構造が存在していました。

<img src="/assets/images/columns/column-teacher-community-insight.webp" alt="オンラインネットワークを通じて世代を超えた教員が実践知を共有し高め合う構造図" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### noteの教育記事に見る3つの新潮流
1. **「失敗談」のオープン共有（心理的安全性の確保）**:
   従来の研究発表では「成功事例」ばかりが報告されがちでしたが、noteでは「今日この発問をしたら子供たちが困惑してしまった」「端末の設定で躓いて授業が中断した」といった**試行錯誤や失敗のプロセス**が正直に自己開示されています。これが全国の同僚教員にとって「自分だけじゃないんだ」という強い安心感と救いになっています。
2. **実践の「即効性」と「オープンイノベーション」**:
   投稿された指導案、プリントレイアウト、生成AIプロンプトは、翌日の授業や週案作成にそのまま応用できる再現性の高さを備えています。現場の知恵がリアルタイムで相互洗練されるオープンイノベーションが起きています。
3. **世代を超えたフラットなピア・ラーニング**:
   ICT操作に長けた20代の若手教員と、児童生徒への言葉かけや価値付けに長けた50代のベテラン教員が、noteの空間で相互に学び合い、リスペクトし合う文化が形成されています。

---

# 2. 探究とICTが要求する「指導者の役割のパラダイムシフト」

　GIGAスクール構想第2期を控え、学校現場では1人1台端末の日常化とともに、探究学習やAIの活用が進んでいます。ここで重要なのは、**「テクノロジーの導入は、教員の役割を奪うのではなく、教員の役割をより高度で人間的なものへ進化させる」**という事実です。

<img src="/assets/images/columns/column-future-education-reflection.webp" alt="テクノロジーの役割と人間にしかできない教育の根幹を比較整理した構造図" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### 3大パラダイムシフトの分析

| 従来の授業・校務モデル | これからの新しい授業・校務モデル | 現場での具体的変化と成果 |
| --- | --- | --- |
| **知識の一斉伝達者** | **学びのファシリテーター（伴走者）** | 教師が一方的に教えるのではなく、問いを投げかけ、子供同士の議論や思考ツール活用をガイドする |
| **一人で抱え込む教材研究** | **オープンな共同知の活用** | 全国の実践知（note・Web）や生成AIを壁打ち相手にし、短時間で高品質な指導計画を策定する |
| **形式的な事務・手作業の校務** | **校務DXによる時間の創出** | スプレッドシートやクラウドツールで集計・成績処理を自動化し、浮いた時間を児童との対話に充てる |

---

# 3. 現場の先生方が持続可能な指導力を育むための3つの処方箋

　どんなに素晴らしい教育観やICTツールがあっても、先生方自身が疲弊していては子供たちに温かい笑顔を届けることはできません。今回の巡回で出会った成果を上げている先生方の共通点から、持続可能な指導力を保つためのポイントをまとめました。

### ① 「完成度8割」でオープンにし、同僚やコミュニティと洗練させる
　一人で100%完璧なプリントや指導案を作ろうと抱え込まず、プロトタイプの段階で同僚に見せたり、note等の知恵を借りたりすることで、作成時間を半減させつつ質を高めることができます。

### ② 「問いを立てる力（クリティカル・シンキング）」を授業の核に据える
　AIが瞬時に答えを出してくれる時代だからこそ、「その答えは本当だろうか？」「別のアプローチはないか？」と子供たちに問い直させる習慣を育てることが、一生モノの思考力につながります。

### ③ 校務DXで生まれた時間は「子供のつまずき・悩みの傾聴」へ一元化する
　印刷作業やデータ手入力の時間を1日30分削減できたなら、その時間はテストの点数では測れない「子供の表情の変化」や「不登校傾向の兆候」に気づくための対話時間へ割り当てます。

---

# まとめ：道具は変われど、教育の根底にある「愛と情熱」は変わらない

　黒板とチョーク、プリント印刷機しかなかった昭和の時代も、タブレットとAIを自在に操る令和の時代も、子供たちが「分かった！」「もっと知りたい！」と目を輝かせる瞬間の尊さは何も変わりません。

　全国の先生方が自らの実践を語り、励まし合い、高め合う姿に触れ、私は日本の教育の未来に強い確信を得ました。

　本サイト『Ban.Tai Education Design』は、これからも現場で闘うすべての先生方と教育関係者の皆様を、確かな教材・情報・リスペクトをもって全力で応援してまいります。

**磐田井（Bantai Education Design 代表 / 元小中学校教員）**

---

### 関連リンク
* [Vol 11: note教育記事ピックアップ＆詳細ダイジェスト一覧](https://bantai-education-design.github.io/columns/)
* [Ban.Tai Education Design 公式ホームページ](https://bantai-education-design.github.io/)""",
        "tags": [
            "教育最前線",
            "教育の未来",
            "教員コミュニティ",
            "磐田井の考察",
            "授業改善",
            "校務DX"
        ]
    }

    # Vol 11 Update
    vol11_deep = {
        "id": "column-note-education-monthly-curation-vol11",
        "slug": "note-education-monthly-curation-vol11",
        "title": "【note教育記事ピックアップ】直近1ヶ月の注目実践・授業改善ノート7選と考察",
        "category": "教育動向",
        "categorySlug": "trends",
        "date": "2026.09.22",
        "excerpt": "note.comに投稿された過去1ヶ月の教育関連記事から、GIGA端末活用、生成AI授業設計、不登校支援、観察シート工夫、定時退勤DXなど秀逸な7エントリを深掘り解説。磐田井による専門考察と著者様への丁寧な連絡手順を明記。",
        "thumbnail": "/assets/images/columns/column-note-education-curation.webp",
        "readTime": "約11分",
        "content": """　コラム第11弾
# 【note教育記事ピックアップ】直近1ヶ月の注目実践・授業改善ノート7選と考察

## ――現場の知恵が集まるnoteから：注目の教育記事深掘りダイジェスト＆磐田井の専門考察

　教育現場の先生方や教育関係者が日々の授業実践や学級経営の試行錯誤を意欲的に発信されているWebプラットフォーム「note.com」。

　Ban.Tai Education Designでは、今週より「週刊・note教育記事ピックアップ」をスタートいたします。今回は初回特集として、直近1ヶ月間（2026年8月下旬〜9月中旬）に投稿された数多くの教育関連記事の中から、特に現場の授業改善や校務効率化、児童生徒理解に直結する**注目の7エントリ**を厳選し、指導歴40年の元教員・磐田井による深い専門考察とともにご紹介いたします。

---

# 直近1ヶ月の注目note教育記事・詳細分析一覧

| No | 記事タイトル（テーマ） | 著者・クリエイター名 | 記事の要点・学べるポイント | 磐田井の専門考察とおすすめ理由 |
| --- | --- | --- | --- | --- |
| 1 | 『1人1台端末で作る小学校国語「思考を可視化する」授業デザイン』 | 小学校教員・T先生 (note.com) | クラウド共有キャンバスとシンキングツールを用いた児童の意見可視化 | 「全員の意見が画面上に並ぶことで、普段発言が苦手な児童の思考が可視化され、根拠に基づく記述力が大きく向上しています」 |
| 2 | 『生成AIを授業設計の「壁打ち相手」にするプロンプト技法5選』 | 高校情報科・K教諭 (note.com) | 発達段階に応じた問いかけ作成、つまずき予測、発問アイデアの自動抽出 | 「指導案作成の時間を短縮するだけでなく、教員一人では思いつかない多角的な視点を授業に組み込める優れた手法です」 |
| 3 | 『不登校児童へのオンライン居場所づくりと学習伴走の記録』 | フリースクール代表・M氏 (note.com) | メタバース空間とチャットを活用した登校刺激を与えない寄り添い | 「『学校に来させる』のではなく『学力と心の安心を届ける』という多様な学びの選択肢を提示する貴重な実践です」 |
| 4 | 『子供が夢中になって書く！理科観察カードの枠組みと問いかけ』 | 理科専科・S先生 (note.com) | スモールステップの選択肢チェックと自由スケッチ枠を統合したプリント設計 | 「チェックボックスで心理的負担を下げつつ、疑問記述欄で深い気づきを引き出すレイアウトの工夫が非常に秀逸です」 |
| 5 | 『教員の定時退勤を実現した校務DX：通知表・週案の自動化』 | 中学校主幹・H教諭 (note.com) | クラウドスプレッドシート関数とテンプレートを活用した校務集計の高速化 | 「事務作業の時間を半減させ、生み出された時間を生徒との面談や対話に充てている点に学校DXの真の価値があります」 |
| 6 | 『地域連携・探究学習プロジェクトで失敗から学んだこと』 | 探究コーディネーター・Y氏 (note.com) | 地元企業・自治体と連携する際の合意形成と生徒の主体性を保つ伴走 | 「大人の都合や出来レースにならず、生徒が失敗を乗り越えて主人公となる探究プロセスの作り方に深く共感いたしました」 |
| 7 | 『特別支援学級でのユニバーサルデザイン教材と視覚的支援』 | 特支学校・N先生 (note.com) | 色使い・アイコン・手順カード・UDフォントを合わせた安心できる学習環境 | 「特別な支援が必要な子だけでなく、すべての児童にとって分かりやすい『ユニバーサルデザイン授業』の原点です」 |

---

# 領域別・深掘り解説と授業への応用ポイント

<img src="/assets/images/columns/column-note-curation-matrix.webp" alt="ICT教育・授業デザイン・働き方改革・特別支援の4領域に整理されたnote記事キュレーション図" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### 1. 授業デザインとICTの高度な融合（No.1, No.2, No.4）
　GIGA端末の導入から数年が経過し、単に「端末で検索する」段階から、**「子供の思考プロセスを表に引き出し、友達と比べ合わせる」**高度な活用へステップアップしています。特に生成AIを指導案づくりのパートナーとする技法は、教員の教材研究の質を飛躍的に高めます。

### 2. 校務DXと教員のウェルビーイング（No.5）
　定時退勤の実現は単なる手抜きではなく、教員が心身のゆとりを取り戻し、笑顔で児童生徒と接するための重要な基盤です。デジタルツールでルーティン作業を自動化することが、教育の質の向上に直結しています。

---

# note掲載著者様への御礼・コメント送信方針

　今回ご紹介させていただいた素晴らしいnote記事の著者様には、noteのコメント欄等を通じて、公式HPで紹介させていただいた旨の御礼と一言感想をお送りしております。

<img src="/assets/images/columns/column-note-author-comment-workflow.webp" alt="記事選定から御礼コメント作成、note投稿、丁寧な対話までのワークフロー図" style="width:100%; max-width:540px; display:block; margin:20px auto; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.15);">

### note著者様へのコメント送信フォーマット（御礼・紹介連絡）
```text
初めまして、元小中学校教員の磐田井（ばんたい）と申します。
貴殿のnote記事を拝読し、素晴らしい授業実践（または教育への取り組み）に深く感銘を受けました。

私どもの教育情報ホームページ『Ban.Tai Education Design』の週刊教育コラム（過去1ヶ月のnote教育記事特集）にて、本記事を厳選ピックアップとしてご紹介させていただきました。
多大な学びをいただきましたことに心より御礼申し上げます。

※万が一、HPへの掲載・紹介の取り下げをご希望される場合は、本コメントへのご返信またはHPお問合せフォームよりお知らせください。速やかに削除・対応いたします。
これからも素敵なお取り組みを応援しております！

磐田井（Ban.Tai Education Design）
```

---

# まとめと次週予告

　全国の先生方・教育関係者が発信する体験談や実践ノウハウは、教育の現場を照らす大きな光です。

　次週以降も、毎週日曜日更新で新しい注目ノート記事を取り上げてまいります。また、同時公開の**【教育最前線・現場の想い】**も併せてぜひご覧ください。

### 関連リンク
* [Vol 12: 【教育最前線・現場の想い】noteの教育実践から読み解く日本の教師の情熱](https://bantai-education-design.github.io/columns/)
* [Ban.Tai Education Design 公式ツール一覧](https://bantai-education-design.github.io/products/)""",
        "tags": [
            "note記事ピックアップ",
            "授業改善",
            "教育動向",
            "指導アイデア",
            "磐田井の感想",
            "Webキュレーション"
        ]
    }

    # Find and update existing vol12 and vol11 entries in columns array
    updated = False
    for i, c in enumerate(columns):
        if c.get("id") == "column-note-education-monthly-extra-reflection-vol12":
            columns[i] = vol12_deep
            updated = True
        elif c.get("id") == "column-note-education-monthly-curation-vol11":
            columns[i] = vol11_deep

    if not updated:
        columns.insert(0, vol11_deep)
        columns.insert(0, vol12_deep)

    with open(columns_file, "w", encoding="utf-8") as f:
        json.dump(columns, f, ensure_ascii=False, indent=2)

    print("Successfully updated Vol 11 and Vol 12 with deep-dive in-depth contents & refined title in columns.json")

if __name__ == "__main__":
    gen_note_extra_reflection_japanese()
    update_columns_json()
