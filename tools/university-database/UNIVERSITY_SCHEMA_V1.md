# Ban.Tai 大学データベース 共通スキーマ v1.0

制定日: 2026-08-22  
対象: Ban.Tai Education Design 全国大学データベース  
機械検証: [`university.schema.json`](./university.schema.json)

## 1. 目的

この仕様は、大学1校あたりの「完成形」の情報項目を全国共通で定義する。東京都版で先行している大学名、設置区分、学生数、学部、学科、研究科、公式・入試リンク等を壊さず、次の7領域を同じ構造で追加できることを目的とする。

1. 学部 → 学科 → 専攻・コース
2. キャンパス・最寄駅
3. 学費
4. 入試方式・Web出願
5. 資格・進路
6. 研究・スポーツ・著名卒業生
7. 出典・最終確認日

このv1.0は「データ契約」であり、画面デザインを固定するものではない。公開ページ、比較画面、検索、将来の全国集約は同じデータを利用する。

## 2. 基本原則

- **大学名を識別子にしない。** `university_id` を永続IDとする。
- **年度で変わる情報には年度または基準日を必ず持たせる。** 学生数、学費、入試、就職率、国家試験実績等が対象。
- **事実データと紹介文を分離する。** 数値・名称・日付と、特色の要約を同じ意味で扱わない。
- **一次情報優先。** 大学公式、文部科学省等の公的資料、公式団体を第一順位とする。
- **出典なしの数値・実績・著名人は掲載しない。** `source_id` で出典へ接続する。
- **未調査と不存在を区別する。** 未調査は `null`、制度・該当項目が存在しないことを確認済みの場合は空配列 `[]` を使う。
- **偏差値はv1.0に含めない。** 将来必要な場合は、第三者提供データとして大学公式情報と別レイヤーで扱う。
- **公開データに調査用中間ファイルを混在させない。** 公開リポジトリは表示・検索・検証に必要な確定データを中心とする。

## 3. 最上位構造

```json
{
  "schema_version": "1.0",
  "university_id": "u000001",
  "name": "大学名",
  "establishment_type": "national",
  "status": "active",
  "official_url": "https://example.ac.jp/",
  "student_counts": {},
  "academics": [],
  "graduate_schools": [],
  "campuses": [],
  "tuition": [],
  "admissions": {},
  "qualifications": [],
  "careers": {},
  "research": {},
  "sports_culture": [],
  "notable_alumni": [],
  "sources": [],
  "verification": {}
}
```

## 4. A. 大学基本情報

| 項目 | キー | 型 | 方針 |
|---|---|---|---|
| スキーマ版 | `schema_version` | string | v1.0では `1.0` 固定 |
| 大学ID | `university_id` | string | `u` + 6桁。永続ID |
| 旧ID | `id` | string/null | 東京都版既存データとの移行互換用。新規処理は `university_id` を正とする |
| 正式名称 | `name` | string | 現行の正式名称 |
| ふりがな | `name_kana` | string/null | 検索・読み上げ用 |
| 英文名称 | `name_en` | string/null | 大学公式英語名 |
| 設置区分 | `establishment_type` | enum | `national / public / private` |
| 状態 | `status` | enum | `active / admissions_stopped / closed / planned` |
| 都道府県 | `prefecture` | string/null | 本部所在地等の代表地域。詳細住所はcampus側 |
| 市区町村 | `municipality` | string/null | 代表所在地 |
| 設置者 | `operator` | string/null | 国立大学法人、学校法人等 |
| 創立年 | `founded_year` | integer/null | 源流・創立 |
| 大学開学年 | `opened_year` | integer/null | 現在の大学としての開学 |
| 創立者 | `founder` | string/null | 公式確認できる場合 |
| 建学の精神・理念 | `philosophy` | string/null | 公式情報を要約 |
| 大学の使命・目的 | `mission` | string/null | 教育目的等 |
| 沿革 | `history_summary` | string/null | 重要事項を簡潔に要約 |
| 大学の特色 | `feature_summary` | string/null | 検索一覧や詳細ページの主紹介 |
| 大学公式 | `official_url` | URI | 公式トップ |
| 入試情報 | `admissions_url` | URI/null | 既存導線互換 |
| 募集要項 | `application_guidelines_url` | URI/null | 既存導線互換 |
| 資料請求 | `brochure_request_url` | URI/null | 既存導線互換 |
| オープンキャンパス | `open_campus_url` | URI/null | 既存導線互換 |
| 主な学問分野 | `academic_field_tags` | string[] | 検索・絞り込み用 |

### 学生数 `student_counts`

`undergraduate`、`graduate`、`other`、`total`、`as_of`、`source_id` を持つ。`as_of` は可能な限り「○年○月○日現在」をISO日付へ変換する。

## 5. ① 学部 → 学科 → 専攻・コース

### 学部 `academics[]`

- `faculty_id`: `f` + 6桁
- `name`
- `academic_field_tags[]`
- `campus_ids[]`
- `departments[]`
- `source_id`

