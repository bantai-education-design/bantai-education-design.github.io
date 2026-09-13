#!/usr/bin/env python3
"""Validate the prefecture silhouette (都道府県地域マーク) integration into
prefecture-card-metadata.json and the generated SVG files themselves.

This is NOT a test of official prefectural crests/flags — see
docs/school-database/prefecture-silhouettes-source-manifest.md. All 47
prefectures must have silhouette.available === true, since these marks are
generated from freely-licensed (CC BY 4.0 compatible) administrative
boundary data, unlike the abandoned official-crest approach (PR #95, only
1/47 usable) whose leftover `emblem` key must NOT appear in production data.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CARD_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
POPULATION_JSON = ROOT / "data" / "school-database" / "prefecture-population.json"
RENDERER_JS = ROOT / "assets" / "js" / "school-database" / "prefecture-card-renderer.js"
CSS_PATH = ROOT / "assets" / "css" / "school-database.css"
SILHOUETTES_DIR = ROOT / "assets" / "images" / "prefecture-silhouettes"
INDEX_HTML = ROOT / "tools" / "school-database" / "index.html"
SCHOOL_DB_DIR = ROOT / "tools" / "school-database"

# 東京都以外46件のSVGは、東京都を本土のみへ変更した際に一切触れていない。
# 生成スクリプトを再実行しても出力が変わらないことの固定リファレンスとして
# SHA-256を記録する（変更する場合は意図的な再生成であることを明示する）。
OTHER_46_SVG_SHA256 = {
    "01-hokkaido.svg": "93bf9fa74b1bc2607d7aaab58f9a146723a246ef6221fd07c5141096b694f0a8",
    "02-aomori.svg": "2c301ac2ee8ab6214b65aeede0b2711ac843764ea1a6f0cbfabb2e380a8dac02",
    "03-iwate.svg": "470c4ad3a4eef68909bad296a0eb3f804c09db010cba4573382aab7e843ea343",
    "04-miyagi.svg": "d648bd5637ce63cf190de591e2e9ef5cd92df446bc6b6524edb153b41f5d264f",
    "05-akita.svg": "c17dce72f12f3d032dea291b2b794ad2b055d1b22a9276168f72dce2f3e14a50",
    "06-yamagata.svg": "1535dfde019d0ea6e14127701df5d9f659a24d3b54deeb7f81b8b597c7253bea",
    "07-fukushima.svg": "a50a9975df5db5589c26b0816b0720f89e11261288902f66c022002fc3d86d60",
    "08-ibaraki.svg": "70ae9515748f3260edcd3d0bf8702746b260c50462d9232bb64a57dff56127df",
    "09-tochigi.svg": "23a39bfc1645afb242c072571388af20f992e2bd10b6b88c34ca14ef8d04ae97",
    "10-gunma.svg": "b1b9d38e3bd41945b4883591d36897108d708604961146f08d8eebd06ec31977",
    "11-saitama.svg": "8aa898c7ff1dfa8b982a2089360e9025a29edf77a231c9251e312b9084e50de1",
    "12-chiba.svg": "e6eacbbc21b2d7173c637e18a0f0157cebd0149ff276ab713fbc0a84685a1e06",
    "14-kanagawa.svg": "cfb8508f3d2fec910432ac4baf94c4618055a49748415932d475941dd788dbc9",
    "15-niigata.svg": "e5494a1bf209d561fbdfb93e4385d6a660a7562df26fbeb119a29bd681fe6554",
    "16-toyama.svg": "30adfef2956b351615fd214432e97862f01857c2722a31a2757b9281d4992066",
    "17-ishikawa.svg": "c60be611f8023edced828c1854581533f772a1f23c94f03e273d2b5dce854135",
    "18-fukui.svg": "969268f2dc989e6a1b6fb8a87733fc0dc5e70d5c6457e5b0cb56be5cfb80f588",
    "19-yamanashi.svg": "cda9242a8ab6831aa7b5ddf11dfb8bc6c329a53f98b98d180f0d6f69bf251ff5",
    "20-nagano.svg": "a3e27c18a4895d987a1911a154dbb7319cd6b8c20149d7af94cd0bd2103e584e",
    "21-gifu.svg": "7aadde76b264860d13cace16e7d29697f2a1ab7885b0fbf4e84a4adff3d5f1c9",
    "22-shizuoka.svg": "95b54ba315e43ea732213f0cf1d7157a64e82fe5658f622e181874c325a41a3b",
    "23-aichi.svg": "6df394a9459360baf7ffc07875dc652b0790af3127af63a890337c27c19a8aa0",
    "24-mie.svg": "2b9f079833e13f0db9404124783eaab01b1d9e9db65fd6af909466826b81de27",
    "25-shiga.svg": "dd3a1cc012317dd0bbbc337329e4ede958b5a96026f2a2cd91af95080d6b63cd",
    "26-kyoto.svg": "654ca78605f5a4acaf1e14360617735a66748430d9b63bb43c9b240ab65c9546",
    "27-osaka.svg": "ed4c34c5c2822145864363094431abf66db6c65606112295d5dfd2ea843477ab",
    "28-hyogo.svg": "b6199581cee99a190d2c98b7126719e4b152301944d167776299b49ba69b43fb",
    "29-nara.svg": "f3d8379b00f27b06bfb6de43fb9c294955322a03ab7fcab8df2c9a13daf5ff8d",
    "30-wakayama.svg": "4bc0a0d8c101a168a6b4a341f77b1e4f7f627ba7347ed8caa478c9a049ff6752",
    "31-tottori.svg": "319cb51b4d9e10adf0537577d5c77a9d5b23369b771292151325d60b78fb6b3f",
    "32-shimane.svg": "08957ec4796374f961d1c0957a13e43d6b0951483868a3e8b4d7d678aee4c611",
    "33-okayama.svg": "f0f8e7b0124ec777c589c9ccaf6127cb9425735f3213cbca25d74bafc76d3c15",
    "34-hiroshima.svg": "5a28907164ad7b480459fc9330079a0585fcd941b2779f616aad2f34c1fc3e50",
    "35-yamaguchi.svg": "05f8193da59495f3cc47bcf54855f6a3214a393fe19b57ed43d45fe6fa36b5e1",
    "36-tokushima.svg": "15519bd78af69603f0ff735e8dc91d5429f379cc581853a14c5860d1261615e5",
    "37-kagawa.svg": "9ad2130110c5f0c01fee699c5de9f926751da59f63e4d1866eb957cb6980346a",
    "38-ehime.svg": "057b46a1708d83433bac371f8496e84b96c4dbfc3b55bfa879fa2ca80ed820e3",
    "39-kochi.svg": "e0a37846fa1a032831f15ff8b6475365dbcffe5ceef61ad613ba90426664d9fc",
    "40-fukuoka.svg": "8f9d1c460a795c941da395d3091d3c4ca787182d0083c30dbae10108c4d9a9fb",
    "41-saga.svg": "cc6ec1c4dfecad4b5a6ee26d5ab38d5444080e180f3b3fad41b0d38f0216a91e",
    "42-nagasaki.svg": "41839d9744e77103d4e692b851db8ff85729bb2e18418ec26c23916ed273f932",
    "43-kumamoto.svg": "a06e63986b2ac54db4b7aeb9623272d32e6f8e921a5fc8adf3cba0220b87b6cc",
    "44-oita.svg": "c4e473cc126542a65d1dd2be8e70ada18527a1ee757dbdee490553d4e4a1429a",
    "45-miyazaki.svg": "2b2c3c5a5a6538314ba2c0d41e074f67f8bf3c0aa6a0d81f0e052100f105894b",
    "46-kagoshima.svg": "c5be2b294de25dc8428a3c1c45c33e012c121496d2fb3b9541cff1326ba0a31f",
    "47-okinawa.svg": "1194137443dae723cd03e59f86ee1a2ce92f7f007dbf20fd9ed6adfcceb00e4c"
}

# 静的HTML方式（.search-box等）を使用する全47都道府県が対象。
# wakayama/oita/miyazaki/kagoshimaも実際にはdb-title/#school-search-app
# 方式ではなく、他43県と同一の.page-hero/.search-box構成で、それぞれ
# 専用のsearch-{slug}.jsを読み込む標準テンプレートであることを
# 2026-08-01に再確認済み（search-core.js欠落による不具合は存在しない）。
STANDARD_TEMPLATE_SLUGS = [
    slug for slug in [
        "hokkaido", "aomori", "iwate", "miyagi", "akita", "yamagata", "fukushima",
        "ibaraki", "tochigi", "gunma", "saitama", "chiba", "tokyo", "kanagawa",
        "niigata", "toyama", "ishikawa", "fukui", "yamanashi", "nagano", "gifu",
        "shizuoka", "aichi", "mie", "shiga", "kyoto", "osaka", "hyogo", "nara",
        "wakayama", "tottori", "shimane", "okayama", "hiroshima", "yamaguchi",
        "tokushima", "kagawa", "ehime", "kochi", "fukuoka", "saga", "nagasaki",
        "kumamoto", "oita", "miyazaki", "kagoshima", "okinawa",
    ]
]

PREFECTURE_CODE_NUMBER = {
    "hokkaido": "01", "aomori": "02", "iwate": "03", "miyagi": "04", "akita": "05",
    "yamagata": "06", "fukushima": "07", "ibaraki": "08", "tochigi": "09", "gunma": "10",
    "saitama": "11", "chiba": "12", "tokyo": "13", "kanagawa": "14", "niigata": "15",
    "toyama": "16", "ishikawa": "17", "fukui": "18", "yamanashi": "19", "nagano": "20",
    "gifu": "21", "shizuoka": "22", "aichi": "23", "mie": "24", "shiga": "25",
    "kyoto": "26", "osaka": "27", "hyogo": "28", "nara": "29", "wakayama": "30",
    "tottori": "31", "shimane": "32", "okayama": "33", "hiroshima": "34", "yamaguchi": "35",
    "tokushima": "36", "kagawa": "37", "ehime": "38", "kochi": "39", "fukuoka": "40",
    "saga": "41", "nagasaki": "42", "kumamoto": "43", "oita": "44", "miyazaki": "45",
    "kagoshima": "46", "okinawa": "47",
}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_47_svg_files_exist_with_correct_codes():
    svg_files = sorted(SILHOUETTES_DIR.glob("*.svg"))
    assert len(svg_files) == 47, f"expected 47 SVG files, got {len(svg_files)}"

    seen_codes = set()
    for path in svg_files:
        match = re.match(r"^(\d{2})-([a-z]+)\.svg$", path.name)
        assert match, f"unexpected filename format: {path.name}"
        code, slug = match.group(1), match.group(2)
        assert PREFECTURE_CODE_NUMBER.get(slug) == code, (
            f"{path.name}: コードとslugの対応が想定と異なります"
        )
        assert code not in seen_codes, f"都道府県コード{code}が重複しています"
        seen_codes.add(code)

    expected_codes = set(PREFECTURE_CODE_NUMBER.values())
    assert seen_codes == expected_codes, (
        f"01〜47のコードが揃っていません。欠落={expected_codes - seen_codes}, "
        f"余分={seen_codes - expected_codes}"
    )


def test_svg_content_is_safe_and_non_empty():
    svg_files = sorted(SILHOUETTES_DIR.glob("*.svg"))
    assert len(svg_files) == 47

    for path in svg_files:
        content = path.read_text(encoding="utf-8")
        assert content.strip(), f"{path.name}: 空ファイルです"
        assert "viewbox" in content.lower(), f"{path.name}: viewBoxがありません"
        assert "<script" not in content.lower(), f"{path.name}: scriptタグが含まれています"
        assert "foreignobject" not in content.lower(), f"{path.name}: foreignObjectが含まれています"
        assert not re.search(r'(href|src)\s*=\s*["\']https?://', content, re.IGNORECASE), (
            f"{path.name}: 外部URL参照が含まれています"
        )
        assert "<path" in content or "<polygon" in content, (
            f"{path.name}: pathまたはpolygon要素が見つかりません"
        )


def test_card_metadata_silhouette_for_all_47():
    payload = _read_json(CARD_METADATA_JSON)
    prefectures = payload["prefectures"]
    assert len(prefectures) == 47

    seen_srcs = set()
    for pref in prefectures:
        assert "silhouette" in pref, f"{pref['prefecture_name']}: silhouetteキーがありません"
        silhouette = pref["silhouette"]
        assert silhouette["available"] is True, (
            f"{pref['prefecture_name']}: silhouette.available が true ではありません"
        )
        assert silhouette["alt"] == "", f"{pref['prefecture_name']}: altが\"\"で統一されていません"
        assert silhouette["src"], f"{pref['prefecture_name']}: srcが空です"

        rel_path = silhouette["src"].lstrip("/")
        file_path = ROOT / rel_path
        assert file_path.is_file(), f"{pref['prefecture_name']}: {file_path} が存在しません"

        expected_code = PREFECTURE_CODE_NUMBER[pref["prefecture_code"]]
        filename = Path(silhouette["src"]).name
        assert filename == f"{expected_code}-{pref['prefecture_code']}.svg", (
            f"{pref['prefecture_name']}: ファイル名 {filename!r} が都道府県コードと一致しません"
        )

        assert silhouette["src"] not in seen_srcs, f"{pref['prefecture_name']}: srcが他県と重複しています"
        seen_srcs.add(silhouette["src"])

        assert silhouette["source"], f"{pref['prefecture_name']}: sourceが空です"
        assert silhouette["reference_date"] == "2026-01-01"

        # 公式章方式（見送り済み）の残骸が本番データに残っていないこと。
        assert "emblem" not in pref, (
            f"{pref['prefecture_name']}: 公式章用のemblemキーが本番データに残っています"
        )


def test_population_and_school_data_unchanged_by_silhouette_addition():
    """silhouette追加が既存の人口・学校DB・地方順・カードリンクに影響
    していないことを再確認する（PR #93/#94の回帰guard）。"""
    card_payload = _read_json(CARD_METADATA_JSON)
    population_payload = _read_json(POPULATION_JSON)
    prefectures = card_payload["prefectures"]

    assert len(prefectures) == 47
    population_by_code = {p["prefecture_code"]: p for p in population_payload["prefectures"]}

    for pref in prefectures:
        assert pref["population"]["available"] is True
        source_ref = population_by_code[pref["prefecture_code"]]
        assert pref["population"]["census_population"] == source_ref["census_population"]
        assert pref["population"]["census_age_3_17"] == source_ref["census_age_3_17"]
        assert pref["school_database"]["record_count"] > 0
        assert pref["url"].startswith("/tools/school-database/")

    assert prefectures[0]["region"]["code"] == "kanto"
    assert prefectures[0]["prefecture_name"] == "東京都"

    region_order = []
    for pref in prefectures:
        code = pref["region"]["code"]
        if not region_order or region_order[-1] != code:
            region_order.append(code)
    assert region_order == [
        "kanto", "hokkaido", "tohoku", "chubu", "kinki", "chugoku", "shikoku", "kyushu",
    ], f"地方順が変更されています: {region_order}"


