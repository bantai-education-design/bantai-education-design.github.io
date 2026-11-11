# 管理センター初期実装：検証記録

2026-11-11。対象ブランチ `feat/bantai-admin-center`。本番へのデプロイ・main編集・PRマージ・本番データ削除は実施していない。

## 実行結果

- `npm test --prefix services/admin-center`: 13件成功。
  - 認証失敗、Origin/CSRF、ログアウト失効、期限切れ、試行回数制限、Secure/HttpOnly/host cookie。
  - 下書きの永続化、世代競合409、復元で新規世代、プレビュー、未設定の公開APIは503。
  - 画像種別、危険URL/任意HTMLの拒否、グラフ/表のレンダリング。
  - GitHub APIモックで、既存記事を保持した一覧追記、非公開案内への置換、許可パス、main更新時の再試行、未完了PR停止、マージ済み確認。
- `npm run build --prefix services/admin-center`: 成功。生成バンドルは約455KB。Tiptapは3.33.1へ固定。
- `npm audit --prefix services/admin-center`: 既知の脆弱性0件（開発依存も含む）。
- `node services/admin-center/test/browser.mjs`: Chromiumで成功。
  - 文章、見出し、リンク、表の挿入と行/列追加、棒グラフ、画像挿入。
  - 自動保存→再読込、通信障害時の未保存表示と再保存、保存後プレビュー、履歴復元。
  - 出典付き大学DB修正提案、PC1440px/スマートフォン390pxの表示と横はみ出しなし。
  - トップ右上「管理」1個、既存公開メニュー11リンク、モバイルメニュー開閉。
  - 既存Jotform Inboxリンク、写真補正画面の継続表示。未接続のログインボタンは非表示。
- 既存 `.github/workflows/admin-center-guard.yml` のPythonチェック: 成功。
- 既存 `.github/workflows/university-photo-review-editor-guard.yml` のPythonチェック: 成功。
- 基準コミットに対し `columns/`、`data/`、`tools/university-database/`、`assets/images/` の差分0。
- トップの `#global-menu` は基準コミットと同一。
- `git diff --check`: 成功。

## 目視確認と自己レビュー

PC/スマートフォンのエディター、プレビュー、トップ管理入口、管理ハブのスクリーンショットを確認。選択中のグラフに画像を挿入すると置換される問題を修正し、両方が保存・再読込・プレビューで残ることを再検証。既存CSSがhiddenを上書きしていたため、未接続ログインボタンを確実に非表示にするルールと回帰チェックを追加した。依存監査で検出された旧Tiptapの脆弱性は修正版への更新後に再監査した。

ブラウザー画像はCIの `admin-center-screenshots` artifactとして取得できる。ローカル実行時は `/tmp/bantai-admin-screenshots`、`SCREENSHOT_DIR` 指定で任意のリポジトリ外ディレクトリに保存できる。

## 未検証・残作業

- 外部管理サーバーの配備・TLS・永続ボリューム・バックアップ・秘密設定。本番接続はdisabled。
- 本物のGitHub書込みを伴うアプリ内公開→人間レビュー→マージ→Pages配信。自動テストはモックを使用し、テスト記事を公開リポジトリへ送っていない。
- 既存コラムの独自HTMLの移行・既存記事そのものの編集/非公開化。
- 大学DB修正提案を公開DBへ適用する既存生成処理との自動統合。今回は提案保存・PR化まで。
- Jotform認証と新サーバー認証のSSO化、多人数向けアカウント/MFA。

これらを実装済み/本番検証済みとは扱わない。初期導入PRのレビュー後、運用手順に従って管理サーバーを設定し、接続設定を別PRで有効化する。
