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

# 1. column-weekly-ai-news-20260919.webp
def gen_thumb_ai_20260919():
    img = Image.new('RGB', (1280, 720), color=(239, 246, 255))
    draw = ImageDraw.Draw(img)
    draw_rounded_rect(draw, (40, 40, 1240, 680), 24, fill=(30, 58, 138), outline=(59, 130, 246), width=3)
    
    draw_rounded_rect(draw, (80, 80, 400, 140), 20, fill=(37, 99, 235))
    draw.text((110, 95), "週刊AI動向", font=get_font(26), fill=(255, 255, 255))
    
    draw.text((80, 190), "【思考型AIの進化とエージェント連携】", font=get_font(38), fill=(255, 255, 255))
    draw.text((80, 260), "今週のAIニュースと教育DXの最前線", font=get_font(28, bold=False), fill=(191, 219, 254))
    
    tags = ["・段階的推論 (Reasoning)", "・校務・学習エージェント", "・AIウォーターマーク", "・オンデバイスSLM"]
    for i, t in enumerate(tags):
        y = 350 + i * 75
        draw_rounded_rect(draw, (80, y, 1200, y + 60), 12, fill=(255, 255, 255))
        draw.text((110, y + 15), t, font=get_font(22), fill=(30, 41, 59))
        
    img.save(os.path.join(target_dir, "column-weekly-ai-news-20260919.webp"), "WEBP", quality=90)
    print("Generated column-weekly-ai-news-20260919.webp")

# 2. column-weekly-ai-news-20260918.webp
def gen_thumb_ai_20260918():
    img = Image.new('RGB', (1280, 720), color=(240, 253, 250))
    draw = ImageDraw.Draw(img)
    draw_rounded_rect(draw, (40, 40, 1240, 680), 24, fill=(13, 148, 136), outline=(20, 184, 166), width=3)
    
    draw_rounded_rect(draw, (80, 80, 400, 140), 20, fill=(15, 118, 110))
    draw.text((110, 95), "週刊AI動向", font=get_font(26), fill=(255, 255, 255))
    
    draw.text((80, 190), "【マルチモーダルAIの進歩と教育活用】", font=get_font(38), fill=(255, 255, 255))
    draw.text((80, 260), "今週のAIニュースと未来の学び", font=get_font(28, bold=False), fill=(204, 251, 241))
    
    tags = ["・リアルタイム音声・対話機能", "・カメラ画像・手元映像の理解", "・AI倫理と著作権ガイドライン", "・学習アクセシビリティ"]
    for i, t in enumerate(tags):
        y = 350 + i * 75
        draw_rounded_rect(draw, (80, y, 1200, y + 60), 12, fill=(255, 255, 255))
        draw.text((110, y + 15), t, font=get_font(22), fill=(30, 41, 59))
        
    img.save(os.path.join(target_dir, "column-weekly-ai-news-20260918.webp"), "WEBP", quality=90)
    print("Generated column-weekly-ai-news-20260918.webp")

