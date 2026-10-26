"""漢字練習帳メーカーの商品画像を作り直す。

使い方: python3 render.py <画像フォルダ> <出力フォルダ>
  画像フォルダ: assets/images/kanji-practice（元画像の読み込み元）
"""
import base64
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

GREEN = "#05241b"
GOLD = "#c8a45d"
GOLD_LIGHT = "#edd996"
NAME = "漢字練習帳メーカー"

SERIF = "'Noto Serif CJK JP', serif"
SANS = "'Noto Sans CJK JP', sans-serif"


def b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def sheet(cols: int, rows: int, char: str, w: int, label: str, note: str) -> str:
    """1枚の印刷プリント（十字点線つきマス目）"""
    cells = []
    for i in range(cols * rows):
        ch = char if i == 0 else ""
        fs = int(w * 0.86 / cols * 0.7)
        inner = f'<span class="ch" style="font-size:{fs}px">{ch}</span>' if ch else ""
        cells.append(f'<div class="cell">{inner}</div>')
    return f"""
    <figure class="sheet" style="width:{w}px">
      <div class="paper">
        <div class="grid" style="grid-template-columns:repeat({cols},1fr)">{''.join(cells)}</div>
      </div>
      <figcaption><b>{label}</b><span>{note}</span></figcaption>
    </figure>"""


THUMB = f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1600px;height:900px;background:{GREEN};font-family:{SANS};color:#fff;
  display:flex;align-items:center;padding:0 90px;gap:60px;overflow:hidden}}
