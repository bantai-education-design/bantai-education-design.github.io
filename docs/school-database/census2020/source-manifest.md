# 令和2年国勢調査 表2-1 原本管理表

更新日: 2026-08-01
対象: 47都道府県共通の人口メタデータ（`data/school-database/prefecture-population.json`）

## 採用方式: 原本をGitで管理する

`data-source/census2020/table2-1.xlsx` として原本ファイルをリポジトリに含める方式を採用した。

判断理由:

- ファイルサイズが468KB（478,236バイト）と小さく、リポジトリ容量への影響は軽微。
- e-Statのダウンロード導線は複数ステップのUI操作を経由するため、公式URL＋取得
  スクリプト方式にすると将来的なページ構造変更の影響を受けやすい。原本を直接
  保存することで、`tools/school-database/generate_prefecture_population_metadata.py`
  がネットワークに一切依存せず、いつでも同一の47都道府県分データを再現できる。
- 47都道府県すべてに影響する共通の一次資料であり、都道府県別の一時的な
  作業ファイル（例: `data-source/hiroshima/`等、Git管理外で運用しているもの）
  とは性質が異なる。

他の都道府県の`data-source/<県名>/`配下（作業用スクリプトや個別収集ファイル）
とは扱いを分け、本ディレクトリは常にこの1ファイルのみを保持する方針とする。

## 原本情報

- 統計調査: 令和2年国勢調査 人口等基本集計
- 表: 第2-1表「男女，年齢（各歳），国籍総数か日本人別人口，平均年齢及び
  年齢中位数－全国，都道府県，21大都市，特別区，人口50万以上の市」
- 統計表ID（statInfId）: 000032142404
- 検索元ページ: https://www.e-stat.go.jp/stat-search/files?cycle=0&tclass=000001125102
- ダウンロードURL: https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032142404&fileKind=0
- 公開更新日（e-Stat上の表示）: 2021-11-30
- 取得日: 2026-07-31
- ファイル形式: Excel（.xlsx）、シート名 `b02_01`
- ファイルサイズ: 478,236 バイト（468KB）
- SHA-256: `b8e395c1341f1772d153343ed0435c5f656c888ab33127c7bed88d170cc733bf`

## ライセンス・出典表記

政府統計の総合窓口（e-Stat）で公開されるデータは「政府標準利用規約（第2.0版）」
（https://www.e-stat.go.jp/terms-of-use）に基づき、出典を明記のうえでの複製・
公衆送信・翻案等の二次利用が認められている。本サイトでは各都道府県カードの
人口表示に「出典：令和2年国勢調査」「統計基準日：2020年10月1日現在」を常時
表示し、出典を明記している（`assets/js/school-database/prefecture-card-renderer.js`
の`population-source-line`）。

## 手動加工の有無

`data-source/census2020/table2-1.xlsx` はe-Statからダウンロードした状態のまま
コミットしており、値の書き換え・行列の削除・再保存等の手動加工は一切行って
いない（SHA-256が変化していないことで担保する）。数値の抽出・集計は、原本を
読み取り専用（`openpyxl.load_workbook(..., data_only=True)`）で開く
`generate_prefecture_population_metadata.py` が行う。

## 再現手順

```bash
python tools/school-database/generate_prefecture_population_metadata.py
python tools/school-database/integrate_population_into_card_metadata.py
```

上記2コマンドを実行すると、`data-source/census2020/table2-1.xlsx` から
`data/school-database/prefecture-population.json`（47件）を再生成し、
`data/school-database/prefecture-card-metadata.json` の各都道府県エントリへ
統合する。同一の原本ファイルから実行する限り、出力は毎回バイト単位で
一致する（`tests/test_generate_metadata.py::test_population_generation_script_is_idempotent`
で検証）。

## 不要ファイルの混入確認

`data-source/census2020/` 配下には `table2-1.xlsx` の1ファイルのみが存在し、
中間生成物・別版Excel・一時ファイルは含まれていないことを確認済み。