# 3. column-weekly-education-news-20260917.webp
def gen_thumb_edu_20260917():
    img = Image.new('RGB', (1280, 720), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    draw_rounded_rect(draw, (40, 40, 1240, 680), 24, fill=(30, 58, 138), outline=(59, 130, 246), width=3)
    
    draw_rounded_rect(draw, (80, 80, 400, 140), 20, fill=(29, 78, 216))
    draw.text((110, 95), "週刊教育動向", font=get_font(26), fill=(255, 255, 255))
    
    draw.text((80, 190), "【生成AIガイドラインとGIGA第2期端末更新】", font=get_font(36), fill=(255, 255, 255))
    draw.text((80, 260), "今週の教育ニュースと現場の展望", font=get_font(28, bold=False), fill=(191, 219, 254))
    
    tags = ["・学校での生成AI利用ガイドライン", "・1人1台端末更新と予備機確保", "・デジタル教科書の本格導入", "・教員の働き方改革と校務DX"]
    for i, t in enumerate(tags):
        y = 350 + i * 75
        draw_rounded_rect(draw, (80, y, 1200, y + 60), 12, fill=(255, 255, 255))
        draw.text((110, y + 15), t, font=get_font(22), fill=(30, 41, 59))
        
    img.save(os.path.join(target_dir, "column-weekly-education-news-20260917.webp"), "WEBP", quality=90)
    print("Generated column-weekly-education-news-20260917.webp")

# 4. column-weekly-lesson-ict-inquiry.webp
def gen_thumb_ict_inquiry():
    img = Image.new('RGB', (1280, 720), color=(237, 233, 254))
    draw = ImageDraw.Draw(img)
    draw_rounded_rect(draw, (40, 40, 1240, 680), 24, fill=(109, 40, 217), outline=(139, 92, 246), width=3)
    
    draw_rounded_rect(draw, (80, 80, 400, 140), 20, fill=(124, 58, 237))
    draw.text((110, 95), "授業改善・ICT教育", font=get_font(26), fill=(255, 255, 255))
    
    draw.text((80, 190), "【1人1台端末で深まる探究学習】", font=get_font(38), fill=(255, 255, 255))
    draw.text((80, 260), "デジタル思考ツール＆協働編集の活用法", font=get_font(28, bold=False), fill=(221, 214, 254))
    
    tags = ["・3大シンキングツール（ベン図・クラゲ・Y）", "・リアルタイム付箋共有とKJ法", "・15秒〜30秒の短尺動画教材活用", "・子供主体の対話型プレゼン"]
    for i, t in enumerate(tags):
        y = 350 + i * 75
        draw_rounded_rect(draw, (80, y, 1200, y + 60), 12, fill=(255, 255, 255))
        draw.text((110, y + 15), t, font=get_font(22), fill=(30, 41, 59))
        
    img.save(os.path.join(target_dir, "column-weekly-lesson-ict-inquiry.webp"), "WEBP", quality=90)
    print("Generated column-weekly-lesson-ict-inquiry.webp")

# 5. column-weekly-lesson-worksheet-design.webp
def gen_thumb_worksheet_design():
    img = Image.new('RGB', (1280, 720), color=(240, 253, 244))
    draw = ImageDraw.Draw(img)
    draw_rounded_rect(draw, (40, 40, 1240, 680), 24, fill=(22, 101, 52), outline=(34, 197, 94), width=3)
    
    draw_rounded_rect(draw, (80, 80, 400, 140), 20, fill=(21, 128, 61))
    draw.text((110, 95), "授業改善・教材配布", font=get_font(26), fill=(255, 255, 255))
    
    draw.text((80, 190), "【伝わるプリント・教材設計術】", font=get_font(38), fill=(255, 255, 255))
    draw.text((80, 260), "方眼紙・五線譜・観察カードのレイアウト", font=get_font(28, bold=False), fill=(187, 247, 208))
    
    tags = ["・ユニバーサルデザイン4大原則", "・理科観察カードの大きなスケッチ枠", "・五線譜メーカー＆デジタル方眼紙", "・子供の『書く意欲』を引き出す工夫"]
    for i, t in enumerate(tags):
        y = 350 + i * 75
        draw_rounded_rect(draw, (80, y, 1200, y + 60), 12, fill=(255, 255, 255))
        draw.text((110, y + 15), t, font=get_font(22), fill=(30, 41, 59))
        
    img.save(os.path.join(target_dir, "column-weekly-lesson-worksheet-design.webp"), "WEBP", quality=90)
    print("Generated column-weekly-lesson-worksheet-design.webp")

def main():
    gen_thumb_ai_20260919()
    gen_thumb_ai_20260918()
    gen_thumb_edu_20260917()
    gen_thumb_ict_inquiry()
    gen_thumb_worksheet_design()
    print("All 5 Japanese thumbnails generated successfully.")

if __name__ == "__main__":
    main()
