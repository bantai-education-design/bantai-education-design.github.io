# 千葉県学校データ 原本管理表

更新日: 2026-07-24
作業ブランチ: `feature/school-database-chiba-phase1`
原本保存先: `data-source/chiba/2025/`（Git管理外、ローカル作業用）

## 収録対象（今回のスコープ）

- 国立・公立幼稚園
- 公立幼保連携型認定こども園
- 国立・公立小学校
- 私立小学校
- 国立・公立中学校
- 私立中学校
- 義務教育学校
- 中等教育学校
- 公立・私立高等学校
- 国立・公立特別支援学校
- 私立幼稚園

専修学校・各種学校・大学は対象外（埼玉県版・東京都版と同じ除外方針）。

> [!IMPORTANT]
> 千葉県版は「公立幼保連携型認定こども園」を収録対象に含む。これは埼玉県版・東京都版が
> 初版で除外した項目（[common-data-schema.md](../common-data-schema.md) 6項）と異なる。
> `school_type` の値に「幼保連携型認定こども園」を追加するか、`school_type=幼稚園` に
> フラグを立てるかを変換設計時に確定する。

## 公立学校（国・公立）

### 基礎原本

- 資料名: 令和7年版千葉県教育便覧 V学校名簿 5-1 国・公立学校名簿
- 基準日: 令和7年5月1日（2025-05-01）
- 出典ページ: https://www.pref.chiba.lg.jp/kyouiku/seisaku/kouhou/kyouikubinran/r7.html
- ファイルURL（Excel）: https://www.pref.chiba.lg.jp/kyouiku/seisaku/kouhou/kyouikubinran/documents/5-1-r7.xls
- ファイルURL（PDF、照合用）: https://www.pref.chiba.lg.jp/kyouiku/seisaku/kouhou/kyouikubinran/documents/5-1-r7.pdf
- 保存名: `5-1-r7_koritsu_meibo.xls` / `.pdf`
- 収録校種: 国・公立幼稚園、公立幼保連携型認定こども園、国・公立小学校、国・公立中学校、
  公立義務教育学校、公立中等教育学校、公立高等学校、国・公立特別支援学校（単一ファイルに統合）
- ダウンロード日: 2026-07-24

### 補正資料（新設・統合・廃止・名称変更）

- 資料名: 公立学校一覧（令和7→8年度 変更一覧）
- 更新日: 令和8年4月24日（2026-04-24）
- 出典ページ: https://www.pref.chiba.lg.jp/kyouiku/seisaku/kouhou/gakkou-ichiran/index.html
- ファイルURL（Excel）: https://www.pref.chiba.lg.jp/kyouiku/seisaku/kouhou/gakkou-ichiran/documents/r8-gakkouichiran-2.xls
- ファイルURL（PDF）: https://www.pref.chiba.lg.jp/kyouiku/seisaku/kouhou/gakkou-ichiran/documents/r8-gakkouichiran-2.pdf
- 保存名: `r8-gakkouichiran-2_henkou_ichiran.xls` / `.pdf`
- 内容: 新設校（例: 八千代市立みどりが丘第二小学校）、統合による廃止校（例: 館山市・富津市の統廃合、
  横芝光町立日吉小学校、勝浦市立興津小学校の他校統合）、名称変更（例: 富津市立大貫小学校→
  富津市立大佐和小学校）
- 参考: 前年度版 `r7-gakkouichiran-2.xls/.pdf`（令和6→7年度差分、照合用に同ページで入手可）
- ダウンロード日: 2026-07-24

> [!NOTE]
> 5-1-r7 の基準日（2025-05-01）と gakkou-ichiran の更新日（2026-04-24）の間に発生した
> 新設・統合・廃止・名称変更を、この補正資料で反映する。県立学校名簿ページ
> （https://www.pref.chiba.lg.jp/kyouiku/seisaku/miryoku/kenritsu.html）は令和5年度時点の
> 情報で更新が止まっており、今回は一次資料として採用しない。