def test_renderer_wires_silhouette_without_breaking_existing_behavior():
    js = RENDERER_JS.read_text(encoding="utf-8")

    assert "pref-card-title-row" in js
    assert "pref-silhouette" in js
    assert "silhouette.available === true" in js
    assert "--silhouette-url" in js
    assert 'setAttribute("aria-hidden", "true")' in js

    # 既存のカード全体クリック・details除外・キーボード操作の仕組みが維持されていること。
    assert re.search(
        r'closest\(["\']a,\s*button,\s*summary,\s*details,\s*input,\s*select,\s*textarea["\']\)',
        js,
    ), "カード全体クリックのdetails除外処理が失われています"
    assert "keydown" in js and "Enter" in js

    # シルエット自体には独立したリンク（href/data-card-href）を持たせていないこと。
    assert "silhouetteEl.href" not in js
    assert "silhouetteEl.dataset.cardHref" not in js


def test_css_defines_mask_based_silhouette_with_responsive_sizes():
    css = CSS_PATH.read_text(encoding="utf-8")
    assert re.search(r"\.pref-silhouette\s*\{[^}]*width:\s*34px", css), "PC相当(34px)の定義が見つかりません"
    assert re.search(
        r"@media\s*\(max-width:\s*900px\)\s*\{[^{}]*\.pref-silhouette\s*\{[^}]*width:\s*30px", css
    ), "タブレット相当(30px)の定義が見つかりません"
    assert re.search(
        r"@media\s*\(max-width:\s*640px\)\s*\{[^{}]*\.pref-silhouette\s*\{[^}]*width:\s*28px", css
    ), "スマホ相当(28px)の定義が見つかりません"
    assert "mask-image: var(--silhouette-url)" in css
    assert "flex-shrink: 0" in css
    assert ".pref-card:hover .pref-silhouette" in css


