#!/usr/bin/env python3
"""Add the prefecture silhouette mark next to the <h1> on each of the 47
individual prefecture pages (tools/school-database/{slug}/index.html).

These pages are static HTML (not JS-rendered like the portal), so the
silhouette's mask URL is inlined per page rather than driven from JSON.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHOOL_DB_DIR = ROOT / "tools" / "school-database"

PREFECTURES = [
    ("01", "hokkaido"), ("02", "aomori"), ("03", "iwate"), ("04", "miyagi"),
    ("05", "akita"), ("06", "yamagata"), ("07", "fukushima"), ("08", "ibaraki"),
    ("09", "tochigi"), ("10", "gunma"), ("11", "saitama"), ("12", "chiba"),
    ("13", "tokyo"), ("14", "kanagawa"), ("15", "niigata"), ("16", "toyama"),
    ("17", "ishikawa"), ("18", "fukui"), ("19", "yamanashi"), ("20", "nagano"),
    ("21", "gifu"), ("22", "shizuoka"), ("23", "aichi"), ("24", "mie"),
    ("25", "shiga"), ("26", "kyoto"), ("27", "osaka"), ("28", "hyogo"),
    ("29", "nara"), ("30", "wakayama"), ("31", "tottori"), ("32", "shimane"),
    ("33", "okayama"), ("34", "hiroshima"), ("35", "yamaguchi"), ("36", "tokushima"),
    ("37", "kagawa"), ("38", "ehime"), ("39", "kochi"), ("40", "fukuoka"),
    ("41", "saga"), ("42", "nagasaki"), ("43", "kumamoto"), ("44", "oita"),
    ("45", "miyazaki"), ("46", "kagoshima"), ("47", "okinawa"),
]

# 2種類のテンプレートに対応する。
# A: <h1>東京都学校データベース</h1>（page-hero系ページ）
# B: <h1 class="db-title">和歌山県 学校データベース</h1>（db-title系ページ）
H1_PATTERNS = [
    re.compile(r'( *)<h1>([^<]+学校データベース)</h1>'),
    re.compile(r'( *)<h1 class="db-title">([^<]+学校データベース)</h1>'),
]


def process_one(code: str, slug: str) -> str:
    page_path = SCHOOL_DB_DIR / slug / "index.html"
    if not page_path.is_file():
        return f"SKIP {slug}: index.htmlが見つかりません"

    html = page_path.read_text(encoding="utf-8")
    if "hero-silhouette" in html:
        return f"SKIP {slug}: 既に追加済み"

    match = None
    h1_class = ""
    for pattern in H1_PATTERNS:
        match = pattern.search(html)
        if match:
            if 'class="db-title"' in pattern.pattern:
                h1_class = ' class="db-title"'
            break
    if not match:
        return f"FAIL {slug}: h1が見つかりません"

    indent, title_text = match.group(1), match.group(2)
    src = f"/assets/images/prefecture-silhouettes/{code}-{slug}.svg"
    replacement = (
        f'{indent}<div class="hero-title-row">\n'
        f'{indent}  <span class="pref-silhouette hero-silhouette" aria-hidden="true" '
        f'style="--silhouette-url: url(\'{src}\');"></span>\n'
        f"{indent}  <h1{h1_class}>{title_text}</h1>\n"
        f"{indent}</div>"
    )
    html = html[: match.start()] + replacement + html[match.end() :]
    page_path.write_text(html, encoding="utf-8", newline="\n")
    return f"OK {slug}"


def main() -> None:
    results = [process_one(code, slug) for code, slug in PREFECTURES]
    for r in results:
        print(r)
    ok_count = sum(1 for r in results if r.startswith("OK"))
    print(f"{ok_count}/47 pages updated")
    if ok_count != 47:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
