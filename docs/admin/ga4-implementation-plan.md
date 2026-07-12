# Ban.Tai 公式HP GA4実装方針メモ

## 1. 現状確認結果

2026年7月12日時点では、Ban.Tai公式HPリポジトリ内に本番用GA4測定IDらしき `G-XXXXXXXXXX` は確認できませんでした。

一方で、次のGA4関連実装は存在します。

- `tools/tokyo-school-address/index.html` に `G-REPLACE_ME` のプレースホルダーがある
- `tools/tokyo-school-address/index.html` に `gtag`、`googletagmanager`、`dataLayer` の記述がある
- `tools/tokyo-school-address/search.js` に `gtag('event', eventName, params)` を呼び出す `trackEvent` 関数がある
- 複数ページで `/assets/js/analytics-events.js` が読み込まれている
- `assets/js/analytics-events.js` はGA4ではなくKARTE向けのクリックイベント送信スクリプトとして作られている

今回は、GA4本番測定IDの差し替えや計測実装は行いません。`G-REPLACE_ME` はプレースホルダーとして維持します。

## 2. `G-REPLACE_ME` の検出箇所

`G-REPLACE_ME` は次の1ファイルで検出されました。

| ファイル | 行 | 内容 |
| --- | ---: | --- |
| `tools/tokyo-school-address/index.html` | 16 | `https://www.googletagmanager.com/gtag/js?id=G-REPLACE_ME` |
| `tools/tokyo-school-address/index.html` | 21 | `gtag('config', 'G-REPLACE_ME')` |

この値は本番GA4測定IDではなく、差し替え前のプレースホルダーです。

## 3. `analytics-events.js` の読み込み箇所

`/assets/js/analytics-events.js` は次のページまたはテンプレートで読み込まれています。

| ファイル |
| --- |
| `index.html` |
| `about/index.html` |
| `contact/index.html` |
| `legal/index.html` |
| `monitor/index.html` |
| `products/index.html` |
| `products/class-roster/index.html` |
| `products/classroom-seat-designer/index.html` |
| `products/education-planning/index.html` |
| `products/first-staff-paper/index.html` |
| `products/houganshi/index.html` |
| `products/id-photo/index.html` |
| `products/kanji-practice/index.html` |
| `products/music-tools/index.html` |
| `products/observation-card/index.html` |
| `products/resume-generator/index.html` |
| `products/school-work/index.html` |
| `products/staff-paper/index.html` |
| `products/text-overlay/index.html` |
| `templates/product-detail.html` |
| `templates/products-page.html` |
| `tools/tokyo-school-address/index.html` |

## 4. 既存イベント計測コードの概要

### `assets/js/analytics-events.js`

`assets/js/analytics-events.js` は、ページ内のリンクやボタンを監視し、対象リンクがクリックされたときにKARTEへ `click_action` イベントを送る想定のスクリプトです。

現在の主な判定対象は次のとおりです。

- ZIP、EXE、`download` 属性、`/downloads/`、GitHub Releasesなどの無料ダウンロード導線
- `booth.pm` へのBOOTH導線
- `docs.google.com/forms` へのGoogleフォーム導線

送信先はGA4ではなく、`krt('send', 'click_action', { item_name })` です。`gtag` は使っていません。

### `tools/tokyo-school-address/search.js`

`tools/tokyo-school-address/search.js` にはGA4向けの `trackEvent` 関数があります。

```js
gtag('event', eventName, params);
```

現在送信を想定しているイベントは次のとおりです。

| イベント名 | 用途 |
| --- | --- |
| `school_search` | 学校検索キーワード入力 |
| `school_municipality_filter` | 区市町村フィルター |
| `school_type_filter` | 学校種別フィルター |
| `school_establishment_filter` | 設置区分フィルター |
| `school_address_copy` | 宛名コピー |
| `school_csv_download` | CSVダウンロード |
| `envelope_app_click` | 封筒関連アプリへの導線クリック |

ただし、`tools/tokyo-school-address/index.html` の測定IDは `G-REPLACE_ME` のままなので、本番GA4計測としては未完成です。

## 5. 本番GA4測定IDの扱い方の選択肢

### 案A: HTML/JSへ直接記載する

GitHub Pagesでは一般的な方法です。`G-REPLACE_ME` を本番GA4測定IDに置き換え、配信されるHTMLに測定IDが含まれる形にします。

メリット:

- 実装が簡単
- 静的サイトと相性がよい
- GitHub Pagesの標準運用に近い
- ローカル確認やレビューがしやすい

注意点:

- 測定IDはブラウザから見える
- ID差し替え履歴がGitに残る
- 複数ファイルに直書きすると更新漏れが起きやすい

### 案B: GitHub Actions secrets または variables からビルド時に注入する

GitHub ActionsのsecretsまたはvariablesにGA4測定IDを置き、ビルド時にHTMLやJSへ注入する方法です。

メリット:

- リポジトリ本文には測定IDを残しにくい
- 環境ごとに測定IDを切り替えやすい
- 将来的に複数環境を運用する場合に拡張しやすい

注意点:

- 管理が少し複雑になる
- 最終的に配信されるHTML/JS上では測定IDは見える
- GitHub Pagesの静的サイト運用としてはやや高度
- 現在の公開フローにビルド処理を追加する必要がある可能性がある