.copy{{flex:0 0 640px}}
.brand{{color:{GOLD};font-size:30px;font-weight:700;letter-spacing:.04em}}
h1{{font-family:{SERIF};font-weight:900;font-size:104px;line-height:1.12;margin:34px 0 30px}}
.lead{{color:{GOLD_LIGHT};font-size:46px;font-weight:700;line-height:1.45}}
.chips{{display:flex;gap:14px;margin-top:40px;flex-wrap:wrap}}
.chips span{{border:2px solid {GOLD};color:{GOLD_LIGHT};border-radius:999px;padding:8px 24px;font-size:28px;font-weight:700}}
.sheets{{flex:1;display:flex;align-items:flex-end;gap:26px;justify-content:center}}
.sheet{{flex:0 0 auto;display:flex;flex-direction:column;align-items:center}}
.paper{{background:#fff;padding:7%;width:100%;box-shadow:0 18px 40px rgba(0,0,0,.45)}}
.grid{{display:grid;border-top:2px solid #1e293b;border-left:2px solid #1e293b}}
.cell{{aspect-ratio:1;overflow:hidden;border-right:2px solid #1e293b;border-bottom:2px solid #1e293b;position:relative;
  display:flex;align-items:center;justify-content:center;font-family:{SERIF};color:#94a3b8;line-height:1}}
.cell::before,.cell::after{{content:"";position:absolute;border:0 dashed #cbd5e1}}
.cell::before{{left:50%;top:0;bottom:0;border-left-width:1.5px}}
.cell::after{{top:50%;left:0;right:0;border-top-width:1.5px}}
.ch{{position:absolute;inset:0;display:grid;place-items:center;z-index:1;color:#94a3b8;font-family:{SERIF};line-height:1}}
figcaption{{margin-top:22px;text-align:center}}
figcaption b{{display:block;color:#fff;font-size:30px}}
figcaption span{{display:block;color:{GOLD_LIGHT};font-size:24px;margin-top:4px}}
</style></head><body>
<div class="copy">
  <div class="brand">Ban.Tai Education Design</div>
  <h1>漢字練習帳<br>メーカー</h1>
  <p class="lead">その子に合うマス目で、<br>すぐ印刷。</p>
  <div class="chips"><span>マス目1〜50</span><span>線の色・濃さ</span><span>A4/B5</span></div>
</div>
<div class="sheets">
  {sheet(5, 5, "山", 250, "特大 5×5", "幼児向け")}
  {sheet(7, 10, "学", 210, "標準 10×7", "低学年向け")}
  {sheet(12, 15, "漢", 240, "やや小 15×12", "中学年向け")}
</div>
</body></html>"""


def booth1_html(ui_src: str) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;background:{GREEN};font-family:{SANS};color:#fff;position:relative;overflow:hidden}}
.ui{{position:absolute;left:540px;top:120px;width:540px}}
.copy{{position:absolute;left:60px;top:58px;width:470px}}
.brand{{color:{GOLD};font-size:24px;font-weight:700}}
.small{{font-size:19px;margin-top:40px;color:#e2e8f0}}
h1{{font-family:{SERIF};font-weight:700;font-size:84px;line-height:1.12;margin:14px 0 22px}}
.lead{{color:{GOLD};font-size:27px;font-weight:700}}
.sub{{font-size:23px;margin-top:16px;padding-bottom:22px;border-bottom:2px solid {GOLD}}}
.body{{font-size:18px;line-height:1.75;margin-top:24px;color:#e2e8f0;font-family:{SERIF}}}
.band{{position:absolute;left:0;right:0;top:920px;bottom:0;background:{GOLD};display:grid;
  grid-template-columns:repeat(4,1fr);align-items:center;padding:0 26px}}
.band div{{display:flex;align-items:center;justify-content:center;gap:10px;color:{GREEN};font-size:23px;font-weight:700;white-space:nowrap}}
.band i{{width:30px;height:30px;border-radius:50%;background:{GREEN};flex:0 0 30px;position:relative}}
.band i::after{{content:"";position:absolute;left:10px;top:6px;width:7px;height:13px;border:solid #fff;border-width:0 3px 3px 0;transform:rotate(45deg)}}
</style></head><body>
<img class="ui" src="{ui_src}">
<div class="copy">
  <div class="brand">Ban.Tai Education Design</div>
  <div class="small">自分だけの漢字練習ノートを作れるWindowsソフト</div>
  <h1>漢字練習帳<br>メーカー</h1>
  <div class="lead">子どもに合わせた漢字ノートを作れる</div>
  <div class="sub">市販の漢字ノートでは、もう物足りない。</div>
  <div class="body">マス目も、余白も、線の濃さも自由自在。<br>家庭学習・学校・学習塾で活躍する<br>漢字練習用紙作成ソフトです。</div>
</div>
<div class="band">
  <div><i></i>A4/B5対応</div>
  <div><i></i>PDF保存・出力</div>
  <div><i></i>すぐに印刷</div>
  <div><i></i>10日間無料体験</div>
</div>
</body></html>"""


def render(html: str, path: Path, w: int, h: int) -> None:
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.set_content(html)
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(path))
        b.close()


# 1. カード用サムネイル（16:9。サイトの他製品と同じ比率）
render(THUMB, OUT / "card-thumbnail.png", 1600, 900)

# 2. BOOTH 1枚目（アプリ画面は元画像から切り出して再利用）
orig1 = Image.open(SRC / "booth-1-main.png").convert("RGB")
ui = orig1.crop((540, 120, 1080, 760))
render(booth1_html(b64(ui)), OUT / "booth-1-main.png", 1080, 1080)

# 3. BOOTH 2枚目（比較表の見出しだけ差し替え）
img2 = Image.open(SRC / "booth-2-diff.png").convert("RGB")
d = ImageDraw.Draw(img2)
d.rectangle((600, 232, 980, 288), fill=(5, 36, 27))
font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc", 31, index=0)
bbox = d.textbbox((0, 0), NAME, font=font)
tw = bbox[2] - bbox[0]
d.text((790 - tw / 2 - bbox[0], 244 - bbox[1]), NAME, font=font, fill=(237, 217, 150))
img2.save(OUT / "booth-2-diff.png")
print("done")
