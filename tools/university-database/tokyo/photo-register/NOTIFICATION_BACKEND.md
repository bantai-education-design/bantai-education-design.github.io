# 大学写真投稿 通知・審査バックエンド

## 目的
公開GitHub Pagesから投稿者の写真を安全に受け取り、公開DBとは分離した「審査待ち」に保存し、運営者へ通知する。

## 公開側の原則
- 投稿者は「審査に提出する」を1回押すだけ。
- 公開リポジトリに運営者メールアドレス、API秘密鍵、サービスロール鍵を置かない。
- 投稿は自動公開しない。必ず `pending` で受け付ける。
- 1投稿=1大学、最大9枚、メイン1枚+サブ最大8枚。

## 推奨構成
Supabase を受信・審査基盤として使う。

1. `photo_submissions` テーブル
   - `submission_id`
   - `university_id`
   - `university_name`
   - `submitted_at`
   - `photo_count`
   - `main_photo`
   - `agreements`
   - `status` (`pending` / `approved` / `rejected` / `published`)
   - `package_path`
2. 非公開 Storage bucket `university-photo-submissions`
3. Edge Function `university-photo-submission`
   - CORSはBan.Tai公式サイトを許可
   - multipart/form-data の `metadata` と `package` を受信
   - MIME/容量/9枚上限/大学IDを検証
   - 非公開Storageへ保存
   - `photo_submissions` に `pending` で記録
   - 運営者へメール通知
4. 審査画面は認証済み運営者だけが閲覧

## フロントエンド契約
`submission-runtime-config.json` を次のように変更すると、投稿ボタンが自動的にリモート提出へ切り替わる。

```json
{
  "schema_version": 1,
  "enabled": true,
  "mode": "remote",
  "endpoint": "https://<project>.supabase.co/functions/v1/university-photo-submission",
  "notification": "operator_email",
  "review_queue": true
}
```

フロントエンドは以下を `POST` する。

- `metadata`: `application/json` の `submission.json`
- `package`: 審査用ZIP

成功レスポンス:

```json
{
  "ok": true,
  "submission_id": "BT-UP-20260825105400-AB12",
  "notified": true,
  "review_status": "pending"
}
```

## 通知メール
件名例:

`[大学写真投稿] 立教大学 / 6枚 / BT-UP-20260825105400-AB12`

本文には以下だけを載せ、写真そのものはメール添付しない。

- 大学名
- 写真枚数
- 受付番号
- 投稿日時
- 審査待ちURL

通知先アドレスは Edge Function の秘密環境変数 `REVIEW_NOTIFICATION_EMAIL` に保存する。公開JSONやJavaScriptには記載しない。

## 迷惑投稿対策
本番公開前に必ず以下を有効にする。

- Origin検証
- 1 IPあたりのレート制限
- 最大リクエスト容量
- ZIP/MIME検証
- 受付番号のサーバー側再発行または検証
- Turnstile等のボット対策
- Storageを非公開にする

## 障害時
通知APIが未接続・停止中の場合、公開ページは自動的に `local_package` モードへ戻る。投稿者には「審査用データを保存」と表示し、「提出済み」と誤表示しない。