### 案C: まだ実装せず、`G-REPLACE_ME` を維持する

今回の推奨です。まず設計を固め、本番GA4測定IDの取得・管理方法を決めてから安全に実装します。

メリット:

- 本番IDを誤ってコミットしない
- 実装範囲を広げずに方針を確認できる
- 既存のKARTE計測や東京学校住所ツールのGA4プレースホルダーとの関係を整理できる

注意点:

- 本番GA4計測はまだ開始されない
- 次フェーズで実装PRが必要になる

## 6. 推奨方針

今回は案Cを採用し、`G-REPLACE_ME` を維持します。

次フェーズで本番GA4測定IDを確認してから実装します。将来実装する場合は、Ban.Tai公式HPの運用負荷を考えると、まずは案Aを基本候補とします。GitHub Actions運用に慣れていて、ビルド時注入の保守体制を用意できる場合のみ案Bを検討します。

GA4測定IDは、配信後のHTMLから閲覧できる設定値です。そのため、APIキー、購入者情報、ライセンスキー、メールアドレスのような秘密情報とは性質が異なります。ただし、リポジトリ運用ルールとして「本番IDをGit履歴に残したくない」場合は、案Bを検討します。

## 7. 実装する場合の対象ファイル案

次フェーズでGA4を実装する場合の対象候補は次のとおりです。

| 対象 | 目的 |
| --- | --- |
| `tools/tokyo-school-address/index.html` | 既存の `G-REPLACE_ME` を本番IDへ置き換える、または注入対象にする |
| `assets/js/analytics-events.js` | 将来、BOOTH、Vector、note、無料ダウンロードなどをGA4イベントとして送る場合の整理対象 |
| `index.html` | 公式HPトップのGA4タグ導入候補 |
| `products/index.html` | 商品一覧ページのGA4タグ導入候補 |
| `products/*/index.html` | 商品詳細ページのGA4タグ導入候補 |
| `templates/product-detail.html` | 商品詳細ページのテンプレート反映候補 |
| `templates/products-page.html` | 商品一覧ページのテンプレート反映候補 |
| GitHub Actions workflow | 案Bを採用する場合の測定ID注入処理 |

今回のPRでは、これらのHTML、CSS、JavaScript、商品データは変更しません。

## 8. 実装前にユーザーが準備するもの

次フェーズの実装前に、管理者側で次を確認します。

1. GA4プロパティを作成済みか。
2. Webデータストリームを作成済みか。
3. 本番GA4測定IDを確認済みか。
4. 測定IDをGitに直接残してよいか。
5. GitHub Actions variablesまたはsecretsで管理したいか。
6. 管理者や開発者アクセスをGA4から除外する方針があるか。
7. KARTE計測を継続するか、GA4へ寄せるか、併用するか。

本番GA4測定ID、APIキー、購入者情報、ライセンスキー、メールアドレスは、この設計書やPR本文には記載しません。

## 9. 計測したいイベント名案

将来、公式HP全体で計測したいイベント名案は次のとおりです。

| イベント名 | 用途 |
| --- | --- |
| `click_booth` | BOOTHボタンクリック |
| `click_vector` | Vectorボタンクリック |
| `click_note` | noteボタンクリック |
| `click_free_download` | 無料ダウンロードボタンクリック |
| `click_textbook_publisher` | 教科書会社公式HPボタンクリック |
| `click_textbook_plan` | 年間指導計画ページボタンクリック |
| `product_search` | 商品検索 |
| `product_filter` | 商品フィルター |

イベントパラメータは、個人を特定できない範囲に限定します。候補は `product_name`、`product_category`、`link_type`、`destination_domain`、`page_path` などです。

## 10. 実装時の注意事項

- 本番GA4測定IDは、今回の設計PRではコミットしない。
- `G-REPLACE_ME` はプレースホルダーとして扱う。
- APIキー、購入者情報、ライセンスキー、メールアドレスは含めない。
- 個人を特定できる情報をGA4イベントパラメータに入れない。
- 公開サイトの見た目や挙動を変更しない範囲で実装する。
- `analytics-events.js` は現在KARTE向けなので、GA4対応を追加する場合はKARTE計測との併用方針を先に決める。
- 商品検索やフィルターは、入力文字列をそのまま送るかどうかを慎重に決める。
- 教科書会社リンク集では、学校名や個人名を送らない。
- 実装後はGA4 DebugView、ブラウザコンソール、ネットワークタブで確認する。

## 11. 実装後の検証手順

次フェーズでGA4を実装した後は、次の手順で検証します。

1. 本番GA4測定IDが意図した方法で反映されているか確認する。
2. 配信HTMLに `G-REPLACE_ME` が残っていないか確認する。
3. ローカルまたは検証環境でJavaScriptエラーが出ていないか確認する。
4. GA4 DebugViewでページビューが届くか確認する。
5. BOOTH、Vector、note、無料ダウンロードのクリックイベントが届くか確認する。
6. 商品検索、商品フィルターイベントが届くか確認する。
7. 教科書会社公式HP、年間指導計画ページのクリックイベントが届くか確認する。
8. イベントパラメータに個人情報や不要な値が含まれていないか確認する。
9. GitHub Pagesのデプロイが成功しているか確認する。
10. GoogleスプレッドシートまたはLooker Studioで見える化する項目を確認する。