## 私立学校

すべて総務部学事課の公式ページから取得。基準日はすべて令和8年5月1日現在（2026-05-01）。

| 校種 | ページURL | Excel URL | 保存名 |
| :--- | :--- | :--- | :--- |
| 私立幼稚園 | https://www.pref.chiba.lg.jp/gakuji/shiritsutou/shiritsugakkou/youchienmeibo.html | https://www.pref.chiba.lg.jp/gakuji/shiritsutou/shiritsugakkou/documents/r8youchien.xlsx | `r8youchien_shiritsu.xlsx` |
| 私立小学校 | https://www.pref.chiba.lg.jp/gakuji/shiritsutou/shiritsugakkou/shougaku-meibo.html | https://www.pref.chiba.lg.jp/gakuji/shiritsutou/shiritsugakkou/documents/r8syougaku.xlsx | `r8syougaku_shiritsu.xlsx` |
| 私立中学校・中等教育学校（前期） | https://www.pref.chiba.lg.jp/gakuji/shiritsutou/shiritsugakkou/chuugaku-meibo.html | https://www.pref.chiba.lg.jp/gakuji/shiritsutou/shiritsugakkou/documents/r8chugaku.xlsx | `r8chugaku_shiritsu.xlsx` |
| 私立高等学校・中等教育学校（後期） | https://www.pref.chiba.lg.jp/gakuji/shiritsutou/shiritsugakkou/koukou-meibo.html | https://www.pref.chiba.lg.jp/gakuji/shiritsutou/shiritsugakkou/documents/r8koukou.xlsx | `r8koukou_shiritsu.xlsx` |

問い合わせ先: 総務部学事課 私学振興班（043-223-2155）／ 幼稚園振興班（043-223-2156）

> [!NOTE]
> 私立中等教育学校は前期課程（chugaku-meibo）と後期課程（koukou-meibo）に分かれて掲載されている。
> 埼玉県版の「中等教育学校」1レコード化方針を踏襲し、前期・後期を同一校として統合するか、
> 埼玉県に中等教育学校の私立校が存在しないため新規判断が必要（変換設計時に確定）。

## 除外した資料

- 私立各種学校名簿（kakushu-meibo.html）: 外国人学校・看護・漁業・芸術・簿記珠算・和洋裁・日本語教育等。
  スコープ対象外（各種学校）のため不採用。
- 私立専修学校名簿（senshuu-meibo.html）: スコープ対象外（専修学校）のため不採用。
- 県立学校名簿（kenritsu.html）: 令和5年度時点で更新停止。教育便覧R7 + 変更一覧R8を優先。

## ダウンロード済み原本一覧

`data-source/chiba/2025/` に保存済み（Git管理外）。

```text
5-1-r7_koritsu_meibo.xls              691,200 bytes
5-1-r7_koritsu_meibo.pdf              608,094 bytes
r8-gakkouichiran-2_henkou_ichiran.xls   35,840 bytes
r8-gakkouichiran-2_henkou_ichiran.pdf   41,270 bytes
r8youchien_shiritsu.xlsx                42,636 bytes
r8syougaku_shiritsu.xlsx                11,919 bytes
r8chugaku_shiritsu.xlsx                 14,085 bytes
r8koukou_shiritsu.xlsx                  18,551 bytes
```

すべてダウンロード直後にファイル形式を検証済み（xls: Composite Document File V2 / xlsx: Microsoft Excel 2007+ / pdf: PDF document）。エラーページやHTML誤取得はなし。

## 原本利用ルール（埼玉県版を踏襲）

- 原本ファイルは加工前の状態で保存する。
- 加工データとは別フォルダーで管理する（`data-source/` は変換元、`data/school-database/` は変換後公開データ）。
- ダウンロード日、基準日、元ページ、ファイル名を本表に記録する。
- 学校名、住所、電話番号を推測で補わない。
- 修正が必要な場合は修正理由と確認元を記録する。
