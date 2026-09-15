# GA4計測一本化・本人除外・コラム計測 改修記録 (Walkthrough)

## 1. 実施概要

本改修は、Ban.Tai Education Design 公式サイトにおけるアクセス解析を Google Analytics 4（GA4: `G-KPGJ0R2KXR`）へ一本化し、本人除外ロジック、主要イベント計測、コラム閲覧エンゲージメント計測、および運用ドキュメントを整備したものです。

## 2. コミット履歴と実施内容

| コミット番号 | コミットID | タイトル・主な内容 |
|---|---|---|
| **Commit 1** | `47eddbd` | `feat(analytics): unify GA4 tag across 88 public pages with pre-config inline exclusion and audit 98 HTML files`<br>- 全98HTMLの分類監査（公開88、管理6、テンプレート3、検証1）<br>- 公開88ページへのPre-config Inline Exclusion付きGA4タグ統一<br>- テンプレート2ページからのGA4タグ除去<br>- 自動監査スクリプト `tools/audit_html_ga4.py` の追加<br>- Draft PR #333 の早期作成 |
| **Commit 2** | `9d3d8c3` | `feat(analytics): add GA4 core event tracking with PII sanitization, duplicate prevention and KARTE parity`<br>- `assets/js/analytics-events.js` の改修<br>- URLサニタイズ（クエリ、ハッシュ、mailtoのマスキング）<br>- 重要イベント（BOOTH、モニターフォーム、ライセンス、製品詳細、DBナビゲーション、お問い合わせ）の実装<br>- file_download のGA4拡張計測委任（手動二重送信防止）<br>- KARTE既存処理および教育計画PV計測の維持 |
| **Commit 3** | `26a7a85` | `feat(analytics): add column GA4 engagement tracking with strict duration thresholds and duplicate prevention`<br>- `assets/js/columns.js` の改修<br>- `column_view`、`column_engagement`、`column_next_action` の実装<br>- 滞在時間基準（5秒未満は非送信、5〜14秒は短時間、15秒以上は一定時間閲覧）の実装<br>- モーダル終了、別記事切替、記事内リンク、ページ離脱での二重送信防止ガード |
| **Commit 4** | `c76a470` | `docs(admin): add GA4 specifications, operation guides and document validation test`<br>- `docs/admin/` 配下の仕様書・手順書の整備<br>- ドキュメント品質検証テスト `tools/check_docs_ga4.py` の追加 |
| **Commit 5** | `5f62fe9` | `fix(analytics): unify admin exclusion parameter to bantai_admin and add event verification tests`<br>- 除外URLパラメータを `?bantai_admin=true` / `?bantai_admin=clear` に完全統一<br>- 全公開88HTML、JS、仕様書、手順書の表記統一<br>- イベント発火・サニタイズ・二重送信防止の自動検証テスト `tools/test_analytics_events.js` の追加 |
| **Commit 6** | 本コミット | `fix(analytics): add read_time_sec metric, address bar replaceState cleanup, and refine realtime verification guides`<br>- `assets/js/columns.js` に `read_time_sec` を追加し、GA4カスタム指標として仕様書・レポート手順書に整備<br>- 全88公開HTMLのPre-config Inline Exclusionスクリプトに `window.history.replaceState` によるアドレスバー・閲覧履歴クエリ消去処理を実装<br>- `docs/admin/admin-exclusion-guide.md` の確認手順を整理（リアルタイムレポートを第一選択、DebugViewをTag Assistant併用の詳細検証用として位置づけ）<br>- `tools/audit_html_ga4.py` および `tools/test_analytics_events.js` を拡張し自動検証 |

## 3. 検証結果一覧

### 3.1 静的検証・構文確認
- `git diff --check`: エラーなし（行末空白、不整合なし）
- `node -c assets/js/analytics-events.js`: 構文正常
- `node -c assets/js/columns.js`: 構文正常

### 3.2 自動化テスト
- `node tools/test_analytics_events.js`: イベント発火、サニタイズ、除外判定、replaceStateによるURLクリーンアップ、コラム滞在時間および `read_time_sec` 計測ロジック全件合格（PASS）
- `python tools/audit_html_ga4.py`: 98HTML全件の分類・タグ設置・replaceStateスクリプト設置チェック通過（PASS）
- `python tools/check_products.py`: 12製品のバリデーション通過（PASS）
- `python tools/check_product_detail.py`: 学級名簿メーカー詳細ページのバリデーション通過（PASS）
- `python tools/check_docs_ga4.py`: ドキュメント内の禁止語句（絶対パス、不正確な表現等）排除チェック通過（PASS）

### 3.3 本人操作が必要な未実施項目
以下の項目は、管理者の Google アカウント認証および実通信環境が必要となるため、本PRでは未実施とし、手順書（`docs/admin/`）を整備して管理者に引き継ぎます：
- GA4 リアルタイムレポートまたは DebugView による本番実受信のリアルタイム目視確認
- Google Search Console と GA4 のサービス間リンク設定（`docs/admin/search-console-ga4-link-guide.md` 参照）
- GA4 管理画面でのカスタム定義（ディメンションおよび指標 `read_time_sec`）の登録