def test_all_47_prefecture_pages_show_hero_silhouette():
    """都道府県ポータルのカードだけでなく、各都道府県別ページ（例:
    tools/school-database/tokyo/index.html）のタイトル帯にも同じ地域マーク
    を表示する。"""
    for slug, code in PREFECTURE_CODE_NUMBER.items():
        page_path = SCHOOL_DB_DIR / slug / "index.html"
        assert page_path.is_file(), f"{slug}: index.htmlが見つかりません"
        html = page_path.read_text(encoding="utf-8")

        assert "hero-silhouette" in html, f"{slug}: hero-silhouetteが見つかりません"
        expected_src = f"/assets/images/prefecture-silhouettes/{code}-{slug}.svg"
        assert expected_src in html, f"{slug}: 期待するsrc({expected_src})が見つかりません"
        assert 'aria-hidden="true"' in html
        assert "<h1" in html, f"{slug}: h1が見つかりません"


def test_portal_html_shows_attribution():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "国土数値情報（行政区域データ）」を加工して作成しています" in html, (
        "国土数値情報の出典表記がindex.htmlに見つかりません"
    )
    # 都道府県章・県旗・公式シンボルマークという表記を使っていないこと。
    for prohibited in ("都道府県章", "県章", "公式マーク", "公式シンボル", "県旗"):
        assert prohibited not in html, f"禁止表記 '{prohibited}' がindex.htmlに含まれています"


