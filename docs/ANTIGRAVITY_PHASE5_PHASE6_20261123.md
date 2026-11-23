# Ban.Tai Phase 5 & Phase 6 Operations Guide (Scheduled Audit + Google Drive Safe Sync)

## 工程5：定期実行の拡充（二重監視構成）

公開リポジトリの品質・SEO・GA4・DB整合性・安全ガードを継続監視するため、クラウドとローカルの二層で定期点検を構成します。

1. GitHub Actions クラウド定期点検（`.github/workflows/weekly-site-health-audit.yml`）
   - 実行時刻: 毎週月曜 朝8:00 JST（日曜 23:00 UTC）および手動実行（`workflow_dispatch`）
   - 権限: `contents: read` のみ（完全読み取り専用・自動変更なし）
   - 点検スクリプト: `scripts/weekly_health_audit.py`
     - `sitemap.xml` のXML構文および重複 `<loc>` 検査
     - 全国学校DB 47都道府県JSON・`data/columns.json`・`data/products.json`・大学音楽コンクールJSON の構文整合検査
     - `tools/school-database/test_seo_metadata.py`（SEOメタデータ検証）
     - `scripts/check_ga_tracking.py`（GA4タグ欠落検査）
     - `tools/check_products.py`・`tools/check_product_detail.py`（製品カタログ・詳細ページ検証）
     - `scripts/test_bantai_*.py`・`scripts/test_long_running_harness.py`（安全ガード・Subagents・ハーネス回帰テスト）
2. Antigravity ローカル定期スケジュール（`/schedule`）
   - 毎週月曜 朝8:00 JST に `main` 同期状況・オープンPR・CI結果を含めてチャット通知します。

## 工程6：Google Drive正本とGitHub制作物の安全連携

Antigravityの `gdrive` プラグイン（接続済みアカウント確認済み）を用い、Google Drive上の原稿・書籍素材・一覧表（正本）とGitHubリポジトリを安全に連携します。

- 専用スキル: `.agents/skills/bantai-gdrive-sync/SKILL.md`
- 基本原則:
  - 既定は `gdrive readonly` のみ使用し、Drive上の正本を削除・上書き・共有変更しない。
  - 取得した一時ファイルは `.gitignore` 対象の `scratch/gdrive/` に隔離し、機密や中間ファイルをGitへ混入させない。
  - GitHub側への反映は必ず専用ブランチ＋検証＋DRAFT PRで行い、公開・マージは人間が最終承認する。
