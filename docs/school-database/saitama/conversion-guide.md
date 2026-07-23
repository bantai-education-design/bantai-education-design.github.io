# 埼玉県学校データ変換手順

## 目的

埼玉県公式Excel名簿を、公式HP検索用の `data/school-database/saitama.json` に変換する。

## 原本配置

公式Excelを次のフォルダーへ保存する。

```text
data-source/saitama/2025/
```

ファイル名は `tools/school-database/saitama_sources.json` の `file` と一致させる。

原本Excelは公開用データではないため、Git管理へ含める前に容量・再配布条件を確認する。原則として、原本はローカル作業用として管理し、公式HPには変換後JSONのみを配置する。

## 必要環境

```powershell
python -m pip install openpyxl
```

## 変換

```powershell
python tools/school-database/convert_saitama_workbooks.py
```

不足ファイルは `SKIP missing` と表示される。存在する原本だけで仮変換できるが、公開用JSONは対象全ファイルが揃ってから確定する。

## 検証

```powershell
python tools/school-database/validate_school_data.py `
  data/school-database/saitama.json `
  --prefecture 埼玉県
```

## 確認事項

- 見出し行が自動検出できているか
- 学校名、住所、郵便番号、電話番号が正しい列から取得されているか
- 分校・分教室が欠落していないか
- 高校の全日制・定時制・通信制を同一校として統合するか、課程別レコードとして残すか
- 私立幼稚園の件数が県公式一覧と一致するか
- 住所に埼玉県が二重付与されていないか
- 郵便番号や電話番号がExcelの数値化で先頭ゼロを失っていないか

## 公開禁止条件

次のいずれかに該当する場合は `prefectures.json` の埼玉県を `published` に変更しない。

- 必須校種の原本が不足
- 変換エラーが残る
- 県公式件数との不一致理由が未確認
- 抽出結果の原本照合が未完了
- 東京都版の回帰確認が未完了
