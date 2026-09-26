# 教育計画システム 無料モニター版配布 実装計画

更新日: 2026-09-25

## 1. 基本方針
- 無料モニター版は **公式HPから直接ダウンロード** と **Vectorからダウンロード** の2経路で配布する。
- BOOTHは製品版専用とする。
- 公式HP版とVector版は同一ZIPを使用し、SHA-256まで一致させる。
- 大容量ZIPは公式HPリポジトリ本体へコミットせず、GitHub Releasesのassetとして配布する。
- 統合版の無料モニター専用大容量ZIPは作らない。教務支援システムと週案システムの2本を組み合わせて統合版として試用する。
- ページ見出しには固定バージョン番号を入れず、「無料モニター版ダウンロード」を恒久見出しとする。
- 通常版系モニター期限: 2027-03-31。
- 調整授業時数対応版モニター期限: 2027-08-31。

## 2. 配布対象
### 通常版系
1. 教務支援システム モニター版
2. 週案システム モニター版
3. 統合版モニター案内（教務支援＋週案の2本構成）

### 調整授業時数対応版
4. 調整授業時数対応版 モニター版

### 製品版
- 教務支援: BOOTH https://bantai3.booth.pm/items/8893534
- 週案: BOOTH https://bantai3.booth.pm/items/8893762
- 統合版: BOOTH https://bantai3.booth.pm/items/8893790
- 調整授業時数対応版: BOOTH公開準備後に正式URLを設定する。

### Vector
- 教務支援: https://www.vector.co.jp/soft/winnt/edu/se528971.html
- 週案: https://www.vector.co.jp/soft/winnt/edu/se528974.html
- 調整授業時数対応版: https://www.vector.co.jp/soft/winnt/edu/se529717.html（公開申請中: SE529717）

## 3. GitHub Releases運用
- ZIPはGitHub Releases assetsとして配布する。
- 1リリースごとに以下を添付する。
  - 教務支援モニターZIP
  - 週案モニターZIP
  - 調整授業時数対応版モニターZIP
  - 共通導入マニュアルPDF
  - 統合版利用ガイドPDF
  - 調整授業時数対応版マニュアルPDF
  - SHA256SUMS.txt
- ファイル名は英数字中心で管理し、公式HP上の表示名は日本語にする。
- 公式HPとVectorで配布するZIPは同一ファイルを使用する。

## 4. 公式HPページ構成
### /products/education-planning/
- 製品概要
- 無料モニター版への導線
- BOOTH製品版への導線
- 統合版の2本構成説明

### /products/education-planning/monitor-download/
新設。以下を掲載する。
- 教務支援システム: 公式HP / Vector / BOOTH / マニュアル / バージョン / 更新日 / SHA-256
- 週案システム: 同上
- 統合版: 教務支援ZIPと週案ZIPの2本構成、公式HP2ボタン、Vector2ボタン、BOOTH統合版、統合版利用ガイド
- 調整授業時数対応版: 公式HP / Vector（SE529717 公開申請中） / BOOTH（URL確定後） / 専用マニュアル / バージョン / 更新日 / SHA-256

### 調整授業時数対応版ページ
候補URL: /products/education-planning/adjusted/
- タイトル画像
- 制度対応の説明
- できること
- 無料モニター版DL
- マニュアル
- FAQ
- 今後の更新・製品版への導線

## 5. 共通表示仕様
- 「無料モニター版 = 公式HP / Vector」
- 「製品版 = BOOTH」
- 初回シリアル認証時のみインターネット接続が必要。
- 認証後の通常利用はオフライン可能。
- 業務データはPC内保存。
- 製品版は購入者本人のWindows PC 2台まで。
- 「完全オフライン」とは表現しない。
- モニター版と製品版の違いを明示する。

## 6. マニュアル構成
### 共通導入マニュアル
- ダウンロード
- ZIP解凍
- 起動
- 初回認証
- 基本操作
- よくある質問
- トラブル対処
- 問い合わせ

### 統合版利用ガイド
- 教務支援と週案の2本構成
- 連携方法
- データ受け渡し
- 注意事項

### 調整授業時数対応版マニュアル
- 制度対応版の位置づけ
- 計画作成
- 削減・充当
- 年間計画連携
- 週案連携
- 時数確認
- 未解決端数・超過等の表示
- FAQ

## 7. 今後につなげる導線
- モニター利用後の感想・改善要望は公式お問い合わせ窓口へ集約する。
- 改善内容とバージョンアップ情報を公式HPで継続告知する。
- 製品版への導線を各モニターカードの近くに配置する。
- FAQを更新し、問い合わせ負担を軽減する。
- GA4で以下を計測する。
  - 公式HPモニターDL
  - Vector遷移
  - BOOTH遷移
  - マニュアルDL

## 8. 公式HP画像計画
公式HP内で使用する画像のみを制作する。
1. 教務支援システム タイトル画像
2. 週案システム タイトル画像
3. 統合版の利用方法画像
4. 調整授業時数対応版 タイトル画像
5. 無料モニター版ダウンロード方法画像
6. モニター版と製品版のご案内画像

デザイン共通:
- 黒・金・白
- 学校実務向けの安心感
- 文字は少なく読みやすく
- 「無料モニター」と「製品版」を混同させない
- 公式HPのレスポンシブ表示で使いやすい横長比率を基本とする

## 9. 実装順序
### Phase 1: 配布物確定
1. 教務支援・週案・調整授業時数対応版の最新モニターZIPを確定。
2. 同梱内容を監査。
3. マニュアルPDFを確定。
4. SHA-256を算出。

### Phase 2: GitHub Releases
5. Release作成。
6. ZIP・PDF・SHA256SUMS.txtを添付。
7. 直リンクを記録。

