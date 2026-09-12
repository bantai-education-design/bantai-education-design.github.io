import os
import json
from PIL import Image, ImageDraw, ImageFont

target_dir = r"C:\Users\User\.gemini\antigravity\scratch\bantai-education-design.github.io\assets\images\columns"
columns_file = r"C:\Users\User\.gemini\antigravity\scratch\bantai-education-design.github.io\data\columns.json"
style_file = r"C:\Users\User\.gemini\antigravity\scratch\bantai-education-design.github.io\assets\style.css"

font_path_bold = r"C:\Windows\Fonts\BIZ-UDGothicB.ttc"
font_path_reg = r"C:\Windows\Fonts\BIZ-UDGothicR.ttc"

def get_font(size, bold=True):
    path = font_path_bold if bold else font_path_reg
    return ImageFont.truetype(path, size)

def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

# Generator for Big, Bold, Eye-Catching Japanese Cover Thumbnails (1280x720)
def create_bold_thumbnail(filename, badge_text, badge_bg, main_title_line1, main_title_line2, sub_text, bg_gradient_start, bg_gradient_end, accent_color):
    img = Image.new('RGB', (1280, 720), color=bg_gradient_start)
    draw = ImageDraw.Draw(img)
    
    # Background Accent Graphic (Gradient / Chalkboard Frame)
    draw_rounded_rect(draw, (30, 30, 1250, 690), 28, fill=bg_gradient_end, outline=accent_color, width=6)
    
    # Outer Glow Ring / Accent Card
    draw_rounded_rect(draw, (50, 50, 1230, 670), 20, fill=bg_gradient_start, outline=None)
    
    # Badge Pill (Top Left)
    draw_rounded_rect(draw, (80, 80, 80 + len(badge_text) * 36 + 60, 150), 20, fill=badge_bg)
    draw.text((110, 95), badge_text, font=get_font(30), fill=(255, 255, 255))
    
    # Big Main Title Line 1 (60pt BOLD)
    draw.text((80, 200), main_title_line1, font=get_font(60), fill=(255, 255, 255))
    
    # Big Main Title Line 2 (54pt BOLD - Accent Gold/Cyan)
    draw.text((80, 290), main_title_line2, font=get_font(54), fill=accent_color)
    
    # Sub Highlight Box (Bottom Banner)
    draw_rounded_rect(draw, (80, 420, 1200, 630), 18, fill=(255, 255, 255), outline=accent_color, width=3)
    
    # Sub Text in Box (32pt BOLD)
    draw.text((110, 460), sub_text, font=get_font(32), fill=(30, 41, 59))
    draw.text((110, 530), "Ban.Tai Education Design ｜ 指導歴40年（小・中・高校教員）磐田井", font=get_font(22, bold=False), fill=(100, 116, 139))
    
    img.save(os.path.join(target_dir, filename), "WEBP", quality=92)
    print(f"Generated High-Impact Thumbnail: {filename}")

def generate_all_thumbnails():
    # 1. Vol 12: 現場の想い・情熱 (Blackboard Emerald & Gold)
    create_bold_thumbnail(
        "column-note-extra-reflection.webp",
        "現場の工夫 ｜ 論文考察",
        (190, 18, 60), # Rose badge
        "noteの教育実践から読み解く",
        "「日本の教師の情熱」とこれからの学び",
        "🌸 失敗談を開示し高め合う、温かい教員文化の価値",
        (20, 50, 40), # Dark Chalkboard Green
        (15, 40, 30),
        (253, 224, 71) # Gold Accent
    )
    
    # 2. Vol 11: note教育ノート7選 (Indigo & Sky Cyan)
    create_bold_thumbnail(
        "column-note-education-curation.webp",
        "教育動向 ｜ 特集ノート",
        (29, 78, 216), # Royal Blue badge
        "現場の知恵が集まる教育ノート",
        "【注目実践 7選】指導案＆授業改善",
        "📘 1人1台端末・生成AI・不登校支援・校務DXの工夫",
        (30, 58, 138), # Deep Indigo
        (23, 37, 84),
        (56, 189, 248) # Cyan Accent
    )
    
    # 3. Vol 10: 1人1台端末×探究学習 (Purple & Lime)
    create_bold_thumbnail(
        "column-weekly-lesson-ict-inquiry.webp",
        "ICT教育 ｜ 授業デザイン",
        (124, 58, 237), # Violet badge
        "1人1台端末で深まる探究学習",
        "【3大デジタル思考ツール】活用法",
        "💡 クラゲチャート・ベン図・Yチャートで思考を可視化",
        (88, 28, 135), # Deep Purple
        (58, 12, 93),
        (163, 230, 53) # Lime Accent
    )

    # 4. Vol 9: 伝わるプリント・教材設計術 (Forest Green & Gold)
    create_bold_thumbnail(
        "column-weekly-lesson-worksheet-design.webp",
        "現場の工夫 ｜ 教材配布",
        (21, 128, 61), # Forest Green badge
        "伝わるプリント・ワークシート設計術",
        "【方眼紙・五線譜・観察カード】",
        "✏️ ユニバーサルデザイン4大原則で子供の意欲を引き出す",
        (20, 83, 45), # Deep Green
        (9, 44, 22),
        (250, 204, 21) # Yellow Accent
    )

    # 5. Vol 8: 思考型AIとエージェント (Navy & Amber)
    create_bold_thumbnail(
        "column-weekly-ai-news-20260919.webp",
        "AIと学び ｜ 今週のAI動向",
        (37, 99, 235), # Blue badge
        "思考型AIモデル（Reasoning）の進化",
        "【AIエージェント連携と教育DX】",
        "🤖 段階的推論プロセスで「考え方の手順」を可視化する",
        (15, 23, 42), # Dark Slate Navy
        (30, 41, 59),
        (251, 191, 36) # Amber Accent
    )

    # 6. Vol 7: マルチモーダルAI (Teal & Cyan)
    create_bold_thumbnail(
        "column-weekly-ai-news-20260918.webp",
        "AIと学び ｜ 最新AI速報",
        (13, 148, 136), # Teal badge
        "マルチモーダルAIの劇的進歩",
        "【リアルタイム音声・対話学習】",
        "🗣️ カメラ映像理解と音声対話で広がる未来の学び",
        (19, 78, 74), # Deep Teal
        (17, 94, 89),
        (45, 212, 191) # Bright Mint Accent
    )

    # 7. Vol 6: 生成AIガイドライン & GIGA第2期 (Navy & Rose)
    create_bold_thumbnail(
        "column-weekly-education-news-20260917.webp",
        "教育動向 ｜ 週刊ダイジェスト",
        (225, 29, 72), # Rose badge
        "学校での生成AI利用ガイドライン",
        "【GIGAスクール第2期 端末更新】",
        "🏫 漠然とした一律禁止から、段階的利活用と現場DXへ",
        (30, 58, 138), # Dark Blue
        (15, 23, 42),
        (244, 63, 94) # Bright Rose Accent
    )

