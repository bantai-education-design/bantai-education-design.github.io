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
- `data/universities_tokyo_all.generated.json` → `tools/university-database/tokyo/data/universities_tokyo_all.generated.json`
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