def test_tokyo_svg_is_mainland_only():
    """東京都のSVGが本土（23区部・多摩地域）のみで、島しょ部の遠隔
    ポリゴンを含まないことを検証する。"""
    svg_path = SILHOUETTES_DIR / "13-tokyo.svg"
    content = svg_path.read_text(encoding="utf-8")

    # 本土は隣接する陸地としてすべて連結しているため、輪郭は1個
    # （サブパス=M(moveto)コマンドが1個）のみになるはず。離島を含めていた
    # 旧版は9個の孤立した輪郭（本土+伊豆諸島+小笠原諸島等）を持っていた。
    subpath_count = content.count("M")
    assert subpath_count == 1, (
        f"東京都SVGのサブパス数が1ではありません（{subpath_count}個）。"
        "本土のみの単一連結領域になっているか確認してください。"
    )

    # viewBoxの縦横比が極端でないこと（島しょ部を含めた旧版はおよそ
    # 170×546、つまり縦横比1:3.2という細長い形状になっていた）。
    match = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', content)
    assert match, "viewBoxが見つかりません"
    width, height = float(match.group(1)), float(match.group(2))
    aspect = max(width, height) / min(width, height)
    assert aspect < 2.5, (
        f"東京都SVGの縦横比が極端です（{aspect:.2f}）。"
        "島しょ部の遠隔ポリゴンが含まれている可能性があります。"
    )


