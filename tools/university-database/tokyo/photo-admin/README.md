# 大学写真 管理画面

## 正式な管理入口

- 管理ハブ: `/tools/university-database/tokyo/photo-admin/`
- Ban.Tai本人撮影登録: `/tools/university-database/tokyo/photo-register/?mode=owner`
- 一般投稿: `/tools/university-database/tokyo/photo-submit/`

一般ユーザーは `photo-submit/` で写真送信だけを行う。大学DBへの登録、補正、メイン・サブ写真の選択は管理者が行う。管理ハブには「本人撮影写真を登録」と「訪問者写真を審査」の2入口を置く。

## 管理コード

管理コードは公開GitHub PagesのHTML、JavaScript、JSONには絶対に書かない。

Supabase Edge Function `university-photo-review` の秘密環境変数 `REVIEW_ADMIN_CODE` にだけ保存する。推奨は24文字以上のランダム文字列で、他サービスのパスワードを流用しない。

ブラウザでは管理コードをAPIへHTTPS送信して照合する。保持する場合も `sessionStorage` のみで、`localStorage` には保存しない。タブを閉じると消える。

## 訪問者写真の保存場所

公開投稿は自動公開しない。

1. `university-photo-submission` Edge Function が投稿を受信
2. 非公開Storage `university-photo-submissions` に審査用ZIPを保存
3. ZIP内の新規写真も個別に非公開Storageへ保存
4. `photo_submissions` に `pending` として記録
5. 管理画面は `university-photo-review` から20分有効の署名付きURLを受け取り、写真を表示
6. 管理者が `pending / approved / rejected / published` を更新

承認 (`approved`) は公開を意味しない。大学DBへ実際に反映した後だけ `published` にする。

## Supabase セットアップ順

1. `../photo-register/backend/schema.sql` を実行
2. `../photo-register/backend/supabase-edge-function.ts` を `university-photo-submission` としてデプロイ
3. `../photo-register/backend/supabase-review-function.ts` を `university-photo-review` としてデプロイ
4. Edge Function secrets を設定
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `REVIEW_ADMIN_CODE`
   - 通知を使う場合: `RESEND_API_KEY`, `REVIEW_NOTIFICATION_EMAIL`, `REVIEW_FROM_EMAIL`, `REVIEW_DASHBOARD_URL`
5. `admin-runtime-config.json` の `enabled` を `true` にし、review function endpointを設定
6. `../photo-register/submission-runtime-config.json` の `enabled` を `true`、`mode` を `remote` にし、submission function endpointを設定
7. 本番で一般投稿→審査待ち→管理画面表示→承認/却下を確認してから運用開始

## セキュリティ

- Storage bucketは常にprivate
- `photo_submissions` はRLSを有効にし、匿名ポリシーを作らない
- service role keyをGitHub Pagesへ出さない
- 管理コード照合はEdge Function側だけで行う
- CORSはBan.Tai公式GitHub Pages originだけを許可
- 審査URLは `noindex,nofollow`
- 本番では管理コード試行回数制限も追加すること
