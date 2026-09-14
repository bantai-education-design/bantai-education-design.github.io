#!/usr/bin/env python3
import io
import unicodedata
import urllib.request
import openpyxl

URL = "https://www.e-stat.go.jp/stat-search/file-download?fileKind=0&statInfId=000040365967"
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as response:
    data = response.read()
wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
print("ICT workbook sheets:", wb.sheetnames)
for ws in wb.worksheets:
    print(f"SHEET {ws.title!r} size={ws.max_row}x{ws.max_column}")
    for r in range(1, min(ws.max_row, 9) + 1):
        values = []
        for c in range(1, ws.max_column + 1):
            v = ws.cell(r, c).value
            if v is not None and str(v).strip() != "":
                text = unicodedata.normalize("NFKC", str(v)).replace("\n", " ")
                values.append(f"c{c}={text!r}")
        if values:
            print(f"row{r}: " + " | ".join(values))
    for r in range(1, ws.max_row + 1):
        row_text = " ".join(unicodedata.normalize("NFKC", str(ws.cell(r, c).value or "")) for c in range(1, ws.max_column + 1))
        if "北海道" in row_text:
            vals = [f"c{c}={ws.cell(r,c).value!r}" for c in range(1, ws.max_column + 1) if ws.cell(r,c).value is not None]
            print(f"HOKKAIDO row{r}: " + " | ".join(vals))
            break