### 学科 `departments[]`

- `department_id`: `d` + 6桁
- `name`
- `academic_field_tags[]`
- `programs[]`
- `source_id`

### 専攻・コース `programs[]`

- `program_id`: `p` + 6桁
- `name`
- `type`
- `academic_field_tags[]`
- `source_id`

`type` は次を共通値とする。

| 値 | 意味 |
|---|---|
| `major` | 専攻 |
| `course` | コース |
| `program` | プログラム |
| `specialization` | 専門・専門領域 |
| `track` | 履修トラック等 |

大学独自名称は `name` に原文のまま保持し、共通分類だけを `type` に入れる。

### 大学院 `graduate_schools[]`

研究科は学部とは別階層にし、`graduate_school_id`、名称、キャンパスID、`programs[]` を持つ。課程分類は `master / doctoral / professional / integrated / other` とする。

## 6. ② キャンパス・最寄駅

キャンパスは大学本体から独立させる。同一大学で学部ごとに所在地が異なるケースや、都道府県をまたぐケースを正しく表現するためである。

`campuses[]` の主項目:

- `campus_id`: `c` + 6桁
- `name`
- `postal_code`
- `prefecture`
- `municipality`
- `address`
- `latitude` / `longitude`
- `nearest_stations[]`
- `faculty_ids[]`
- `official_url`
- `source_id`

最寄駅 `nearest_stations[]` は駅名、路線、公式案内のアクセス表現、徒歩分数を保持する。徒歩分数は公式案内で確認できる場合を優先し、地図から独自推定した値を事実として登録しない。

## 7. ③ 学費

学費は `tuition[]` とし、**年度 + 学部/学科/プログラム**単位で複数レコードを保持できるようにする。

主項目:

- `academic_year`
- `faculty_id`
- `department_id`
- `program_id`
- `admission_fee`
- `annual_tuition`
- `facility_fee`
- `other_fees`
- `first_year_total`
- `currency`: v1.0では `JPY`
- `as_of`
- `source_id`

`first_year_total` は公式に総額が掲載されていればその値を優先する。独自計算する場合は、画面・生成処理側で「計算値」であることを区別し、元データの公式値と混同しない。4年間総額は公式明示がない限り共通項目にしない。

## 8. ④ 入試方式・Web出願

`admissions` は受験年度を必ず持つ。募集停止校等では `admission_year: null` を許容する。

- `admission_year`
- `web_application_url`
- `application_guidelines_url`
- `admissions_url`
- `methods[]`

`methods[]` の共通分類:

| `category` | 表示例 |
|---|---|
| `general` | 一般選抜 |
| `common_test` | 共通テスト利用 |
| `recommendation` | 学校推薦型選抜 |
| `comprehensive` | 総合型選抜 |
| `special` | 特別選抜 |
| `international` | 外国人留学生選抜等 |
| `transfer` | 編入学 |
| `other` | 上記に当てはまらない公式区分 |

各方式には `method_id`、対象学部・学科・プログラム、募集人数、出願期間、試験日、合格発表日、科目、共通テスト要否、公式URL、出典を持てる。

入試情報は年度更新が特に激しいため、**過年度情報であることを隠さない**。公開画面では受験年度を明示する。

## 9. ⑤ 資格・進路

### 資格 `qualifications[]`

資格種別:

- `national_license`: 国家資格
- `teaching_license`: 教員免許状
- `examination_eligibility`: 受験資格
- `certification`: 民間・公的認定等
- `other`

対象学部・学科・プログラムと取得条件を接続する。「卒業すれば自動取得」「所定科目履修で取得」「受験資格を得る」は混同しない。

### 進路 `careers`

- `employment_rate`
- `employment_rate_as_of`
- `graduate_school_rate`
- `main_employers[]`
- `main_career_fields[]`
- `national_exam_results[]`
- `source_ids[]`

国家試験実績は試験名、年度、受験者数、合格者数、合格率、出典を保持する。大学公表値と厚生労働省等の公的値が異なる場合は、定義の違いを確認して安易に混在させない。

## 10. ⑥ 研究・スポーツ・著名卒業生

### 研究 `research`

次の4群を持つ。

- `strengths[]`: 大学が公式に特色として示す研究分野
- `institutes[]`: 研究所・センター等
- `notable_projects[]`: 代表的研究プロジェクト
- `awards[]`: 研究上の受賞・顕著な実績

各項目は `title`、`summary`、`field_tags[]`、`source_id` を基本とする。Ban.Tai側で独自の「研究力順位」を付けない。

### スポーツ・文化 `sports_culture[]`

`category` は `sports / culture / music / arts / competition / other`。団体名、実績、年度、実績レベル、出典を保持する。

全国大会出場等は「現在強い」と同義ではないため、必ず年度と具体的実績で表示する。

### 著名卒業生 `notable_alumni[]`

- `name`
- `field`
- `affiliation_note`
- `graduation_year`
- `source_id` **必須**

