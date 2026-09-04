# 東京都大学データベース 公開移植メモ

## 方針

非公開リポジトリ `bantai-education-design/daigaku_DB` の東京都144大学版を、公開中の公式HP `bantai-education-design.github.io` の `/tools/university-database/tokyo/` に移植する。

## 公開対象

- `tokyo.html` → `tools/university-database/tokyo/index.html`
- `assets/prototype.css` → `tools/university-database/tokyo/assets/prototype.css`
- `assets/tokyo.css` → `tools/university-database/tokyo/assets/tokyo.css`
- `assets/tokyo-v2.css` → `tools/university-database/tokyo/assets/tokyo-v2.css`
- `assets/tokyo.js` → `tools/university-database/tokyo/assets/tokyo.js`
- `assets/bantai-logo.svg` → `tools/university-database/tokyo/assets/bantai-logo.svg`
- `assets/tokyo-hero-students.svg` → `tools/university-database/tokyo/assets/tokyo-hero-students.svg`
- `data/universities_tokyo_all.generated.json` → 公開側の144校ID基礎一覧（氏名等の最小項目）
- `data/public_export/tokyo_core_01.json` ～ `tokyo_core_12.json` → 公開側の同名ファイル（学生数・所在地・特色・公式根拠等）
- `data/faculties_tokyo_all.generated.json` → `tools/university-database/tokyo/data/faculties_tokyo_all.generated.json`
- `data/departments_tokyo_all.generated.json` → `tools/university-database/tokyo/data/departments_tokyo_all.generated.json`
- `data/graduate_schools_tokyo_all.generated.json` → `tools/university-database/tokyo/data/graduate_schools_tokyo_all.generated.json`
- `data/tokyo_dataset_summary.generated.json` → `tools/university-database/tokyo/data/tokyo_dataset_summary.generated.json`

## 公開条件

1. 144大学が読み込めること。
2. 大学名・学部・学科・分野・地域検索が動くこと。
3. 国立・公立・私立、募集状況、並び替えが動くこと。
4. Google Mapsへの大学別リンクが動くこと。
5. 2〜4大学比較が動くこと。
6. 公式入試情報リンクを維持すること。
7. 公平な掲載方針とデータ品質表示を維持すること。
8. 1366 / 1024 / 768 / 375 / 320pxで横スクロールや欠落がないこと。
9. `/databases/` から東京都版へ到達できること。
10. 上記を満たすまでPR #124はDraftのままとし、`main` へマージしないこと。

## データの扱い

公開ページには、表示に必要な生成済みJSONだけを置く。調査用ソース、監査用中間ファイル、生成スクリプト等は非公開の `daigaku_DB` に残す。


## データの役割と同期契約（2026-09-04更新）

| 区分 | 所在 | 用途 |
|---|---|---|
| 正本 | `daigaku_DB/data/universities_tokyo_all.generated.json` | 東京都144校の統合済み事実データ |
| 公開用生成物 | `daigaku_DB/data/public_export/` | 正本から公開可能項目だけを生成した成果物 |
| 公開コピー | `tools/university-database/tokyo/data/` | GitHub Pagesが実際に読み込むファイル |
| 初期・試作 | `daigaku_DB/data/universities.json`、`prototype_universities.json` | 開発・GUI試作専用。本番入力には使用しない |

公開側の `universities_tokyo_all.generated.json` は144校のIDと名称を保持する基礎一覧です。詳細表示・検索・比較に必要な確認済み項目は `tokyo_core_01～12.json` をIDで合成します。基礎一覧だけで公開を完結させてはいけません。

### 同期手順

1. 正本側で大学データを生成・検証する。
2. 正本側の `scripts/generate_tokyo_public_export.py` で公開用生成物を作る。
3. 正本側manifestの元コミット、144件、各分割範囲を確認する。
4. 公開用コア・所在地・入試・教育組織データを専用ブランチへコピーする。
5. 公開側 `data/source-sync-manifest.json` を同じPRで更新する。
6. 公開コピーのID集合、学生数、所在地、公式URL、一次資料が144校分そろうことを確認する。
7. 1366 / 1024 / 768 / 375 / 320pxと検索・並べ替え・詳細・比較を確認する。
8. 人間の承認後にマージし、Pages反映後に本番を再確認する。

### 禁止事項

- 公開コピーだけを先に修正し、正本との差を放置しない。
- `data/public_export/` を手編集しない。
- 初期13校版・代表6校版を本番データとして使用しない。
- manifestを更新せずに公開データを差し替えない。
- 144校分のコアシャードが欠けた状態で部分表示を継続しない。
