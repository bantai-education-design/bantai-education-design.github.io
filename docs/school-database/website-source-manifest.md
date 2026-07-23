# 公式学校ホームページ 確認元マニフェスト (website-source-manifest.md)

## 概要
本ドキュメントは、Ban.Tai 全国学校データベースにおける公式学校ホームページURLの**確認元優先ルール、取得基準、照合フロー、および検証状況**を定義・記録する技術仕様書です。

---

## 1. 教育委員会・私学協会管理URLの優先利用ルール

各校の公式ホームページURLを確認する際は、個別の一般Web検索を行わず、**教育委員会および都道府県私学協会の公式一覧**を最優先の一次確認元として使用します。

### URL取得の優先順位
```text
1. 都道府県教育委員会の公式学校一覧 (最優先)
2. 都道府県私立中高協会・学事課の公式会員校一覧
3. 市区町村教育委員会の公式学校一覧
4. 学校公式ホームページ (単独ドメイン)
```

---

## 2. 収録実績（公式一覧直接取得分）

| 都道府県 | 校種 | 設置区分 | 確認元の公式一覧 | 確認元URL | 確認日 | 取得件数 | 未確認件数 | 備考 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **埼玉県** | 高等学校 | 公立 | 埼玉県教育委員会「公立高校のホームページ」 | `https://www.pref.saitama.lg.jp/e2201/school01.html` | 2026-07-23 | **131 件** | **1,801 件** | `*.spec.ed.jp` 等の埼玉県教育委員会公式ドメインを直接取得・HTTP 200確認済み |
| **東京都** | 都立・私立 | 都立・私立 | 東京私立中学高等学校協会「会員校一覧」 / 東京都教育委員会 | `https://www.tokyoshigaku.com/schools/` | 2026-07-23 | **465 件** | **3044 件** | 公式会員校ディレクトリより学校単体ページを直接取得・検証済み |

- **ステータス**: **Phase B 進行中**
- **確認済み合計**: **596 件** (埼玉県 131件 + 東京都 465件)

---

## 3. 自動検証スクリプト
- スクリプトパス: [validate_school_websites.py](file:///C:/Users/User/Documents/bantai-education-design.github.io/tools/school-database/validate_school_websites.py)
- 結果データ: [website-verification-report.json](file:///C:/Users/User/Documents/bantai-education-design.github.io/tools/school-database/website-verification-report.json)