### Phase 3: 公式HP
8. monitor-downloadページ新設。
9. 既存education-planningページから導線追加。
10. 調整授業時数対応版ページを追加。
11. 画像6点を配置。
12. GA4計測を追加。

### Phase 4: Vector
13. 教務支援・週案の旧説明を現行方式へ更新。
14. 調整授業時数対応版を登録。
15. 公式HP版とVector版のZIP/SHA-256一致を確認。

### Phase 5: 検証
16. リンク切れ確認。
17. ZIPハッシュ一致確認。
18. Windows実機起動確認。
19. モバイル/PC表示確認。
20. 旧BOOTH無料版・旧Googleフォーム・旧固定ライセンスキー説明が利用者向けページに残っていないことを確認。

## 10. リリース条件
以下が揃うまで本番公開しない。
- 最新ZIP確定
- SHA-256一致
- マニュアル完成
- GitHub Releases配置
- 公式HPリンク動作
- Vectorリンク動作
- 旧案内削除
- 実機起動確認
- 公式HP表示確認


## 11. Phase 1 監査結果（2026-09-25）

### 通常版系
- 配布準備ブランチ: `release/monitor-v5.70.12-prep`
- 配布元コミット: `136fb93f70f5557770d964a9f1b1731819a2fc79`
- GitHub Actions: `Build monitor distribution packages` 成功
- `npm run verify:all` 成功
- 教務支援モニターZIP:
  - file: `bantai_kyomu_support_monitor_v5.70.12.zip`
  - size: 170,827,361 bytes
  - SHA-256: `5f41a18af1c5b3c44773f3cc29e4420ea1c4d9a6e86d36dcdf82d254f7cee424`
- 週案モニターZIP:
  - file: `bantai_weekplan_monitor_v5.70.12.zip`
  - size: 170,690,105 bytes
  - SHA-256: `73131ca44ecd99b13a20b01e6c80ec61d21951ce2e3d9882253766e2c7c28d73`
- 共通モニターマニュアルPDFも同一ワークフロー内で生成済み。
- モニター期限: 2027-03-31。
- モニター期間中はシリアル登録不要。
- 公式HP / Vector の2経路配布方針は README / マニュアルに反映済み。
- BOOTHは製品版専用。

### 調整授業時数対応版
- 配布準備ブランチ: `release/monitor-v1.0.6-prep`
- 配布元コミット: `15f660f7b0b8bb2bfc65132d23ad2d45c850cbcf`
- GitHub Actions: `Build adjusted monitor distribution package` 成功
- `npm run verify:all` 成功
- `npm run verify:installer` 成功
- 印刷・週案印刷・学校設定の検証成功
- 配布ZIP:
  - file: `bantai_adjusted_curriculum_monitor_v1.0.6.zip`
  - size: 170,900,449 bytes
  - SHA-256: `ddb6466ea032413e7fa17479e49ee730c57acd6fc433fb5634c496afaed4730b`
- 専用モニターマニュアルPDFも同一ワークフロー内で生成済み。
- モニター期限: 2027-08-31。
- モニター期間中はシリアル登録不要。
- 公式HP / Vector の2経路配布方針は README / マニュアルに反映済み。
- **未完了ゲート:** `npm run verify:setup` は Stable/Adjusted の実インストール共存検証のため、実Windows環境でのローカル確認が必須。GitHub Actions上では代替しない。

### 配布先に関する重要事項
- `bantai-kyomu-support-system` と `bantai-adjusted-curriculum-system` は private リポジトリのため、そこに作成した Release asset を一般利用者向け直リンクには使用しない。
- 一般公開用の大容量ZIPは、public の `bantai-education-design.github.io` リポジトリの GitHub Releases asset として配置する。
- ZIPをGit履歴には入れない。
- 公式HPの直DLボタンは public Release asset のURLへ接続する。

### Phase 1 判定
- 教務支援: 配布物確定候補
- 週案: 配布物確定候補
- 調整授業時数対応版: `verify:setup` 完了後に配布物確定
- Phase 2（public GitHub Release作成）は、上記最終ゲート確認後に実施する。


## 12. 通常版系 再ビルド確定（2026-09-25）

Vector用READMEを「公式HP / Vectorの2経路配布」へ修正したため、通常版系を再ビルドした。

- 最終コミット: `d3f8005fb7f5dc9ffd7f60495f24c8540b2bbdad`
- GitHub Actions run: `36072715441`
- 結果: SUCCESS

### 教務支援
- file: `bantai_kyomu_support_monitor_v5.70.12.zip`
- bytes: 170,827,341
- SHA-256: `48b39454252b68f15ac1c36cdb7f2d22c5d75277d4c3272c4f09f5ebb94f1315`

### 週案
- file: `bantai_weekplan_monitor_v5.70.12.zip`
- bytes: 170,690,132
- SHA-256: `40dd1486d8bf233d378cda883ec4248875ba661fae713c5fa3e0996b5f36d0a2`

上記2本を通常版系の公式HP公開候補として固定する。
旧ハッシュ値は公開用に使用しない。

## 13. 公開用Release配置の実装上の制約

現在のGitHub接続ではRelease assetへのバイナリ直接アップロード操作を実行できない。
そのため、公式HP側のページと文言は先行してDraft実装し、GitHub Releases assetがpublicリポジトリへ配置されるまでは「公式HPから直接ダウンロード」ボタンを準備中表示とする。

公開用Releaseにassetを配置後、以下を満たした時点でボタンを有効化する。

1. public Release URLが取得できる。
2. Release assetのファイル名が確定している。
3. Release assetを再ダウンロードしてSHA-256を照合する。
4. 公式HP掲載ハッシュと一致する。
5. 実Windows環境で起動確認する。
