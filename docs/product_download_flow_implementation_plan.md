# 商品ページ 販売導線 実装計画書

- 作成日: 2026-07-14
- 前提文書: [統一方針](product_download_flow_policy.md) / [現状調査報告書](product_download_flow_audit.md)
- 進め方: 段階ごとに完了確認してから次へ進む。各段階は独立してコミットし、途中で止めても本番が壊れない状態を保つ。

## 第1段階: 試用版ZIPの置き場所を確定

- 方針5・6に基づき、製品ごとに /downloads/ 直置きか GitHub Releases 併用かを決める。
- 対象製品と現在の試用版の所在:
  - Ban.Tai はじめての五線紙メーカー（BOOTH 0円バリエーション）
  - 漢字練習帳（BOOTH内体験版）
  - 方眼紙メーカー（BOOTH内体験版・本体）
  - 絵日記・観察カード作成メーカー（BOOTH内10日試用）
  - 小学校教育計画作成・運営システム モニター版（BOOTH、約60〜130MBの3構成 → 大容量のためGitHub Releases併用の第一候補）
### 第1段階の決定事項（2026-07-14 確定）

- 試用版ZIPは原則 `/downloads/trials/` 配下に配置する。
- 無料ツールZIPは `/downloads/free-tools/` 配下とする。ただし現行リンクの維持が必要な場合（外部サイト・note記事等からの直リンク）は互換性を考慮して整理する。
- 大容量・履歴管理が必要なものは GitHub Releases を併用できる（教育計画モニター版が第一候補）。
- 利用者向け表示は、どの場合も「公式HPの商品ページからダウンロード」で統一する。
- `/downloads/` 直下の旧版ZIPやプレースホルダーは、参照リンクがなければ削除対象とする。
- 旧版 BanTai_BannerStudioV2_Final.zip は削除対象とする（下記の参照確認結果に基づく）。
- プレースホルダーtxt（ここに_BanTai_BannerStudioV2_Final.zip_を入れてください.txt）は削除対象とする。
- 実際の削除は本追記とは別のコミットで行い、削除時に README.md と data/product-details/banner-studio.json の旧版参照もあわせて更新する。

### 残存物2件の参照確認結果（2026-07-14 実施）

リポジトリ全体（HTML・JSON・JS・Markdown等）を対象に検索した。

- 旧版 BanTai_BannerStudioV2_Final.zip への参照:
  - 利用者向けページ（index.html、products/ 配下のHTML、data/products.json）には参照なし。現行 v3.0.0 ZIPへの参照のみ存在（index.html、products/index.html、products/banner-studio/index.html、data/products.json の4系統）。
  - 参照が残るのは次の3箇所のみで、いずれも利用者導線ではない。
    1. README.md（66・73・74・113行目。旧Dropbox URLと「バックアップとして保持」の記述）
    2. data/product-details/banner-studio.json（42行目。実ページと乖離した未使用の生成用データ）
    3. プレースホルダーtxt自身の本文
  - 結論: 現行版への参照が別に存在し、旧版への利用者向け参照はないため、削除対象の条件を満たす。
- プレースホルダーtxtへの参照: リポジトリ内のどのファイルからも参照されていない。削除対象の条件を満たす。

## 第2段階: data/products.json に trial_download_url 等を追加

- 各製品に試用版DL先フィールド（trial_download_url）を追加する。第1段階で確定したURLを設定する。
- 試用版がない製品（証明写真メーカー等）と無料ツールは null のままとする。
- 休止中の楽譜・五線紙作成メーカーに残る hasTrial:true と旧BOOTH URLをこの機会に整理する。
- この段階では JSON のみ変更し、生成は第4段階まで行わない。

## 第3段階: build_products.py の render_actions() を改修

- ボタン生成順を方針4の「試用版DL → BOOTH購入 → Vector掲載 → note → 分野を見る → 詳細を見る」に変更する。
- trial_download_url があれば先頭に「試用版を無料ダウンロード」ボタンを出力する。
- 無料ツールの「無料でダウンロードする」ボタンは現行どおり先頭を維持する。
- tools/check_products.py での検証も更新が必要か確認する。

## 第4段階: 商品一覧ページを再生成

- tools/build_products.py を実行し、products/index.html と index.html の統計プレースホルダーを再生成する。
- git diff で生成結果を確認してからコミットする（生成物の手編集はしない）。
- トップページ index.html の手書きCTA（製品セクション8箇所）も同じボタン順に手動修正する。

## 第5段階: 主力商品ページから順に詳細ページを修正

- 修正順序（主力・売上導線の太い順）:
  1. 小学校教育計画作成・運営システム（モニター版DL直リンク化、同一URL3ボタンの整理）
  2. Ban.Tai はじめての五線紙メーカー（試用版直DL化。本文Step1と実装の矛盾解消）
  3. 漢字練習帳（ヒーローのボタン順逆転の修正）
  4. 方眼紙メーカー（試用版直DLボタン追加）
  5. 絵日記・観察カード作成メーカー（試用版直DLボタン追加、Vector URL確定時にリンク追加）
  6. 証明写真メーカー（id="vector" 残骸の修正、重複セクション統合）
- 詳細ページは手書きHTML管理のため直接編集する（data/product-details/ のJSONは実態と乖離しているので使わない）。

## 第6段階: 古い矛盾文言を削除

- 現状調査報告書 第5節の11件を対象に、方針と矛盾する文言を削除・書き換える。主なもの:
  - 方眼紙メーカー「公式HPからZIPやEXEへの直接リンクは掲載していません」
  - 証明写真メーカー「公式ホームページから直接ZIPやEXEは配布しません」
  - はじめての五線紙メーカーの Gumroad 言及
  - 絵日記・観察カード「GitHubは一般利用者向けの直接配布先にはしません」（方針6・7に合わせて表現を修正）
  - バナースタジオの制作メモ調の一文
- 第5段階のページ修正と同時に行ってよいが、漏れ確認はこの段階でまとめて行う。

## 第7段階: GA4で試用版DLクリックを計測

- 試用版DLボタンに計測用の識別（クラスまたは data 属性）を付与し、GA4のイベントとしてクリックを計測する。
- 既存の assets/js/analytics-events.js と docs/admin/ga4-implementation-plan.md の設計に合わせて実装する。
- 計測開始後、「試用版DL → BOOTH購入」の転換を見られる状態をゴールとする。

## 各段階共通の注意

- コミットは段階ごとに分け、コミットメッセージで段階番号が分かるようにする。
- products.json を編集したら必ず build_products.py を実行し、products/index.html を手で編集しない。
- 着手前に index.html が正常な全体構造（header / nav / main / footer）を保っているか確認する（2026-07-11のトップページ破損の再発防止）。
