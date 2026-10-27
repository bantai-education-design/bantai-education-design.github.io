"""絵日記・観察カード作成メーカーの紹介画像を作る。

アプリ本体のHTMLを実際に描画し、出力見本（3種類）とアプリ画面を切り出して使う。
使い方: python3 tools/render_observation_card_images.py <アプリのHTML> <出力フォルダ>
"""
import base64
import pathlib
import sys

from playwright.sync_api import sync_playwright

APP = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

GREEN = "#05241b"
GOLD = "#c8a45d"
GOLD_LIGHT = "#edd996"
SERIF = "'Noto Serif CJK JP', serif"
SANS = "'Noto Sans CJK JP', sans-serif"

# (ファイル名, 絵の広さ, 文章欄, 見出し, 補足)
SAMPLES = [
    ("sample-grid", "1/3", "grid", "絵 1/3 ＋ マス目", "低学年の絵日記に"),
    ("sample-hline", "1/2", "horizontal-line", "絵 1/2 ＋ 横罫線", "観察・自由研究に"),
    ("sample-vline", "1/2", "vertical-line", "絵 1/2 ＋ 縦罫線", "縦書きの作文に"),
]


def b64(path: pathlib.Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def capture(pw):
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 1280, "height": 900}, device_scale_factor=2, offline=True)
    pg = ctx.new_page()
    pg.goto(APP.as_uri())
    pg.wait_for_timeout(800)
    # アプリ画面（試用中の状態のまま）
    pg.screenshot(path=str(OUT / "app-screen.png"))
    # 出力見本は透かしを隠して、用紙だけを切り出す
    pg.evaluate("document.getElementById('paper').classList.add('licensed')")
    for name, ratio, style, *_ in SAMPLES:
        pg.select_option("#picRatio", ratio)
        pg.check(f'input[name="textStyle"][value="{style}"]')
        pg.wait_for_timeout(400)
        pg.locator("#paper").screenshot(path=str(OUT / f"{name}.png"))
    b.close()


def sheet(name, title, note):
    return f"""<figure><img src="{b64(OUT / f'{name}.png')}"><figcaption><b>{title}</b><span>{note}</span></figcaption></figure>"""


CARD = """<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1600px;height:900px;background:{green};font-family:{sans};color:#fff;display:flex;align-items:center;padding:0 80px;gap:56px;overflow:hidden}}
.copy{{flex:0 0 600px}}
.brand{{color:{gold};font-size:30px;font-weight:700}}
h1{{font-family:{serif};font-weight:900;font-size:80px;line-height:1.16;margin:26px 0 26px}}
.lead{{color:{gold_light};font-size:42px;font-weight:700;line-height:1.45}}
.chips{{display:flex;gap:12px;margin-top:36px;flex-wrap:wrap}}
.chips span{{border:2px solid {gold};color:{gold_light};border-radius:999px;padding:8px 22px;font-size:26px;font-weight:700}}
.sheets{{flex:1;display:flex;gap:26px;justify-content:center;align-items:flex-start}}
figure{{width:236px;display:flex;flex-direction:column;align-items:center}}
figure img{{width:100%;display:block;box-shadow:0 18px 40px rgba(0,0,0,.45);background:#fff}}
figcaption{{margin-top:20px;text-align:center}}
figcaption b{{display:block;font-size:27px}}
figcaption span{{display:block;color:{gold_light};font-size:22px;margin-top:4px}}
</style></head><body>
<div class="copy">
  <div class="brand">Ban.Tai Education Design</div>
  <h1>絵日記・<br>観察カード<br>作成メーカー</h1>
  <p class="lead">絵と文章の広さを、<br>活動に合わせて。</p>
  <div class="chips"><span>A4・B4・八つ切・四つ切</span><span>マス目・横罫・縦罫</span></div>
</div>
<div class="sheets">{sheets}</div>
</body></html>"""


with sync_playwright() as pw:
    capture(pw)
    html = CARD.format(
        green=GREEN, gold=GOLD, gold_light=GOLD_LIGHT, serif=SERIF, sans=SANS,
        sheets="".join(sheet(n, t, s) for n, _, _, t, s in SAMPLES),
    )
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1600, "height": 900})
    pg.set_content(html)
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "card-thumbnail.png"))
    b.close()
print("done")