# 3. Update titles in columns.json to be Punchy, Clear, and Readable on cards
def update_card_titles():
    with open(columns_file, "r", encoding="utf-8") as f:
        columns = json.load(f)

    title_map = {
        "column-note-education-monthly-extra-reflection-vol12": "【教育最前線】noteの授業実践から読み解く「日本の教師の情熱」とこれからの学び",
        "column-note-education-monthly-curation-vol11": "【注目ノート7選】先生方の現場知恵・指導案＆授業改善アイデア集",
        "column-weekly-lesson-ict-inquiry-tools": "【1人1台端末】探究学習を深めるデジタル思考ツール活用法",
        "column-weekly-lesson-practice-worksheet-templates": "【教材設計】方眼紙・五線譜・観察カードで作る「伝わるプリント」",
        "column-weekly-ai-news-20260919": "【週刊AI動向】思考型AIモデルの進化と教育DXの最前線",
        "column-weekly-ai-news-20260918": "【週刊AI動向】マルチモーダルAIの進化と未来の学び",
        "column-weekly-education-news-20260917": "【週刊教育動向】生成AIガイドラインとGIGA第2期端末更新"
    }

    for c in columns:
        cid = c.get("id")
        if cid in title_map:
            c["title"] = title_map[cid]

    with open(columns_file, "w", encoding="utf-8") as f:
        json.dump(columns, f, ensure_ascii=False, indent=2)

    print("Updated columns.json with punchy, highly readable card titles.")

# 4. Enhance Card Title Typography CSS in style.css
def update_style_css_typography():
    with open(style_file, "r", encoding="utf-8") as f:
        css = f.read()

    typography_css = """

/* === High-Impact Column Card Typography & Thumbnail Styling === */
.column-card-media {
  position: relative;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: #0f172a;
}

.column-card-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.column-card:hover .column-card-media img {
  transform: scale(1.04);
}

.column-title {
  font-family: "BIZ UDGothic", "Hiragino Kaku Gothic ProN", "Meiryo", sans-serif !important;
  font-weight: 700 !important;
  font-size: 1.15rem !important;
  color: #0f172a !important;
  line-height: 1.45 !important;
  margin: 10px 0 8px 0 !important;
  display: -webkit-box !important;
  -webkit-line-clamp: 2 !important;
  -webkit-box-orient: vertical !important;
  overflow: hidden !important;
  letter-spacing: -0.01em;
}

.column-card-body {
  padding: 18px 20px 20px 20px !important;
}

.column-excerpt {
  font-size: 0.92rem !important;
  color: #475569 !important;
  line-height: 1.65 !important;
  display: -webkit-box !important;
  -webkit-line-clamp: 2 !important;
  -webkit-box-orient: vertical !important;
  overflow: hidden !important;
}
"""

    if "/* === High-Impact Column Card Typography & Thumbnail Styling === */" not in css:
        css += typography_css
        with open(style_file, "w", encoding="utf-8") as f:
            f.write(css)
        print("Updated style.css with High-Impact Card Typography rules.")
    else:
        print("style.css already contains High-Impact Card Typography rules.")

if __name__ == "__main__":
    generate_all_thumbnails()
    update_card_titles()
    update_style_css_typography()
