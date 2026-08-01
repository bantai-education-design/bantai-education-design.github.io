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
    "01-hokkaido.svg": "6268b81825f651e071ab707468cb9b0e2f7b03a7658b090a5622f0a6839a88f2",
    "02-aomori.svg": "d7c6a7f5dd81149d9a49d5b283dc428cb0c76c3a11601abcd31ef8410d63adfa",
    "03-iwate.svg": "1aa862d665eec5e476068d28ef238f517d8c2bbfb13f81e76cec85722382791f",
    "04-miyagi.svg": "fc598cf26626fde91f6143f7209da30febc09504e8e9d24448fbc716228769dc",
    "05-akita.svg": "8e0ef2ddfc585e74d54852f50fb349ea77239a2d4287030d15cafc45149b5223",
    "06-yamagata.svg": "76029f198dd7d1c2d65548b8a5ef1246b73521be84d26b7319ddee8ffa339ed9",
    "07-fukushima.svg": "dabcc348cf1a3e31fcb961ed70e85536d86ec70bfd3a92d26d3e2b77130b2b8c",
    "08-ibaraki.svg": "fc0ec7d6ee95ea5e72a1028f2eeeecfdd4de85cd69d8d9ea5610bf0e5450d69c",
    "09-tochigi.svg": "6a3adf6770f440526fd9ba8fbd16b9767513541c07df72a51f54efceed6a5574",
    "10-gunma.svg": "2f8fad7898ebf2c67b0d4bdf02ef891da4ca7d534b03559188b9dbc697864dc3",
    "11-saitama.svg": "9d49164456306569f51b581c4b36c91a6f641790421738cc4183e6ccc1206d88",
    "12-chiba.svg": "7333204692c35bb815d996e369212d2ad79f5882d15f03c81558ae13e3d6cd05",
    "14-kanagawa.svg": "17bc4d33095c9923b7ca6de40cc9d10cac8dd3c537f6201d041055796f2cf645",
    "15-niigata.svg": "39b9f40e89fa5652e570531d56329969d60c00eee4ef57ddbfaf7d0202e657ca",
    "16-toyama.svg": "ac5789f5c2ebe4041ee4eb62d5d6d4bd90cbbe11c715aa2cabf07f800a8f070d",
    "17-ishikawa.svg": "3f44c3e4266c2791f09d6d01d07f05c8ae80473c252025e0d68e41c0c6a3f9b1",
    "18-fukui.svg": "54f301debc2256e200e399825292ea4b3bc24cc4eeb61864c61fb80e687f538e",
    "19-yamanashi.svg": "66aa87f0dff2207532c274c84f4ad4f0ca78ac63712c66f19383e265fb62ee56",
    "20-nagano.svg": "5915ae26c40354f3245dcf7ce554f3d2786fd52cd53b80d93571efca83be6d94",
    "21-gifu.svg": "477f4ef512c2eeb7255b151f4246d57a49a24aec7b4c306a6b4be2b5be70b7fa",
    "22-shizuoka.svg": "9ecda5dbeb3f94842a56d24b5b6cd8006c1292ee1290e23fe8fee5c24b45d9e4",
    "23-aichi.svg": "e6473ed52dd4d02cd6e6b997bb36a9452c1d1c60430a6e8cea00a38da4177f0a",
    "24-mie.svg": "59146eead7f231098f8a9cc55f3a97653e2a0dbc28eb78d8a640472f1368a1c9",
    "25-shiga.svg": "6d19de317e404ada29a4ed29d772e1a74646f9a2754f91a9267cf1e159e7bc31",
    "26-kyoto.svg": "b87c30e6d15b5f80cf1fff06d6bf76b5240bc54054d7996c8eeb507901ade552",
    "27-osaka.svg": "84e013de82874654cad4b385bbc6e303a23b812a9ea014b8fb29ff9d7ce1371f",
    "28-hyogo.svg": "bb9a5a4b7ee892e4e7cfee1c33405ef8fc985ed41cfa8529705892d301424b67",
    "29-nara.svg": "9972ee1e7adaf16fd8850ac8a10852e629dfc3ef89332e7534dc3d4397b2898f",
    "30-wakayama.svg": "1b38b69746caf602ad8315491b36ba0831fffc1c99a0c650796ae6a81116975b",
    "31-tottori.svg": "12d41fc892210374875820b2b1750aa5e427e8231e072e5652d30d75a930c07f",
    "32-shimane.svg": "ff3a5586e72e934ec867add8caa34aeff3d208147c33b067864a54f6e4fd1015",
    "33-okayama.svg": "3d953870bae165a4373beef6327753a3db2ba4bdd5ca5d7df8992e4b52295280",
    "34-hiroshima.svg": "6714c90635f02510840223384580434e77ffccb271b07609355d8eb8a0e3d776",
    "35-yamaguchi.svg": "25b0b35e5890bed13047049378e6b5a736748ced62849e1043970348e73a2573",
    "36-tokushima.svg": "aae1676338f070768f5be260ee5a19abd5611263dbc5a38eb5970b48817e9f62",
    "37-kagawa.svg": "44274c8a0f6fcb9bf92a429db71d214187800f8a58adcd162f1083a0fe3a7eb4",
    "38-ehime.svg": "679a428a62f447b8f5218fcbec8f661fc50451696d7a413c42617c3868f9ebaf",
    "39-kochi.svg": "9ea5898bbe1fd227c4817c897f90c326dc7601e759308fa4ec77faa425d95a9b",
    "40-fukuoka.svg": "67e470c9fb4a84aa48637a9c1cb64cbea52741b1daa63dbc085c1f3dfbf3861e",
    "41-saga.svg": "a1f741b53bd0f41f76cff83c1690a52d54d81e36f9dcce2a6679ab2178cb96c4",
    "42-nagasaki.svg": "c990e54a04655a451ad4945665f7a9817854946814113d6498d5d37c0fd29fbc",
    "43-kumamoto.svg": "fc114f87b56c19dae6cc11195e943ea3bb8759126cce197bf0c2eebe689f6394",
    "44-oita.svg": "5ae145b3172ace3f83f73aae615e400a5642d7c23d986aa225fcd71f0d9ac066",
    "45-miyazaki.svg": "fc42f5548fd6bf21ece5242ff9b241a72645ad5ed4b0d138014e2b8ae076be25",
    "46-kagoshima.svg": "0de6e253ccddcff0fcba932c2ee7b48f08c64be80f17c5665b69a744d6096e74",
    "47-okinawa.svg": "295e9682ad0efa86516f2e94b8994273b8c3a95e323c8cf561bb2b3ecdcaae7b",
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
    assert re.search(r"\.pref-silhouette\s*\{[^}]*width:\s*32px", css), "PC相当(32px)の定義が見つかりません"
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
