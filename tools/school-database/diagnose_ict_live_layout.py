#!/usr/bin/env python3
import io
import unicodedata
import urllib.request
import openpyxl

ICT_URL = "https://www.e-stat.go.jp/stat-search/file-download?fileKind=0&statInfId=000040365967"
WAITING_URL = (
    "https://www.cfa.go.jp/assets/contents/node/basic_page/field_ref_resources/"
    "b0a8057b-34bf-4c20-84fb-ae592708ca9b/1a728dcc/"
    "20250828_policies_hoiku_torimatome_r7_02.xlsx"
)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def fmt(v):
    return unicodedata.normalize("NFKC", str(v)).replace("\n", " ")


ict = openpyxl.load_workbook(io.BytesIO(fetch(ICT_URL)), data_only=True)
ws = ict["県教員（合計）"]
print("ICT row53:", [ws.cell(53, c).value for c in range(1, 8)])

waiting = openpyxl.load_workbook(io.BytesIO(fetch(WAITING_URL)), data_only=True)
ws = waiting["資料3"]
print(f"WAITING 資料3 size={ws.max_row}x{ws.max_column}")
for r in range(48, min(ws.max_row, 58) + 1):
    vals = [f"c{c}={fmt(ws.cell(r,c).value)!r}" for c in range(1, ws.max_column + 1) if ws.cell(r,c).value is not None and str(ws.cell(r,c).value).strip()]
    if vals:
        print(f"WAITING row{r}: " + " | ".join(vals))

pref_names = {
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県", "群馬県",
    "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県", "福岡県",
    "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
}
rows = []
for r in range(1, ws.max_row + 1):
    for c in range(1, ws.max_column + 1):
        if fmt(ws.cell(r,c).value or "").strip() in pref_names:
            rows.append(r)
            break
print("prefecture rows:", rows[:3], "...", rows[-3:], "count=", len(rows))
print("sum col6 across prefecture rows:", sum(float(ws.cell(r,6).value or 0) for r in rows))
print("sum col12 across same rows:", sum(float(ws.cell(r,12).value or 0) for r in rows))
