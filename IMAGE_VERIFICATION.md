# 画像資料の検証メモ

- staff-infographic: Gemini_Generated_Image_j2y8voj2y8voj2y8.png / (2048, 1117) / PNG
- id-photo-steps: 1774710117-b8pZP4cTXq6zBDMUREydoOJr.webp / (807, 440) / WEBP
- id-photo-okng: 1774710145-pIMUHNGrd2BOoL8hkQSznftW.webp / (816, 439) / WEBP
- id-photo-roadmap: 証明写真.webp / (810, 448) / WEBP
- staff-icon-source: スクリーンショット 2026-04-27 135649.png / (406, 407) / PNG
- staff-splash-source: スクリーンショット 2026-04-29 191255.png / (789, 625) / PNG
- staff-hero: ChatGPT Image 2026年5月3日 21_13_41.png / (1536, 1024) / PNG
- text-tool-features-blue: 特色.png / (1200, 630) / PNG
- text-tool-features-light: 特色2.png / (1152, 619) / PNG
- text-tool-overview: 特色3.png / (2048, 1143) / PNG
- staff-usecases: unnamed (1).png / (2048, 1143) / PNG
- staff-clefs: スクリーンショット 2026-05-03 143519.png / (936, 638) / PNG
- staff-settings: スクリーンショット 2026-05-03 143613.png / (948, 580) / PNG
- staff-icon-ico: icon.ico / (256, 256) / ICO

使用方針:
- 五線紙作成メーカー資料は `products/staff-paper/` に使用。
- 画像文字入れくん資料は `products/text-overlay/` に使用。
- 証明写真メーカー資料は `products/id-photo/` に使用。
- 教育計画システムの主力商品ページとは混在させない。

## 教科書・年間学習計画ガイド カード背景画像

確認日: 2026-08-09

生成元:
- Codex built-in image generation で生成した新規画像。
- 外部写真、素材サイト、既存人物写真、第三者ロゴ、第三者著作物は入力していない。
- 画像内の人物は架空人物として生成。実在人物の写真や本人確認可能な素材は使用していない。
- 生成後、Pillowで 1600x900 に調整し、WebP形式へ変換した。

利用条件:
- Ban.Tai Education Design公式HPの `resources/textbook-plans/` 学年ガイド・入口カード背景として使用する。
- 画像内に意図的な文字、ロゴ、ブランド名、学校名、出版社名は入れていない。
- 画像はカード背景としてCSSオーバーレイを重ね、白文字の最小コントラスト 4.5:1 以上を満たすことを確認した。

| 用途 | ファイル | 寸法 | 容量 | SHA256先頭12桁 | 白文字最小CR |
| --- | --- | ---: | ---: | --- | ---: |
| 1年生 | `assets/images/textbook-guides/grade-1-classroom-desk.webp` | 1600x900 | 57,020 bytes | `2f6d73072de2` | 4.88:1 |
| 2年生 | `assets/images/textbook-guides/grade-2-textbook-notebook.webp` | 1600x900 | 52,690 bytes | `fae15693a887` | 5.15:1 |
| 3年生 | `assets/images/textbook-guides/grade-3-classroom-board.webp` | 1600x900 | 56,338 bytes | `37b4f3350c2d` | 4.98:1 |
| 4年生 | `assets/images/textbook-guides/grade-4-map-study.webp` | 1600x900 | 67,082 bytes | `1540a0a3318f` | 4.94:1 |
| 5年生 | `assets/images/textbook-guides/grade-5-tablet-study.webp` | 1600x900 | 55,380 bytes | `d186893d8544` | 4.73:1 |
| 6年生 | `assets/images/textbook-guides/grade-6-globe-window.webp` | 1600x900 | 64,320 bytes | `6873a33eb5b4` | 5.07:1 |
| 先生 | `assets/images/textbook-guides/audience-teacher-desk.webp` | 1600x900 | 58,036 bytes | `a058089d92d6` | 5.31:1 |
| 保護者 | `assets/images/textbook-guides/audience-parent-desk.webp` | 1600x900 | 66,558 bytes | `54633bd7cbbf` | 5.12:1 |
| 教科書会社 | `assets/images/textbook-guides/audience-publisher-bookshelf.webp` | 1600x900 | 75,544 bytes | `030bd24209b5` | 5.11:1 |

CSS確認:
- `assets/style.css` のカード背景参照は上記WebPへ更新済み。
- 旧JPEG 9枚はPR差分から削除済み。
- オーバーレイ最終値は `0.84 / 0.58 / 0.68`。
- 700〜1023pxでは学年カード・3入口カードを2列表示、699px以下では1列表示。
