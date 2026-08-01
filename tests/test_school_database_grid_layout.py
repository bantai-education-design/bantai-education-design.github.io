"""
全国学校データベースのポータルページ（tools/school-database/index.html）の
グリッド構造・地方区分・レンダラー配線を検証する回帰テスト。

背景: PR #87〜#92で、47都道府県カードは静的HTMLへ直接埋め込む方式から、
prefecture-card-renderer.js が prefecture-card-metadata.json を fetch して
動的に描画する方式へ移行した。本テストは旧来の「index.htmlに47枚のカード
HTMLが直接存在する」という前提を廃止し、以下の2点を検証する。

1. index.html側: カード描画ルート要素とレンダラーの読み込みが存在すること。
2. データ側: prefecture-card-metadata.json の地方（region）区分・順序・
   都道府県の割り当てが、ポータルが表示すべき仕様どおりであること。

実際にブラウザでレンダリングした結果（列数・detailsの開閉・カード全体
クリック・キーボード操作等）は、Playwright を用いた
tools/school-database/test_population_metadata_browser.js が実ブラウザで
検証する。責務は次のとおり分離している。

- 本ファイル（Python, 静的検証）: HTMLの配線、CSSのブレークポイント定義、
  レンダラーJSのソースコードに書かれた振る舞い（クリック除外・共通関数
  経由でdetailsを生成していること等）、JSONの地方区分・順序。
- test_population_metadata_browser.js（Playwright, 実ブラウザ検証）:
  実際にレンダリングされたDOMでの列数・横スクロール・details開閉・
  キーボード操作・ページ遷移。
"""

import json
import os
import re
from pathlib import Path

ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
INDEX_HTML = ROOT / "tools" / "school-database" / "index.html"
CSS_PATH = ROOT / "assets" / "css" / "school-database.css"
RENDERER_JS = ROOT / "assets" / "js" / "school-database" / "prefecture-card-renderer.js"
CARD_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"

EXPECTED_REGIONS = [
    ("kanto", "関東地方"),
    ("hokkaido", "北海道地方"),
    ("tohoku", "東北地方"),
    ("chubu", "中部地方"),
    ("kinki", "近畿地方"),
    ("chugoku", "中国地方"),
    ("shikoku", "四国地方"),
    ("kyushu", "九州・沖縄地方"),
]

