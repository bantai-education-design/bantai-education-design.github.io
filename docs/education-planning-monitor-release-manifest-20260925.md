# 教育計画システム 公開用Releaseアップロード・マニフェスト

作成日: 2026-09-25  
対象Publicリポジトリ: `bantai-education-design/bantai-education-design.github.io`

## Public Release

推奨タグ:

`education-planning-monitors-2026-09-25`

Releaseの目的:
- 公式HPからの無料モニター版直接ダウンロード
- Vectorへ提出するZIPと同一ファイルを恒久配布
- 大容量バイナリをGitリポジトリ本体へ入れない

## 確定済みモニターZIP

### 教務支援システム

- file: `bantai_kyomu_support_monitor_v5.70.12.zip`
- bytes: `170827361`
- SHA-256: `5f41a18af1c5b3c44773f3cc29e4420ea1c4d9a6e86d36dcdf82d254f7cee424`
- build source commit: `136fb93f70f5557770d964a9f1b1731819a2fc79`
- source workflow run: `36069187907`
- source artifact: `monitor-packages-v5.70.12`

公開後の予定URL:

`https://github.com/bantai-education-design/bantai-education-design.github.io/releases/download/education-planning-monitors-2026-09-25/bantai_kyomu_support_monitor_v5.70.12.zip`

### 週案システム

- file: `bantai_weekplan_monitor_v5.70.12.zip`
- bytes: `170690105`
- SHA-256: `73131ca44ecd99b13a20b01e6c80ec61d21951ce2e3d9882253766e2c7c28d73`
- build source commit: `136fb93f70f5557770d964a9f1b1731819a2fc79`
- source workflow run: `36069187907`
- source artifact: `monitor-packages-v5.70.12`

公開後の予定URL:

`https://github.com/bantai-education-design/bantai-education-design.github.io/releases/download/education-planning-monitors-2026-09-25/bantai_weekplan_monitor_v5.70.12.zip`

### 調整授業時数対応版

- file: `bantai_adjusted_curriculum_monitor_v1.0.6.zip`
- bytes: `170900449`
- SHA-256: `ddb6466ea032413e7fa17479e49ee730c57acd6fc433fb5634c496afaed4730b`
- build source commit: `15f660f7b0b8bb2bfc65132d23ad2d45c850cbcf`
- source workflow run: `36069472382`
- source artifact: `adjusted-monitor-package-v1.0.6`

公開後の予定URL:

`https://github.com/bantai-education-design/bantai-education-design.github.io/releases/download/education-planning-monitors-2026-09-25/bantai_adjusted_curriculum_monitor_v1.0.6.zip`

## マニュアルPDF

通常版系artifactに含まれるPDF:
- `小学校教育計画システム_無料モニター版_利用マニュアル_v5.70.12.pdf`

調整版artifactに含まれるPDF:
- `調整授業時数対応版_無料モニター_利用マニュアル_v1.0.6.pdf`

Public Releaseには上記PDFも添付する。

## SHA一覧

Release assetとして `SHA256SUMS.txt` を作成し、最低限次の3行を入れる。

```text
5f41a18af1c5b3c44773f3cc29e4420ea1c4d9a6e86d36dcdf82d254f7cee424  bantai_kyomu_support_monitor_v5.70.12.zip
73131ca44ecd99b13a20b01e6c80ec61d21951ce2e3d9882253766e2c7c28d73  bantai_weekplan_monitor_v5.70.12.zip
ddb6466ea032413e7fa17479e49ee730c57acd6fc433fb5634c496afaed4730b  bantai_adjusted_curriculum_monitor_v1.0.6.zip
```

## 公開前ゲート

- [x] 通常版系 `verify:all` PASS
- [x] 教務支援 / 週案 Windows build PASS
- [x] 通常版系マニュアルPDF生成 PASS
- [x] 調整版 `verify:all` PASS
- [x] 調整版 installer identity check PASS
- [x] 調整版 print / shuan-print / school-settings PASS
- [x] 調整版 Windows build PASS
- [x] 調整版マニュアルPDF生成 PASS
- [ ] 調整版 `verify:setup` 実機双方向共存テスト（Stable installerを使うローカル専用ゲート）
- [ ] Public Releaseへ3 ZIP + 2 PDF + SHA256SUMS.txtをアップロード
- [ ] 公開Release URLから再ダウンロードしSHA-256再照合
- [ ] Vector提出ファイルのSHA-256がPublic Releaseと一致
- [ ] 公式HPの「公式HPから無料DL」ボタンを有効化

## 注意

Privateのアプリ開発リポジトリのActions artifact / Releaseを、一般利用者向け恒久URLとして使わない。一般公開用バイナリはPublicの公式HPリポジトリのReleasesに置く。