原則として公人・著名人として公に活動実績があり、大学公式、本人公式、公的機関等で在籍・卒業関係を確認できる人物を掲載する。Wikipediaのみを唯一の根拠にしない。卒業・中退・在籍等は `affiliation_note` で正確に区別する。

## 11. ⑦ 出典・最終確認日

### 出典 `sources[]`

出典を大学レコード内で一元管理し、各項目から `source_id` で参照する。

`source_type` の優先度:

1. `official_university` — 大学公式
2. `government` — 文部科学省・自治体等
3. `official_organization` — 大学法人・国家試験機関・競技団体等の公式
4. `person_official` — 著名卒業生本人の公式情報
5. `other_primary` — その他の一次資料
6. `secondary` — 補助的な二次資料

出典には `title`、`url`、`publisher`、`published_at`、`verified_at`、`status` を持たせる。

### 検証状態 `verification`

- `last_verified_at`
- `verification_status`: `verified / partial / needs_review`
- `verified_sections[]`
- `pending_sections[]`
- `notes`

セクション名は次で統一する。

`basic / academics / campuses / tuition / admissions / qualifications / careers / research / sports_culture / notable_alumni`

公開画面では、可能なら「最終確認日」と「未確認領域」を利用者が分かる形で表示する。

## 12. null・空配列・未収録の正式ルール

| 状態 | 保存方法 | 意味 |
|---|---|---|
| 値を確認できた | 値 | 確認済み事実 |
| 調査したが値を特定できない | `null` | 不明・未確定 |
| 該当制度・項目がないことを確認した | `[]` | 確認済みで該当なし |
| まだ調査していない | `null` または構造内の空値 + `pending_sections` | 未調査 |

**空文字 `""` を「不明」の意味で使わない。** URL未確認、人数未確認等は `null` とする。

## 13. ID規則

| 対象 | 形式 | 例 |
|---|---|---|
| 大学 | `u` + 6桁 | `u000001` |
| 学部 | `f` + 6桁 | `f000137` |
| 学科 | `d` + 6桁 | `d000001` |
| 専攻・コース | `p` + 6桁 | `p000001` |
| 研究科 | `g` + 6桁 | `g000001` |
| 大学院課程 | `gp` + 6桁 | `gp000001` |
| キャンパス | `c` + 6桁 | `c000001` |
| 入試方式 | `a` + 6桁 | `a000001` |
| 出典 | `src` + 3桁以上 | `src001` |

IDは表示順を意味しない。一度公開したIDを、大学名変更・組織改編を理由に再利用しない。

## 14. 東京都144大学版からの移行

現行の大学基本データでは大学IDとして `id` が使われている。v1.0への移行では以下とする。

1. 現行 `id` の値を変更しない。
2. `university_id = id` として新しい正式キーを追加する。
3. 移行期間中は `id` を互換用に残してよい。
4. 新規コードは `university_id` を優先し、なければ `id` を読むフォールバックを許容する。
5. 学部・学科等の既存IDも原則維持し、不要な採番し直しをしない。
6. 現行生成済みJSONを一括でv1.0へ無理に変換せず、検証済み領域から段階移行する。

## 15. 検証でJSON Schemaだけでは確認できない事項

`university.schema.json` は型・必須項目・列挙値・ID形式等を検証する。ただし次は別途整合性検査が必要である。

- `faculty_id`、`department_id`、`campus_id`、`source_id` が実在する参照先を指すこと
- `university_id` と互換用 `id` を併記する場合に両者が一致すること
- `student_counts.total` と内訳の合計が合理的に一致すること
- `pass_rate` と受験者数・合格者数の整合性
- 学費の合計値と構成項目の整合性
- `verified_sections` と実データ充足状況の整合性
- URLが実在し、大学・公的機関の正しいページを指すこと

これらは将来の検証スクリプト/CIで扱う。

## 16. 完成判定

大学1校を「v1.0完成」と呼べるのは、最低限次を満たす場合とする。

- 大学基本情報と公式URLが確認済み
- 学部・学科・専攻/コースの現行組織を確認済み（該当しない階層は確認済み空配列）
- 全主要キャンパスと最寄駅を確認済み
- 最新対象年度の学費を確認済み
- 最新対象年度の入試方式・Web出願導線を確認済み、または募集停止を確認済み
- 主な資格・卒業後進路を確認済み
- 研究、スポーツ・文化、著名卒業生は「確認済み情報」または「該当なし/掲載見送り」を明確化
- 各重要項目に出典があり、`verification.last_verified_at` が設定済み
- `verification_status = verified`

「情報量が多いこと」ではなく、**何が確認済みで、何が未確認かを明示できること**を完成条件とする。

## 17. バージョン方針

- v1.0.x: 意味を変えない誤記・説明修正
- v1.x: 後方互換のある項目追加
- v2.0: 必須項目変更、キー削除、列挙値の意味変更等の破壊的変更

スキーマを変更する際は、先にこの仕様書とJSON Schemaを更新し、その後に各都道府県データへ展開する。