REGION_LEADERS = {
    "kanto": "東京都",
    "hokkaido": "北海道",
    "tohoku": "宮城県",
    "chubu": "愛知県",
    "kinki": "大阪府",
    "chugoku": "広島県",
    "shikoku": "香川県",
    "kyushu": "福岡県",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_portal_html_wires_up_renderer():
    """index.htmlが静的カードを持たず、描画ルートとレンダラーの読み込みだけを
    持つこと（カードはJSがJSONから動的に生成する）。"""
    html = _read(INDEX_HTML)

    assert re.search(r'<div[^>]*\bdata-prefecture-card-root\b[^>]*>', html), (
        "data-prefecture-card-root を持つカード描画ルート要素が見つかりません"
    )
    assert 'id="prefecture-card-root"' in html, "prefecture-card-root のid要素が見つかりません"
    assert '<script src="/assets/js/school-database/prefecture-card-renderer.js"></script>' in html, (
        "prefecture-card-renderer.js の読み込みが見つかりません"
    )

    # 静的HTML方式の名残（旧来の47枚のカードHTML）が復活していないこと。
    assert html.count('<div id="prefecture-card-root"') == 1
    assert "pref-card active-card region-" not in html, (
        "静的に埋め込まれたカードHTMLが復活しています（動的レンダリング方式のはずです）"
    )

    # placeholderカード（「他都道府県」等の準備中カード）を生成していないこと。
    for prohibited in ("準備中", "順次拡張予定", "順次追加予定", "全国他都道府県"):
        assert prohibited not in html, f"placeholder文言 '{prohibited}' が index.html に残っています"


def test_card_metadata_region_order_and_assignment():
    """8地方区分の順序・47都道府県の重複なし割り当てを、レンダラーが実際に
    読み込むJSONで検証する（region.code/region.nameの並び順がそのまま
    描画時のセクション順序になる。prefecture-card-renderer.js参照）。"""
    payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    prefectures = payload["prefectures"]
    assert len(prefectures) == 47, f"Expected 47 prefectures, got {len(prefectures)}"

    # 地方コードの初出順（=描画されるセクション順）を抽出する。
    seen_order = []
    seen_codes = set()
    for pref in prefectures:
        code = pref["region"]["code"]
        if code not in seen_codes:
            seen_codes.add(code)
            seen_order.append((code, pref["region"]["name"]))

    assert seen_order == EXPECTED_REGIONS, (
        f"地方の並び順が想定と異なります。期待={EXPECTED_REGIONS}, 実際={seen_order}"
    )

    # 各地方が連続したブロックとして現れること（同じ地方コードが分断されて
    # 複数箇所に出現しない = 重複なく割り当てられている）。
    region_sequence = [pref["region"]["code"] for pref in prefectures]
    blocks = []
    for code in region_sequence:
        if not blocks or blocks[-1] != code:
            blocks.append(code)
    assert len(blocks) == len(EXPECTED_REGIONS), (
        "同じ地方コードが複数の非連続ブロックに分断されています"
        f"（都道府県が地方をまたいで重複している可能性）: {blocks}"
    )

    # 都道府県名・コードの重複なし。
    names = [pref["prefecture_name"] for pref in prefectures]
    codes = [pref["prefecture_code"] for pref in prefectures]
    assert len(set(names)) == 47, "都道府県名に重複があります"
    assert len(set(codes)) == 47, "prefecture_codeに重複があります"

    # 関東地方が最初、先頭は東京都。
    assert prefectures[0]["region"]["code"] == "kanto", "最初の地方が関東地方ではありません"
    assert prefectures[0]["prefecture_name"] == "東京都", "関東地方の先頭が東京都ではありません"

    # 北海道地方と東北地方が別区分であること。
    assert "hokkaido" in seen_codes and "tohoku" in seen_codes
    assert seen_order[1][0] == "hokkaido" and seen_order[2][0] == "tohoku", (
        "関東地方の次に北海道地方、その直後に東北地方という順序になっていません"
    )

    # 東北地方の先頭が宮城県。
    tohoku_prefs = [p["prefecture_name"] for p in prefectures if p["region"]["code"] == "tohoku"]
    assert tohoku_prefs[0] == "宮城県", f"東北地方の先頭が宮城県ではありません: {tohoku_prefs}"

    # 各地方の先頭都道府県（中心都市）。
    for code, expected_leader in REGION_LEADERS.items():
        block = [p["prefecture_name"] for p in prefectures if p["region"]["code"] == code]
        assert block[0] == expected_leader, (
            f"{code} 地方の先頭が {expected_leader} ではありません: {block}"
        )


def test_grid_breakpoints_defined_in_css():
    """.prefectures-grid の列数ブレークポイントが 1/2/3/4列で定義されていること。"""
    css = _read(CSS_PATH)

    assert re.search(r"\.prefectures-grid\s*\{[^}]*grid-template-columns:\s*repeat\(1", css), (
        "デフォルト（1列）の定義が見つかりません"
    )
    assert re.search(
        r"@media\s*\(max-width:\s*640px\)\s*\{[^{}]*\.prefectures-grid\s*\{[^}]*grid-template-columns:\s*1fr",
        css,
    ), "640px以下で1列になる定義が見つかりません"
    assert re.search(
        r"@media\s*\(min-width:\s*641px\)\s*and\s*\(max-width:\s*900px\)\s*\{[^{}]*\.prefectures-grid\s*\{[^}]*repeat\(2",
        css,
    ), "641〜900pxで2列になる定義が見つかりません"
    assert re.search(
        r"@media\s*\(min-width:\s*901px\)\s*and\s*\(max-width:\s*1199px\)\s*\{[^{}]*\.prefectures-grid\s*\{[^}]*repeat\(3",
        css,
    ), "901〜1199pxで3列になる定義が見つかりません"
    assert re.search(
        r"@media\s*\(min-width:\s*1200px\)\s*\{[^{}]*\.prefectures-grid\s*\{[^}]*repeat\(4",
        css,
    ), "1200px以上で4列になる定義が見つかりません"

    # 横スクロールを生みやすい固定幅指定が存在しないこと。
    assert re.search(r"writing-mode:\s*vertical", css) is None
    assert re.search(r"word-break:\s*break-all", css) is None
    assert "width: fit-content" not in css


def test_renderer_generates_shared_population_details_and_click_handling():
    """人口カードのdetailsが47件分の重複コードではなく共通関数
    （appendPopulationSummary）から生成されること、カード全体クリックが
    summary/details/リンク等の内部操作を妨げないこと、placeholderカードを
    生成するコードが存在しないことを、レンダラーのソースで検証する。"""
    js = _read(RENDERER_JS)

    assert js.count("appendPopulationSummary") >= 2, (
        "appendPopulationSummary が定義・呼び出しの両方で見つかりません"
        "（47件分が個別にハードコードされている可能性）"
    )
    assert "population-age-details" in js
    assert js.count('createElement("details"') == 1, (
        "detailsを生成する箇所が複数ある = 都道府県ごとに重複コードがある可能性があります"
    )

    # カード全体クリック時、summary/details/リンク等の内部操作をナビゲー
    # ションから除外していること。
    assert re.search(
        r'closest\(["\']a,\s*button,\s*summary,\s*details,\s*input,\s*select,\s*textarea["\']\)',
        js,
    ), "カード全体クリックがsummary/details等の内部操作を除外していません"

    # キーボード操作（Enter）でも同じナビゲーションが行えること。
    assert "keydown" in js and "Enter" in js, "キーボード操作（Enter）の処理が見つかりません"

    # placeholderカード（準備中カード等）を生成するロジックが存在しないこと。
    for prohibited in ("準備中", "順次拡張予定", "順次追加予定", "全国他都道府県", "opacity:0.75"):
        assert prohibited not in js, f"レンダラーJSにplaceholder関連の文言 '{prohibited}' が残っています"

    # 47件すべてに同じデータ駆動のカード生成関数を通すこと（1件だけ特別扱い
    # するifブロックが無いこと = 東京都だけ別ロジックになっていないこと）。
    assert "tokyo" not in js.lower(), (
        "レンダラーJSに東京都固有のハードコードが残っています"
        "（全都道府県が同じデータ駆動ロジックを通るべきです）"
    )


if __name__ == "__main__":
    test_portal_html_wires_up_renderer()
    test_card_metadata_region_order_and_assignment()
    test_grid_breakpoints_defined_in_css()
    test_renderer_generates_shared_population_details_and_click_handling()
    print("Grid layout / renderer wiring regression tests passed successfully.")
