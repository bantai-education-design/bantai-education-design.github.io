# 試用版ZIP 配置対象 棚卸し結果（第2段階A）

- 調査日: 2026-07-14
- 調査範囲: ローカルPC（Desktop / Documents / Downloads 配下）のZIPファイル
- 前提文書: [実装計画書](product_download_flow_implementation_plan.md) 第1段階決定事項
- 本調査ではZIPのコピー・/downloads/trials/ の作成・HTML等の修正は行っていない。

## サイズ制限の前提

- GitHubリポジトリは1ファイル100MBを超えるとpushが拒否されるため、100MB超のZIPは /downloads/trials/ に置けない（GitHub Releases必須）。
- 100MB未満でも、数十MBのバイナリをリポジトリに入れるとclone・履歴が重くなる。50MBを超えるものはReleases併用を推奨とする（最終判断は製品ごと）。
- GitHub Releases はアセット1件2GBまで対応。

## 棚卸し一覧

| 製品 | 現在のHP掲載版 | ローカル実体（試用版に相当するZIP） | 保管場所 | サイズ | 公式HP用ファイル名案 | /downloads/trials/ 配置可否 | 推奨 |
|---|---|---|---|---|---|---|---|
| はじめての五線紙メーカー | v2.0.0 | はじめての五線紙メーカー_v2.0.0_BOOTH.zip（ほかGumroad_Trial版・Vector版も同サイズで存在） | Documents\アプリ\03_配布物・ZIP・EXE\ | 88.3MB | bantai_first_staff_paper_trial_v2.0.0.zip | 可（ただし100MBに近い） | GitHub Releases 併用を推奨（サイズと今後の版更新頻度を考慮） |
| 漢字練習帳 | 版表記なし（BOOTH販売中） | kanji-practice-sheet-1.0.0-windows.zip（同内容らしき kanji-sheet-100-win.zip も同日・同サイズで存在） | Documents\アプリ\漢字練習帳\ | 163.6MB | bantai_kanji_practice_trial_v1.0.0.zip | 不可（100MB超） | GitHub Releases 必須 |
| 方眼紙メーカー | v3.1.2 | 方眼紙メーカー-v3.1.2-体験版.zip（体験版ビルドが明確に分離されている） | Documents\アプリ\方眼紙メーカー\release\ | 73.8MB | bantai_graph_paper_trial_v3.1.2.zip | 可 | /downloads/trials/ 直置きで可（Releases併用も選択可） |
| 絵日記・観察カード作成メーカー | v1.2.0 | 絵日記・観察カード作成メーカー-v1.2.0-Vector-Trial-Windows.zip（試用版ビルド。BOOTH版・Vector版も同サイズで存在） | Documents\アプリ\観察カード\04_Release\ | 76.9MB | bantai_observation_card_trial_v1.2.0.zip | 可 | /downloads/trials/ 直置きで可（Releases併用も選択可） |
| 小学校教育計画作成・運営システム モニター版 | Ver.5.70.7 | 下記「教育計画システムの補足」参照（候補複数） | Documents\アプリ\ ほか | 277〜833MB | bantai_education_planning_monitor_v5.70.x.zip（版確定後に決定） | 不可（100MB超） | GitHub Releases 必須。かつ配布する版と構成の確定が先 |

## 教育計画システムの補足（版・構成の確定が必要）

ローカルには複数世代・複数構成のZIPが混在しており、どれを公式HP導線の正とするかの確定が必要。

- Ver.5.70.7 BOOTHモニター版系（HP記載の版と一致）:
  - 小学校教育計画作成・運営システム_Ver5.70.7_BOOTHモニター版.zip（832.7MB、2026-06-26）
  - 同 _15分見学.zip（420.4MB、2026-06-26 22:52 — 15分見学対応の最終と思われる）
  - 同 _15分見学対応.zip および _FIX2〜_FIX4（各341.5MB、2026-06-26 — 中間ビルドの残存と思われる）
- Ver.5.70.8 Vector登録用 Trial系（HPの記載より新しい版）:
  - BanTai_Kyomu_v5.70.8_Vector_Trial.zip（277.7MB）／SetupOnly（82.1MB）
  - BanTai_Shuan_v5.70.8_Vector_Trial.zip（277.5MB）／SetupOnly（82.1MB）
  - BanTai_Togo_v5.70.8_Vector_Trial.zip（555.2MB）／SetupOnly（164.2MB）
  - 場所: Documents\vector販売\rebuilt_zips_20260703_v5.70.8_vector_hash\
- 確定すべきこと:
  1. 公式HPから案内する版を 5.70.7（BOOTHモニター版・15分見学対応）とするか、5.70.8 系に更新するか。
  2. HP商品ページの「約130MB／約60MB／約70MB」という3構成の記載は、実在ZIPのサイズ（277〜833MB、SetupOnlyでも82MB）と一致しておらず、ページ記載の見直しが必要。
  3. 配布構成（統合版／教務単体／週案単体、フルZIPかSetupOnlyか）。

## BOOTH内だけに置かれていてローカルに実体がないもの

- 該当なし。5製品すべてにローカル実体が存在する。
- ただし漢字練習帳は「体験版」と分離されたビルドがなく、BOOTH配布と同一のZIP（試用開始はアプリ側の10日制限による方式）と思われる。公式HP配布用にファイル名を変えるだけでよいか、ビルド内容（同梱の案内文書がBOOTH前提になっていないか）の確認を推奨。
- 同様に、はじめての五線紙メーカーは BOOTH版／Gumroad_Trial版／Vector版の3ビルドが同サイズで存在する。公式HP用にはどれを元にするか（同梱のライセンス申請案内PDFがチャネル固有でないか）の確認を推奨。

## 安全上の注意（配置作業時）

- Documents\アプリ\99_Archive_危険_キー同梱ZIP_使用禁止\ 配下および「使用禁止_キー同梱」の名を持つZIPは、ライセンスキー同梱の旧ビルドであり、いかなる経路でも公開しないこと。
- 配置作業では上記アーカイブフォルダに触れず、本棚卸しで特定したファイルのみを使用する。

## 次の作業（第2段階B以降の想定）

1. 教育計画システムの版・構成の確定（利用者判断）。
2. はじめての五線紙メーカー・漢字練習帳の同梱文書のチャネル依存確認。
3. 確定したZIPを新ファイル名で /downloads/trials/ または GitHub Releases に配置。
4. data/products.json に trial_download_url を追加（第2段階B）。