def test_other_46_svg_hashes_unchanged():
    """東京都のみを本土抽出に変更する作業で、他46都道府県のSVGファイルが
    一切変更されていないことを検証する（SHA-256の固定リファレンスと比較）。"""
    assert len(OTHER_46_SVG_SHA256) == 46
    for filename, expected_hash in OTHER_46_SVG_SHA256.items():
        path = SILHOUETTES_DIR / filename
        assert path.is_file(), f"{filename} が存在しません"
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, (
            f"{filename}: SHA-256が変更前と一致しません"
            f"（期待={expected_hash}, 実際={actual_hash}）。"
            "東京都以外のSVGが意図せず再生成された可能性があります。"
        )


def test_47_pages_have_exactly_one_silhouette_no_duplicate_insertion():
    for slug, code in PREFECTURE_CODE_NUMBER.items():
        page_path = SCHOOL_DB_DIR / slug / "index.html"
        html = page_path.read_text(encoding="utf-8")
        count = html.count("hero-silhouette")
        assert count == 1, (
            f"{slug}: hero-silhouetteが{count}個あります（1個のみのはずです。"
            "二重挿入されている可能性があります）"
        )
        assert html.count(f"{code}-{slug}.svg") == 1, (
            f"{slug}: SVGパスへの参照が重複しているか見つかりません"
        )


