# 公式学校ホームページ 確認元マニフェスト (website-source-manifest.md)

## 概要
本ドキュメントは、Ban.Tai 全国学校データベースにおいて各学校カードへ表示する「公式HP」ボタンのURL取得元、確認基準、および検証状況を記録・管理する仕様書です。

### 登録・公開の厳格ルール
1. **推測・自動検索の完全禁止**: 検索エンジンの結果無条件採用や外部口コミサイト（Wikipedia、民間学校情報サイト、SNS）からの収集は一切行いません。
2. **公式一覧直接取得**: 各都道府県教育委員会および自治体が公開する公式学校一覧から直接リンクされている正規URLのみを登録します。
3. **未確認校の非表示**: 確認できていない学校については JSON 内の `website` を空文字 (`""`) とし、UI上でもボタン自体を表示しません。

---

## Phase A 収録実績（公式一覧直接取得分）

| 都道府県 | 校種 | 設置区分 | 確認元の公式一覧 | 確認元URL | 確認日 | 取得件数 | 未確認件数 | リンク切れ件数 | 備考 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **埼玉県** | 高等学校 | 公立 | 埼玉県教育委員会「公立高校のホームページ」 | `https://www.pref.saitama.lg.jp/e2201/school01.html` | 2026-07-22 | 131件 | 5件 | 0件 | `*.spec.ed.jp` 等の埼玉県教育委員会公式ドメインを直接取得・HTTP 200確認済み |
| **埼玉県** | 特別支援学校 | 公立 | 埼玉県教育委員会 | `https://www.pref.saitama.lg.jp/e2201/school01.html` | 2026-07-22 | 0件 | 58件 | 0件 | 次回Phaseにて追加検証予定 |
| **東京都** | 都立高校 | 都立 | 東京都教育委員会 | `https://www.kyoiku.metro.tokyo.lg.jp/` | 2026-07-22 | 0件 | 193件 | 0件 | 次回Phaseにて追加検証予定 |
| **東京都** | 特別支援 | 都立 | 東京都教育委員会 | `https://www.kyoiku.metro.tokyo.lg.jp/` | 2026-07-22 | 0件 | 80件 | 0件 | 次回Phaseにて追加検証予定 |

---

## 自動検証スクリプト
- スクリプトパス: [validate_school_websites.py](file:///C:/Users/User/Documents/bantai-education-design.github.io/tools/school-database/validate_school_websites.py)
- 結果データ: [website-verification-report.json](file:///C:/Users/User/Documents/bantai-education-design.github.io/tools/school-database/website-verification-report.json)
