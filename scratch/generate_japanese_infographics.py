import os
from PIL import Image, ImageDraw, ImageFont

target_dir = r"C:\Users\User\.gemini\antigravity\scratch\bantai-education-design.github.io\assets\images\columns"
font_path_bold = r"C:\Windows\Fonts\BIZ-UDGothicB.ttc"
font_path_reg = r"C:\Windows\Fonts\BIZ-UDGothicR.ttc"

def get_font(size, bold=True):
    path = font_path_bold if bold else font_path_reg
    return ImageFont.truetype(path, size)

def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

# 1. column-note-curation-matrix.webp
def gen_note_curation_matrix():
    img = Image.new('RGB', (1280, 720), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Header Banner
    draw_rounded_rect(draw, (40, 30, 1240, 110), 16, fill=(30, 58, 138))
    draw.text((60, 48), "注目教育実践・note記事キュレーション（直近1ヶ月特集）", font=get_font(32), fill=(255, 255, 255))
    draw.text((950, 58), "Ban.Tai Education", font=get_font(20), fill=(191, 219, 254))
    
    # 4 Category Cards
    cats = [
        ("① ICT教育・端末活用", (239, 246, 255), (29, 78, 216), [
            "・1人1台端末による探究学習",
            "・クラウドリアルタイム協働編集",
            "・思考ツール（ベン図等）の導入"
        ]),
        ("② 授業デザイン・教材", (240, 253, 244), (21, 128, 61), [
            "・生成AIを「壁打ち相手」に",
            "・子供が夢中になる観察カード",
            "・伝わるワークシートレイアウト"
        ]),
        ("③ 働き方改革・校務DX", (254, 243, 199), (180, 83, 9), [
            "・定時退勤を実現する校務自動化",
            "・スプレッドシート週案・成績処理",
            "・生み出した時間の生徒対応へ"
        ]),
        ("④ 特別支援・学級経営", (250, 245, 255), (126, 34, 206), [
            "・視覚的UD教材と安心の環境",
            "・メタバース不登校居場所づくり",
            "・地域連携探究プロジェクト"
        ])
    ]
    
    for i, (title, bg_color, title_color, points) in enumerate(cats):
        x1 = 40 + i * 295
        x2 = x1 + 280
        y1 = 135
        y2 = 640
        draw_rounded_rect(draw, (x1, y1, x2, y2), 14, fill=bg_color, outline=(226, 232, 240), width=2)
        
        # Header box in card
        draw_rounded_rect(draw, (x1+10, y1+15, x2-10, y1+65), 8, fill=title_color)
        draw.text((x1+20, y1+25), title, font=get_font(18), fill=(255, 255, 255))
        
        # Points
        for j, pt in enumerate(points):
            py = y1 + 90 + j * 95
            draw_rounded_rect(draw, (x1+15, py, x2-15, py+80), 8, fill=(255, 255, 255), outline=(203, 213, 225), width=1)
            lines = pt.split(" ")
            draw.text((x1+25, py+15), pt, font=get_font(15, bold=False), fill=(30, 41, 59))
            
    # Footer
    draw.text((40, 665), "※各記事の著者様へは公式HP掲載の御礼と一言感想をお送りしております（取り下げ希望時は即時削除対応）", font=get_font(16, bold=False), fill=(100, 116, 139))
    img.save(os.path.join(target_dir, "column-note-curation-matrix.webp"), "WEBP", quality=90)
    print("Generated column-note-curation-matrix.webp")

# 2. column-note-author-comment-workflow.webp
def gen_note_author_comment_workflow():
    img = Image.new('RGB', (1280, 720), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Header Banner
    draw_rounded_rect(draw, (40, 30, 1240, 110), 16, fill=(15, 118, 110))
    draw.text((60, 48), "note著者様への御礼・丁寧なコミュニケーションフロー", font=get_font(32), fill=(255, 255, 255))
    
    steps = [
        ("ステップ 1", "注目の教育記事選定", "note.comから現場に役立つ\n優れた実践ノウハウを発見", (204, 251, 241), (13, 148, 136)),
        ("ステップ 2", "御礼文章の作成", "感謝の言葉と磐田井の\n一言感想を心を込めて執筆", (207, 250, 254), (8, 145, 178)),
        ("ステップ 3", "noteコメント欄送信", "公式HPで紹介した旨と\n掲載URLをご報告", (224, 231, 255), (67, 56, 202)),
        ("ステップ 4", "誠実な対話・対応", "著者様の意図を最優先にし\n辞退時は即時削除対応", (254, 226, 226), (220, 38, 38))
    ]
    
    for i, (step_num, title, desc, bg_col, text_col) in enumerate(steps):
        x1 = 50 + i * 295
        x2 = x1 + 265
        y1 = 150
        y2 = 560
        draw_rounded_rect(draw, (x1, y1, x2, y2), 16, fill=bg_col, outline=(203, 213, 225), width=2)
        
        # Step badge
        draw_rounded_rect(draw, (x1+20, y1+25, x1+140, y1+65), 20, fill=text_col)
        draw.text((x1+35, y1+33), step_num, font=get_font(18), fill=(255, 255, 255))
        
        # Title
        draw.text((x1+20, y1+90), title, font=get_font(20), fill=(30, 41, 59))
        
        # Content box
        draw_rounded_rect(draw, (x1+15, y1+150, x2-15, y2-20), 12, fill=(255, 255, 255), outline=(226, 232, 240), width=1)
        draw.text((x1+25, y1+175), desc, font=get_font(16, bold=False), fill=(51, 65, 85))
        
        # Draw Arrow to next step
        if i < 3:
            ax1 = x2 + 5
            ax2 = ax1 + 20
            ay = (y1 + y2) // 2
            draw.polygon([(ax1, ay-15), (ax2, ay), (ax1, ay+15)], fill=(100, 116, 139))
            
    # Bottom Alert Banner
    draw_rounded_rect(draw, (50, 590, 1230, 670), 12, fill=(254, 242, 242), outline=(248, 113, 113), width=2)
    draw.text((70, 615), "【安心・誠実のお約束】掲載を取り下げたい場合は、コメントご返信またはHPフォームよりご連絡頂ければ即時削除いたします。", font=get_font(17), fill=(153, 27, 27))

    img.save(os.path.join(target_dir, "column-note-author-comment-workflow.webp"), "WEBP", quality=90)
    print("Generated column-note-author-comment-workflow.webp")

# 3. column-teacher-community-insight.webp
def gen_teacher_community_insight():
    img = Image.new('RGB', (1280, 720), color=(245, 247, 250))
    draw = ImageDraw.Draw(img)
    
    # Title Banner
    draw_rounded_rect(draw, (40, 30, 1240, 110), 16, fill=(67, 56, 202))
    draw.text((60, 48), "つながり高め合う「新しい教師コミュニティ」の構造", font=get_font(32), fill=(255, 255, 255))
    
    # Center Hub Box
    draw_rounded_rect(draw, (460, 270, 820, 470), 24, fill=(99, 102, 241), outline=(67, 56, 202), width=3)
    draw.text((505, 330), "オープンな実践知", font=get_font(28), fill=(255, 255, 255))
    draw.text((525, 385), "(note / Web発信)", font=get_font(22), fill=(224, 231, 255))
    
    # 4 Outer Nodes
    nodes = [
        ("失敗談と試行錯誤の開示", "成功例だけでなく悩みや失敗もオープンにし\n全国の悩める先生の救いになっている", (60, 160, 420, 320), (239, 246, 255), (29, 78, 216)),
        ("再現性の高い指導アイデア", "明日からの授業プリントやICT設定に\nそのまま活用できる実践例が満載", (860, 160, 1220, 320), (240, 253, 244), (21, 128, 61)),
        ("世代を超えたノウハウ共有", "若手・中堅・ベテランがフラットに学び合い\n校務DXや授業改善を高め合う", (60, 420, 420, 580), (254, 243, 199), (180, 83, 9)),
        ("子どもへの温かい情熱", "「わかる楽しさを味わわせたい」という\n教育の原点がどの文章からも溢れている", (860, 420, 1220, 580), (250, 245, 255), (126, 34, 206))
    ]
    
    for title, desc, (x1, y1, x2, y2), bg_col, t_col in nodes:
        draw_rounded_rect(draw, (x1, y1, x2, y2), 16, fill=bg_col, outline=t_col, width=2)
        draw.text((x1+20, y1+20), title, font=get_font(20), fill=t_col)
        draw.text((x1+20, y1+65), desc, font=get_font(15, bold=False), fill=(51, 65, 85))
        
    # Quote Box at bottom
    draw_rounded_rect(draw, (40, 610, 1240, 680), 12, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.text((60, 630), "「道具や環境が変わっても、子どもの成長を願う情熱は変わらない」 ―― 磐田井（元小中学校教員）", font=get_font(18), fill=(30, 41, 59))

    img.save(os.path.join(target_dir, "column-teacher-community-insight.webp"), "WEBP", quality=90)
    print("Generated column-teacher-community-insight.webp")

# 4. column-future-education-reflection.webp
def gen_future_education_reflection():
    img = Image.new('RGB', (1280, 720), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Title Banner
    draw_rounded_rect(draw, (40, 30, 1240, 110), 16, fill=(194, 65, 12))
    draw.text((60, 48), "これからの学校教育とテクノロジーの調和", font=get_font(32), fill=(255, 255, 255))
    
    # Left Box (AI & Tech)
    draw_rounded_rect(draw, (60, 150, 610, 570), 20, fill=(255, 247, 237), outline=(249, 115, 22), width=3)
    draw_rounded_rect(draw, (80, 170, 590, 230), 10, fill=(249, 115, 22))
    draw.text((160, 185), "テクノロジー・AIの役割", font=get_font(24), fill=(255, 255, 255))
    
    ai_points = [
        "・データ処理・自動集計・成績管理",
        "・授業案や類題テンプレートの下案生成",
        "・個別最適な練習問題とヒントの提示",
        "・校務DXによる教員の作業時間削減"
    ]
    for k, pt in enumerate(ai_points):
        draw_rounded_rect(draw, (90, 260 + k*75, 580, 320 + k*75), 8, fill=(255, 255, 255), outline=(253, 186, 116), width=1)
        draw.text((105, 275 + k*75), pt, font=get_font(17, bold=False), fill=(51, 65, 85))
        
    # Right Box (Human Education)
    draw_rounded_rect(draw, (670, 150, 1220, 570), 20, fill=(240, 253, 244), outline=(34, 197, 94), width=3)
    draw_rounded_rect(draw, (690, 170, 1200, 230), 10, fill=(34, 197, 94))
    draw.text((750, 185), "人間にしかできない教育の根幹", font=get_font(24), fill=(255, 255, 255))
    
    human_points = [
        "・児童生徒の表情を見守る寄り添いと共感",
        "・温かい対話と学級の安心できる雰囲気づくり",
        "・問いを立てる批判的思考力・倫理観の育成",
        "・一人ひとりの強みを引き出すキャリア伴走"
    ]
    for k, pt in enumerate(human_points):
        draw_rounded_rect(draw, (700, 260 + k*75, 1190, 320 + k*75), 8, fill=(255, 255, 255), outline=(134, 239, 172), width=1)
        draw.text((715, 275 + k*75), pt, font=get_font(17, bold=False), fill=(51, 65, 85))

    # Bottom Banner
    draw_rounded_rect(draw, (60, 600, 1220, 670), 12, fill=(30, 41, 59))
    draw.text((280, 623), "「テクノロジーは道具であり、主役は子どもと教員である」", font=get_font(22), fill=(255, 255, 255))

    img.save(os.path.join(target_dir, "column-future-education-reflection.webp"), "WEBP", quality=90)
    print("Generated column-future-education-reflection.webp")

# 5. column-note-extra-reflection.webp
def gen_note_extra_reflection():
    img = Image.new('RGB', (1280, 720), color=(253, 248, 246))
    draw = ImageDraw.Draw(img)
    
    # Title Header
    draw_rounded_rect(draw, (50, 40, 1230, 130), 16, fill=(159, 18, 57))
    draw.text((80, 60), "【番外コラム】1ヶ月の教育ノート巡回を終えて", font=get_font(32), fill=(255, 255, 255))
    draw.text((80, 100), "教育の未来を照らす現場の知恵と感謝のメッセージ", font=get_font(18), fill=(254, 205, 211))
    
    # Main Note Book Box
    draw_rounded_rect(draw, (80, 160, 1200, 580), 20, fill=(255, 255, 255), outline=(251, 113, 133), width=2)
    
    items = [
        ("● 現場の情熱に触れて", "若手からベテランまで、日々の成功や悩みを正直に発信し高め合う姿に深く感動いたしました。"),
        ("● 子どもが主役の学び", "1人1台端末やAIなどの新しい道具も、子供が『分かった！』と輝く瞬間のために使われています。"),
        ("● 発信者様へのリスペクト", "素晴らしい実践知を共有してくださるクリエイターの皆様に、心より敬意と御礼を申し上げます。")
    ]
    for m, (h, b) in enumerate(items):
        iy = 190 + m * 125
        draw_rounded_rect(draw, (110, iy, 1170, iy + 105), 12, fill=(255, 241, 242))
        draw.text((130, iy + 18), h, font=get_font(22), fill=(190, 18, 60))
        draw.text((130, iy + 58), b, font=get_font(17, bold=False), fill=(51, 65, 85))

    # Signature at bottom right
    draw.text((700, 610), "磐田井（Bantai Education Design 代表 / 指導歴40年）", font=get_font(20), fill=(136, 19, 55))

    img.save(os.path.join(target_dir, "column-note-extra-reflection.webp"), "WEBP", quality=90)
    print("Generated column-note-extra-reflection.webp")

# 6. column-thinking-tools-inquiry-diagram.webp
def gen_thinking_tools_inquiry_diagram():
    img = Image.new('RGB', (1280, 720), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Title Banner
    draw_rounded_rect(draw, (40, 30, 1240, 110), 16, fill=(2, 132, 199))
    draw.text((60, 48), "授業で活躍する「3大デジタル思考ツール」活用構造図", font=get_font(30), fill=(255, 255, 255))
    
    tools = [
        ("ベン図 (Venn Diagram)", "2つ以上の対象の「共通点」と「相違点」を円の重なりで表現", [
            "・理科：昆虫とメダカの共通点",
            "・国語：2つの物語の比較",
            "・英語：文化や生活習慣の対比"
        ], (224, 242, 254), (3, 105, 161)),
        ("クラゲチャート", "頭部に結論、足の部分に理由や根拠をロジカルに配置", [
            "・国語：自分の意見と理由付け",
            "・社会：歴史的事件の要因分析",
            "・道徳：主人公の心情変化と根拠"
        ], (240, 253, 244), (21, 128, 61)),
        ("Yチャート", "思考を「見えたこと」「聞こえたこと」「感じたこと」に3分割", [
            "・生活科：町探検・自然観察の振返り",
            "・総合：体験活動後の気づき整理",
            "・美術：作品鑑賞の印象分類"
        ], (254, 243, 199), (180, 83, 9))
    ]
    
    for i, (name, purpose, usage, bg_col, t_col) in enumerate(tools):
        x1 = 50 + i * 395
        x2 = x1 + 370
        y1 = 140
        y2 = 590
        draw_rounded_rect(draw, (x1, y1, x2, y2), 16, fill=bg_col, outline=t_col, width=2)
        
        draw_rounded_rect(draw, (x1+15, y1+15, x2-15, y1+65), 10, fill=t_col)
        draw.text((x1+25, y1+27), name, font=get_font(20), fill=(255, 255, 255))
        
        draw.text((x1+20, y1+80), purpose, font=get_font(14, bold=False), fill=(51, 65, 85))
        
        draw_rounded_rect(draw, (x1+15, y1+160, x2-15, y2-20), 10, fill=(255, 255, 255))
        draw.text((x1+25, y1+175), "【具体的な使用例】", font=get_font(16), fill=t_col)
        for u_idx, u_str in enumerate(usage):
            draw.text((x1+25, y1+215 + u_idx*45), u_str, font=get_font(15, bold=False), fill=(30, 41, 59))
            
    # Bottom Bar
    draw_rounded_rect(draw, (50, 615, 1230, 680), 12, fill=(30, 41, 59))
    draw.text((250, 637), "「端末画面上で付箋をリアルタイム共同編集し、協働学習を活性化」", font=get_font(20), fill=(255, 255, 255))

    img.save(os.path.join(target_dir, "column-thinking-tools-inquiry-diagram.webp"), "WEBP", quality=90)
    print("Generated column-thinking-tools-inquiry-diagram.webp")

# 7. column-classroom-digital-presentation.webp
def gen_classroom_digital_presentation():
    img = Image.new('RGB', (1280, 720), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Header
    draw_rounded_rect(draw, (40, 30, 1240, 110), 16, fill=(109, 40, 217))
    draw.text((60, 48), "1人1台端末×大型提示装置による協働発表授業モデル", font=get_font(30), fill=(255, 255, 255))
    
    steps = [
        ("フェーズ 1", "個人思考タイム (3分)", "まずは児童生徒各自が手元端末で\nアイデア付箋を書き出し整理する", (237, 233, 254), (124, 58, 237)),
        ("フェーズ 2", "班内共有タイム (7分)", "班の共通キャンバスに集め\n似た意見をグループ化（KJ法）", (224, 231, 255), (67, 56, 202)),
        ("フェーズ 3", "全体発表・比較 (10分)", "大型モニターに代表画面を提示し\n他の班の工夫や発見を相互参照", (254, 243, 199), (180, 83, 9))
    ]
    
    for i, (ph, title, desc, bg_col, t_col) in enumerate(steps):
        x1 = 60 + i * 390
        x2 = x1 + 360
        y1 = 150
        y2 = 540
        draw_rounded_rect(draw, (x1, y1, x2, y2), 16, fill=bg_col, outline=t_col, width=2)
        
        draw_rounded_rect(draw, (x1+20, y1+20, x1+220, y1+65), 20, fill=t_col)
        draw.text((x1+35, y1+30), ph, font=get_font(18), fill=(255, 255, 255))
        
        draw.text((x1+20, y1+90), title, font=get_font(20), fill=(30, 41, 59))
        
        draw_rounded_rect(draw, (x1+15, y1+150, x2-15, y2-20), 10, fill=(255, 255, 255))
        draw.text((x1+25, y1+180), desc, font=get_font(16, bold=False), fill=(51, 65, 85))

    # Bottom Tip
    draw_rounded_rect(draw, (60, 570, 1220, 660), 12, fill=(243, 244, 246), outline=(156, 163, 175), width=2)
    draw.text((80, 595), "【動画活用のコツ】15秒〜30秒の短尺提示 / 手元端末でのスロー再生で動作や変化の瞬間をじっくり観察", font=get_font(17), fill=(31, 41, 55))

    img.save(os.path.join(target_dir, "column-classroom-digital-presentation.webp"), "WEBP", quality=90)
    print("Generated column-classroom-digital-presentation.webp")

# 8. column-observation-card-sample.webp
def gen_observation_card_sample():
    img = Image.new('RGB', (1280, 720), color=(245, 247, 250))
    draw = ImageDraw.Draw(img)
    
    # Title
    draw_rounded_rect(draw, (40, 30, 1240, 100), 16, fill=(22, 101, 52))
    draw.text((60, 48), "理科・生活科 デジタル観察カードのレイアウト構造事例", font=get_font(28), fill=(255, 255, 255))
    
    # Simulated Observation Card Paper
    draw_rounded_rect(draw, (120, 130, 1160, 680), 16, fill=(255, 255, 255), outline=(187, 247, 208), width=3)
    
    # Card Header
    draw.text((150, 155), "【理科・観察カード】アサガオの観察記録", font=get_font(24), fill=(22, 101, 52))
    draw.text((800, 160), "日付: 2026年9月  名前: 〇〇 〇〇", font=get_font(18, bold=False), fill=(51, 65, 85))
    draw.line([(150, 195), (1130, 195)], fill=(187, 247, 208), width=2)
    
    # Box 1: Sketch area
    draw_rounded_rect(draw, (150, 220, 650, 540), 12, fill=(240, 253, 244), outline=(134, 239, 172), width=2)
    draw.text((170, 235), "【スケッチ・写真枠】（大きな絵を描く）", font=get_font(18), fill=(22, 101, 52))
    draw.text((280, 360), "（ここに観察した植物や\n　生き物の図を描く）", font=get_font(20, bold=False), fill=(100, 116, 139))
    
    # Box 2: Checkboxes
    draw_rounded_rect(draw, (680, 220, 1130, 370), 12, fill=(254, 243, 199), outline=(252, 211, 77), width=2)
    draw.text((700, 235), "【かんさつチェック】", font=get_font(18), fill=(180, 83, 9))
    draw.text((700, 280), "・天気： [✓] はれ  [ ] くもり  [ ] あめ", font=get_font(16, bold=False), fill=(30, 41, 59))
    draw.text((700, 320), "・色　： [✓] あおい  [ ] むらさき  [ ] みどり", font=get_font(16, bold=False), fill=(30, 41, 59))
    
    # Box 3: Discovery Notes
    draw_rounded_rect(draw, (680, 390, 1130, 650), 12, fill=(239, 246, 255), outline=(147, 197, 253), width=2)
    draw.text((700, 405), "【きづいたこと・ぎもん】", font=get_font(18), fill=(29, 78, 216))
    draw.text((700, 450), "1. はっぱの形が手のひらに似ている。\n2. つぼみが朝早くひらいていた。\n3. なぜつるは巻いてのびるのだろう？", font=get_font(16, bold=False), fill=(51, 65, 85))
    
    # Bottom Left Note inside card
    draw_rounded_rect(draw, (150, 560, 650, 650), 12, fill=(243, 244, 246))
    draw.text((170, 575), "★ポイント：スモールステップのチェックと大きなスケッチ枠で\n　子どもたちの『書く意欲』を引き出します。", font=get_font(15), fill=(31, 41, 55))

    img.save(os.path.join(target_dir, "column-observation-card-sample.webp"), "WEBP", quality=90)
    print("Generated column-observation-card-sample.webp")

# 9. column-worksheet-layout-diagram.webp
def gen_worksheet_layout_diagram():
    img = Image.new('RGB', (1280, 720), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Header
    draw_rounded_rect(draw, (40, 30, 1240, 110), 16, fill=(30, 58, 138))
    draw.text((60, 48), "ユニバーサルデザインを取り入れた「教材レイアウト4大原則」", font=get_font(30), fill=(255, 255, 255))
    
    principles = [
        ("① 整列 (Alignment)", "見出し・本文・解答欄の開始位置を\n左揃えに整え、視線の迷いをなくす", (239, 246, 255), (29, 78, 216)),
        ("② 近接 (Proximity)", "関連する設問と解答欄の余白を詰め\n別の大問とは10px以上の余白を開ける", (240, 253, 244), (21, 128, 61)),
        ("③ コントラスト", "太字見出し・枠線・薄グレー背景で\n優先順位と重要指示を明快にする", (254, 243, 199), (180, 83, 9)),
        ("④ 反復 (Repetition)", "全ページでフォントサイズと解答枠を\n統一し、安心して学習に集中させる", (250, 245, 255), (126, 34, 206))
    ]
    
    for i, (title, desc, bg_col, t_col) in enumerate(principles):
        x1 = 50 + i * 295
        x2 = x1 + 270
        y1 = 150
        y2 = 560
        draw_rounded_rect(draw, (x1, y1, x2, y2), 16, fill=bg_col, outline=t_col, width=2)
        
        draw_rounded_rect(draw, (x1+15, y1+15, x2-15, y1+70), 10, fill=t_col)
        draw.text((x1+20, y1+27), title, font=get_font(19), fill=(255, 255, 255))
        
        draw_rounded_rect(draw, (x1+15, y1+100, x2-15, y2-20), 10, fill=(255, 255, 255))
        draw.text((x1+25, y1+130), desc, font=get_font(15, bold=False), fill=(51, 65, 85))

    # Bottom Footer Bar
    draw_rounded_rect(draw, (50, 590, 1230, 670), 12, fill=(30, 41, 59))
    draw.text((220, 615), "「見やすいプリントが、子どもの集中力と丁寧な解答を引き出します」", font=get_font(20), fill=(255, 255, 255))

    img.save(os.path.join(target_dir, "column-worksheet-layout-diagram.webp"), "WEBP", quality=90)
    print("Generated column-worksheet-layout-diagram.webp")

# 10. column-weekly-ai-reasoning-models.webp
def gen_weekly_ai_reasoning_models():
    img = Image.new('RGB', (1280, 720), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Title
    draw_rounded_rect(draw, (40, 30, 1240, 110), 16, fill=(30, 58, 138))
    draw.text((60, 48), "思考型AI（Reasoning Models）の段階的推論プロセス", font=get_font(30), fill=(255, 255, 255))
    
    # Left: Conventional AI
    draw_rounded_rect(draw, (60, 150, 610, 560), 20, fill=(241, 245, 249), outline=(148, 163, 184), width=2)
    draw_rounded_rect(draw, (80, 170, 590, 230), 10, fill=(100, 116, 139))
    draw.text((180, 185), "従来のAI (従来のLLM)", font=get_font(22), fill=(255, 255, 255))
    draw.text((100, 270), "入力 → [単語の確率予測] → 即座に出力", font=get_font(18), fill=(51, 65, 85))
    draw.text((100, 340), "・思考途中のセルフチェックなし\n・途中の計算ミスや誤解に気づきにくい", font=get_font(16, bold=False), fill=(100, 116, 139))
    
    # Right: Reasoning AI
    draw_rounded_rect(draw, (670, 150, 1220, 560), 20, fill=(239, 246, 255), outline=(37, 99, 235), width=3)
    draw_rounded_rect(draw, (690, 170, 1200, 230), 10, fill=(37, 99, 235))
    draw.text((750, 185), "最新の思考型AI (Reasoning)", font=get_font(22), fill=(255, 255, 255))
    
    r_steps = [
        "1. 課題分析・方針立案 (Chain of Thought)",
        "2. 段階的推論とセルフチェック・検証",
        "3. 高精度な最終回答と過程の出力"
    ]
    for m, s in enumerate(r_steps):
        draw_rounded_rect(draw, (700, 260 + m*80, 1190, 320 + m*80), 8, fill=(255, 255, 255), outline=(191, 219, 254), width=1)
        draw.text((720, 275 + m*80), s, font=get_font(17), fill=(29, 78, 216))

    # Bottom Impact
    draw_rounded_rect(draw, (60, 590, 1220, 670), 12, fill=(30, 41, 59))
    draw.text((200, 615), "【教育へのメリット】途中の解法手順を可視化し、「どこでつまずいたか」を分析可能", font=get_font(18), fill=(255, 255, 255))

    img.save(os.path.join(target_dir, "column-weekly-ai-reasoning-models.webp"), "WEBP", quality=90)
    print("Generated column-weekly-ai-reasoning-models.webp")

# 11. column-weekly-ai-multimodal-learning.webp
def gen_weekly_ai_multimodal_learning():
    img = Image.new('RGB', (1280, 720), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Title
    draw_rounded_rect(draw, (40, 30, 1240, 110), 16, fill=(13, 148, 136))
    draw.text((60, 48), "マルチモーダルAIがもたらすリアルタイム対話学習", font=get_font(30), fill=(255, 255, 255))
    
    features = [
        ("① 音声・対話学習", "・発音やアクセントの即時判定\n・自然なネイティブ英会話対話\n・個に応じた難易度自動調整", (204, 251, 241), (13, 148, 136)),
        ("② カメラ・映像理解", "・手元実験器具の使い方チェック\n・植物・美術作品のリアルタイム解説\n・数式や図形のカメラ読み取り", (240, 253, 244), (21, 128, 61)),
        ("③ 学習アクセシビリティ", "・視覚・聴覚サポート（音声読み上げ）\n・要約と字幕表示による理解支援\n・特別支援教育での多様なサポート", (239, 246, 255), (29, 78, 216))
    ]
    
    for i, (title, desc, bg_col, t_col) in enumerate(features):
        x1 = 50 + i * 395
        x2 = x1 + 370
        y1 = 150
        y2 = 560
        draw_rounded_rect(draw, (x1, y1, x2, y2), 16, fill=bg_col, outline=t_col, width=2)
        
        draw_rounded_rect(draw, (x1+15, y1+15, x2-15, y1+65), 10, fill=t_col)
        draw.text((x1+25, y1+27), title, font=get_font(20), fill=(255, 255, 255))
        
        draw_rounded_rect(draw, (x1+15, y1+100, x2-15, y2-20), 10, fill=(255, 255, 255))
        draw.text((x1+25, y1+120), desc, font=get_font(16, bold=False), fill=(51, 65, 85))

    # Bottom Banner
    draw_rounded_rect(draw, (50, 590, 1230, 670), 12, fill=(30, 41, 59))
    draw.text((200, 615), "「テキストを超えて、五感に訴えかけるインタラクティブな学びへ」", font=get_font(20), fill=(255, 255, 255))

    img.save(os.path.join(target_dir, "column-weekly-ai-multimodal-learning.webp"), "WEBP", quality=90)
    print("Generated column-weekly-ai-multimodal-learning.webp")

# 12. column-weekly-education-ai-guidelines.webp
def gen_weekly_education_ai_guidelines():
    img = Image.new('RGB', (1280, 720), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Title
    draw_rounded_rect(draw, (40, 30, 1240, 110), 16, fill=(30, 58, 138))
    draw.text((60, 48), "学校における生成AI活用ガイドラインと実践ステップ", font=get_font(30), fill=(255, 255, 255))
    
    steps = [
        ("領域 1: 生徒の学び", "・文章のブレインストーミング\n・思考のパートナーとしての活用\n・クリティカルシンキングの育成", (239, 246, 255), (29, 78, 216)),
        ("領域 2: 問いを立てる力", "・ファクトチェックの習慣化\n・「答えの根拠」を吟味する指導\n・情報リテラシー・AI倫理", (254, 243, 199), (180, 83, 9)),
        ("領域 3: 教員の校務効率化", "・週案・指導案の素案作成\n・テスト類題の自動生成\n・通知表所見のアイデア支援", (240, 253, 244), (21, 128, 61))
    ]
    
    for i, (title, desc, bg_col, t_col) in enumerate(steps):
        x1 = 50 + i * 395
        x2 = x1 + 370
        y1 = 150
        y2 = 560
        draw_rounded_rect(draw, (x1, y1, x2, y2), 16, fill=bg_col, outline=t_col, width=2)
        
        draw_rounded_rect(draw, (x1+15, y1+15, x2-15, y1+65), 10, fill=t_col)
        draw.text((x1+25, y1+27), title, font=get_font(20), fill=(255, 255, 255))
        
        draw_rounded_rect(draw, (x1+15, y1+100, x2-15, y2-20), 10, fill=(255, 255, 255))
        draw.text((x1+25, y1+120), desc, font=get_font(16, bold=False), fill=(51, 65, 85))

    # Bottom Banner
    draw_rounded_rect(draw, (50, 590, 1230, 670), 12, fill=(30, 41, 59))
    draw.text((220, 615), "「漠然とした一律禁止から、段階的利活用と人間中心の教育へ」", font=get_font(20), fill=(255, 255, 255))

    img.save(os.path.join(target_dir, "column-weekly-education-ai-guidelines.webp"), "WEBP", quality=90)
    print("Generated column-weekly-education-ai-guidelines.webp")

def generate_all():
    gen_note_curation_matrix()
    gen_note_author_comment_workflow()
    gen_teacher_community_insight()
    gen_future_education_reflection()
    gen_note_extra_reflection()
    gen_thinking_tools_inquiry_diagram()
    gen_classroom_digital_presentation()
    gen_observation_card_sample()
    gen_worksheet_layout_diagram()
    gen_weekly_ai_reasoning_models()
    gen_weekly_ai_multimodal_learning()
    gen_weekly_education_ai_guidelines()
    print("All 12 Japanese infographics generated successfully.")

if __name__ == "__main__":
    generate_all()