def test_no_new_badge_remains():
    js = RENDERER_JS.read_text(encoding="utf-8")
    assert "pref-badge" not in js, "レンダラーJSにpref-badge（NEWバッジ）が残っています"
    assert "status_label" not in js, "レンダラーJSにstatus_label（NEWバッジ用）が残っています"

    for slug in PREFECTURE_CODE_NUMBER:
        page_path = SCHOOL_DB_DIR / slug / "index.html"
        html = page_path.read_text(encoding="utf-8")
        assert "pref-badge" not in html, f"{slug}: pref-badge（NEWバッジ）が残っています"


def test_search_form_elements_preserved_on_standard_pages():
    """静的HTML方式（.search-box）の47都道府県すべてのページで、検索
    フォームのinput/select/checkbox/radioおよびCSV・宛名コピー機能の
    要素が維持されていることを確認する（東京都のみ、並び順機能と
    Google Maps文言を持たない旧来の別テンプレートのため一部項目を
    対象外とする）。"""
    assert len(STANDARD_TEMPLATE_SLUGS) == 47

    for slug in STANDARD_TEMPLATE_SLUGS:
        page_path = SCHOOL_DB_DIR / slug / "index.html"
        html = page_path.read_text(encoding="utf-8")

        assert 'id="keyword"' in html, f"{slug}: キーワード入力欄がありません"
        assert 'id="city"' in html and "<select" in html, f"{slug}: 自治体選択が見つかりません"
        if slug != "tokyo":
            # 東京都ページのみ、並び順機能を持たない旧来の別テンプレート
            # （tools/tokyo-school-address/style.css）を使用しており、
            # これは今回の変更以前からの既存差分（回帰ではない）。
            assert 'id="sort-order"' in html, f"{slug}: 並び順選択が見つかりません"
        assert 'type="checkbox"' in html and "establishment-type" in html, (
            f"{slug}: 設置区分チェックボックスが見つかりません"
        )
        assert 'type="checkbox"' in html and "school-type" in html, (
            f"{slug}: 学校種チェックボックスが見つかりません"
        )
        assert 'type="radio"' in html and "honorific" in html, (
            f"{slug}: 宛名選択のラジオボタンが見つかりません"
        )
        assert 'id="csv-download-btn"' in html, f"{slug}: CSVダウンロードボタンが見つかりません"
        if slug != "tokyo":
            # 東京都ページの静的な説明文にはGoogle Mapsの文言がそもそも
            # 含まれていない（既存の別テンプレートによる差分であり、
            # 今回の変更で削除したものではない）。
            assert "Google Maps" in html, f"{slug}: Google Maps関連の記述が見つかりません"


if __name__ == "__main__":
    test_47_svg_files_exist_with_correct_codes()
    test_svg_content_is_safe_and_non_empty()
    test_card_metadata_silhouette_for_all_47()
    test_population_and_school_data_unchanged_by_silhouette_addition()
    test_renderer_wires_silhouette_without_breaking_existing_behavior()
    test_css_defines_mask_based_silhouette_with_responsive_sizes()
    test_all_47_prefecture_pages_show_hero_silhouette()
    test_portal_html_shows_attribution()
    test_tokyo_svg_is_mainland_only()
    test_other_46_svg_hashes_unchanged()
    test_47_pages_have_exactly_one_silhouette_no_duplicate_insertion()
    test_no_new_badge_remains()
    test_search_form_elements_preserved_on_standard_pages()
    print("Prefecture silhouette integration tests passed successfully.")
