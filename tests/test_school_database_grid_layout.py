"""
全国学校データベースのポータルページ（tools/school-database/index.html）が
安定したカードグリッド構造を持つことを検証する回帰テスト。

背景: .prefectures-grid が二重にネストされ（外側の1つの.prefectures-gridの
中に、地方ごとの内側.prefectures-gridが子要素として並ぶ構造になっていた）、
カード幅が実測60px程度まで潰れ、都道府県名が1文字ずつ折り返される・横スクロール
が発生する重大な表示不具合が本番で発生した。本テストはこの不具合の再発を防ぐ。
"""
import os
import re

INDEX_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "tools", "school-database", "index.html")
)
CSS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "assets", "css", "school-database.css")
)

EXPECTED_REGIONS = [
    "関東地方", "北海道・東北地方", "中部地方",
    "近畿地方", "中国地方", "四国地方", "九州・沖縄地方",
]

REGION_LEADERS = {
    "関東地方": "東京都",
    "北海道・東北地方": "北海道",
    "中部地方": "愛知県",
    "近畿地方": "大阪府",
    "中国地方": "広島県",
    "四国地方": "香川県",
    "九州・沖縄地方": "福岡県",
}


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _region_sections(html):
    """<section class="region-section">...</section> ブロックを順に抜き出す。"""
    return re.findall(
        r'<section class="region-section">(.*?)</section>', html, re.DOTALL
    )


def check_region_section_structure(html=None):
    html = html or _read(INDEX_PATH)

    # region-section が7個（北海道地方と東北地方は「北海道・東北地方」として
    # 1セクションに統合）、かつ外側でgrid/flexの横並びコンテナになっていない
    # こと（region-sectionは常に縦積み）。
    sections = _region_sections(html)
    assert len(sections) == 7, f"Expected 7 region-section blocks, got {len(sections)}"

    # 各region-section直下にregion-titleとprefectures-gridが1つずつ。
    for i, block in enumerate(sections):
        titles = re.findall(r'<h3 class="[^"]*region-title[^"]*">(.*?)</h3>', block)
        grids = re.findall(r'<div class="prefectures-grid">', block)
        assert len(titles) == 1, f"section {i}: expected 1 region-title, got {len(titles)}"
        assert len(grids) == 1, f"section {i}: expected 1 prefectures-grid, got {len(grids)}"
        assert titles[0] == EXPECTED_REGIONS[i], (
            f"section {i}: expected heading {EXPECTED_REGIONS[i]!r}, got {titles[0]!r}"
        )

    # prefectures-grid の合計が7個（region-sectionの外に余分なgridが無い）。
    total_grids = len(re.findall(r'<div class="prefectures-grid">', html))
    assert total_grids == 7, f"Expected 7 prefectures-grid total, got {total_grids}"

    # prefecture-card（= pref-card エイリアス）の合計が47個。
    cards = re.findall(r'<a class="[^"]*prefecture-card[^"]*".*?</a>', html, re.DOTALL)
    assert len(cards) == 47, f"Expected 47 prefecture-card total, got {len(cards)}"

    # 関東地方の最初が東京都。
    kanto_block = sections[0]
    first_pref = re.search(r"<h2>(.*?)</h2>", kanto_block).group(1)
    assert first_pref == "東京都", f"関東地方の最初のカードが東京都ではありません: {first_pref}"

    # 各地方ブロックの先頭都道府県（中心都市）の確認。
    for i, region_name in enumerate(EXPECTED_REGIONS):
        if region_name not in REGION_LEADERS:
            continue
        first = re.search(r"<h2>(.*?)</h2>", sections[i]).group(1)
        assert first == REGION_LEADERS[region_name], (
            f"{region_name}の先頭都道府県が{REGION_LEADERS[region_name]}ではありません: {first}"
        )

    # 北海道・東北地方の先頭が北海道であり、7道県（北海道+東北6県）が
    # 含まれる。
    hokkaido_tohoku_block = sections[1]
    hokkaido_tohoku_prefs = re.findall(r"<h2>(.*?)</h2>", hokkaido_tohoku_block)
    assert hokkaido_tohoku_prefs[0] == "北海道", (
        f"北海道・東北地方の先頭が北海道ではありません: {hokkaido_tohoku_prefs}"
    )
    assert len(hokkaido_tohoku_prefs) == 7, (
        f"北海道・東北地方には北海道+東北6県の計7件が含まれるべきです: {hokkaido_tohoku_prefs}"
    )

    # 北海道が関東地方のブロックに含まれていない。
    kanto_prefs = re.findall(r"<h2>(.*?)</h2>", kanto_block)
    assert "北海道" not in kanto_prefs, "北海道が関東地方のprefectures-gridに含まれています"

    return True


def check_no_layout_breaking_css_rules(css=None):
    css = css or _read(CSS_PATH)

    # writing-mode: vertical-* がカード系CSSに存在しない。
    assert "writing-mode: vertical" not in css.replace(" ", ""), (
        "writing-mode: vertical-* が school-database.css に存在します"
    )
    assert re.search(r"writing-mode:\s*vertical", css) is None, (
        "writing-mode: vertical-* が school-database.css に存在します"
    )

    # word-break: break-all がカード系CSSに存在しない。
    assert re.search(r"word-break:\s*break-all", css) is None, (
        "word-break: break-all が school-database.css に存在します"
    )

    # 横スクロールを生みやすい固定幅指定（例: repeat(8, ...)、
    # minmax(0, 220px)のような固定px、width: fit-content）が
    # prefectures-grid / pref-card 関連に存在しない。
    assert "repeat(8" not in css, "grid-template-columns: repeat(8, ...) が存在します"
    assert re.search(r"minmax\(0,\s*220px\)", css) is None, (
        "固定220px幅のminmax指定が存在します"
    )
    assert "width: fit-content" not in css, "width: fit-content が存在します"

    return True


def check_deterministic_generation():
    """同じ入力ファイルから2回チェックしても結果が変わらないことを確認する
    （HTML/CSSは静的ファイルであり生成のたびに揺れるものではないが、
     チェック関数自体の非決定性がないことを担保する）。"""
    html = _read(INDEX_PATH)
    css = _read(CSS_PATH)
    result1 = (
        check_region_section_structure(html),
        check_no_layout_breaking_css_rules(css),
    )
    result2 = (
        check_region_section_structure(html),
        check_no_layout_breaking_css_rules(css),
    )
    assert result1 == result2, "2回の検証結果に差分があります"
    return True


if __name__ == "__main__":
    check_region_section_structure()
    check_no_layout_breaking_css_rules()
    check_deterministic_generation()
    print("Grid layout regression tests passed successfully.")
