# 無料モニター版 Public GitHub Release 公開チェックリスト

更新日: 2026-09-25

## 1. 通常版系

### Release
- Repository: `bantai-education-design/bantai-education-design.github.io`
- Tag: `education-monitor-v5.70.12`
- Title: `小学校教育計画システム 無料モニター版 Ver.5.70.12`

### Upload assets
- `bantai_kyomu_support_monitor_v5.70.12.zip`
- `bantai_weekplan_monitor_v5.70.12.zip`
- `bantai_education_planning_monitor_manual_v5.70.12.pdf`
- `SHA256SUMS.txt`

### Expected SHA-256
- 教務支援 ZIP  
  `48b39454252b68f15ac1c36cdb7f2d22c5d75277d4c3272c4f09f5ebb94f1315`
- 週案 ZIP  
  `40dd1486d8bf233d378cda883ec4248875ba661fae713c5fa3e0996b5f36d0a2`
- 共通マニュアル PDF  
  `7d175f986d3d15a011ecb3b583023c384a7c04b828f3b04f145a41285244a114`

### Verified published URLs (公開済み・ハッシュ検証完了)
- 教務支援  
  `https://github.com/bantai-education-design/bantai-education-design.github.io/releases/download/education-monitor-v5.70.12/bantai_kyomu_support_monitor_v5.70.12.zip`
- 週案  
  `https://github.com/bantai-education-design/bantai-education-design.github.io/releases/download/education-monitor-v5.70.12/bantai_weekplan_monitor_v5.70.12.zip`
- 共通マニュアル  
  `https://github.com/bantai-education-design/bantai-education-design.github.io/releases/download/education-monitor-v5.70.12/bantai_education_planning_monitor_manual_v5.70.12.pdf`

## 2. 調整授業時数対応版

### 公開前ゲート
Public Releaseを作成する前に、実Windows環境で以下を実行する。

```
npm run verify:setup
```

Stable版と調整授業時数対応版について、インストール・更新・アンインストールの共存を確認する。

### Release
- Tag: `adjusted-monitor-v1.0.6`
- Title: `調整授業時数対応版 無料モニター Ver.1.0.6`

### Upload assets
- `bantai_adjusted_curriculum_monitor_v1.0.6.zip`
- `bantai_adjusted_curriculum_monitor_manual_v1.0.6.pdf`
- `SHA256SUMS.txt`

### Expected SHA-256
- ZIP  
  `ddb6466ea032413e7fa17479e49ee730c57acd6fc433fb5634c496afaed4730b`
- 専用マニュアル PDF  
  `962c35279503e04eba737947d46396d4be2412c20a8979791c4fdec956240224`

### Planned direct URLs
- ZIP  
  `https://github.com/bantai-education-design/bantai-education-design.github.io/releases/download/adjusted-monitor-v1.0.6/bantai_adjusted_curriculum_monitor_v1.0.6.zip`
- マニュアル  
  `https://github.com/bantai-education-design/bantai-education-design.github.io/releases/download/adjusted-monitor-v1.0.6/bantai_adjusted_curriculum_monitor_manual_v1.0.6.pdf`

## 3. Release公開後の必須確認

1. public Releaseページをログアウト状態でも開ける。
2. 各assetを公式HP経由で再ダウンロードする。
3. SHA-256を再計算し、本書の値と一致する。
4. Windows実機でZIP展開・起動する。
5. モニター版ではシリアル要求が出ないことを確認する。
6. 公式HPの「公式HPから無料ダウンロード」ボタンを有効化する。
7. Vector版と同一ZIPであることを確認する。
8. GA4の公式HPダウンロードイベントが送信されることを確認する。

## 4. 公式HP画像の配置予定

バイナリ画像はサイト実装時に以下へ配置する。

- `/assets/images/education-planning/kyomu-support-features.webp`
- `/assets/images/education-planning/weekplan-features.webp`
- `/assets/images/education-planning/integrated-overview.webp`
- `/assets/images/education-planning/adjusted-features.webp`
- `/assets/images/education-planning/adjusted-hero.webp`
- `/assets/images/education-planning/monitor-download-flow.webp`

画像を配置するまで、ページ側で存在しない画像パスを参照しない。
