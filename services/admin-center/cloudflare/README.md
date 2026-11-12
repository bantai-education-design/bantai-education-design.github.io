# 自前サーバー・月額契約を前提にしない管理センター

利用者の希望に従い、**Cloudflare Workers Free＋D1 Free** を主案にします。有料Render案は採用せず、参考設定を `deploy/render.yaml.example` に退避しました。ルートに自動適用される有料Blueprintは置きません。2026-11-12に利用者の画面でWorkers Free（$0・Current plan）を確認し、新規専用D1と認証設定前のテストWorkerを作成しました。プラン変更・有料製品の契約は行っていません。

## 構成と、無料枠の条件

- 管理画面・APIはWorkersのHTTPS付き `workers.dev` URLで提供。自前ドメイン、VPS、常駐サーバーは不要。
- 下書き・版履歴・原本・セッション・画像はD1へ保存。ブラウザーだけの保存へは格下げしない。
- R2、KV、有料Workers、外部有料DBは利用しない。D1の画像はBLOBとして非公開保存する。
- GitHub OAuthで実際に認証し、設定された管理者ログイン名と一致した利用者だけ許可する。OAuthの `state` を署名付きHttpOnly Cookieで照合する。GitHubトークンやクライアント秘密値はWorkers Secretsだけに置く。
- セッションは8時間、CookieはSecure/HttpOnly/SameSite=Strict。DBにはトークンのハッシュのみを保存し、変更APIはOriginとCSRFを検証する。
- 公開は既存の専用ブランチ＋PRだけ。mainへの直接更新・自動マージ・本番記事や画像の削除は行わない。

2026-11-11にCloudflare公式ドキュメントの公開ソースで確認したFreeの主な上限：

| 項目 | Freeの上限 |
| --- | --- |
| Workersリクエスト | 1日100,000 |
| Workers CPU時間 | 1リクエスト10ms |
| D1読込 | 1日5,000,000行 |
| D1書込 | 1日100,000行（インデックス等も加算） |
| D1保存 | 1DB 500MB、アカウント合計5GB、10DBまで |
| D1 Time Travel | 7日間 |

日次枠のリセットは日本時間09:00です。Freeプランのまま運用し、プラン変更・追加の有料製品を有効にしません。上限時は処理停止・未保存表示とし、自動アップグレードする処理を実装しません。既にPaid契約のアカウントを使う場合はFreeと同じ請求条件と決めつけず、設定を確認する必要があります。

無料構成のアプリ上限は**画像1枚1MB、1記事9枚**。新規画像を勝手に加工・縮小せず、元ファイルが上限を超えれば明示して止めます。既存の大学写真管理ツールは別の既存フローを再利用します。

CPU制限に備え、既存60記事のHTML解析はビルド時に前処理します。原本データはWorker内部の非公開バンドルに含め、公開アセットへは置きません。取り込み時は最新mainの一覧・原本ハッシュを確認し、外部変更があれば再ビルドを要求して上書きを止めます。既存の下書きはそのまま開けます。プレビューのメタデータ更新も事前記録した位置情報を使います。**実際のFree環境のCPU・容量・負荷確認はアカウント接続後の受入検証として残っています。**

確認元：

- [Workers制限の公式ソース](https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/docs/workers/platform/limits.mdx)
- [D1制限の公式ソース](https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/docs/d1/platform/limits.mdx)
- [D1料金の公式ソース](https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/partials/workers/d1-pricing.mdx)

## 準備済み・ローカル検証

```sh
cd services/admin-center
npm ci
npm run build:cloudflare
npm test
npm run test:cloudflare
npx wrangler deploy --dry-run --config cloudflare/wrangler.jsonc
```

`npm test` の前処理も、生成物だけを更新します。公開記事・大学DB・写真の原本は変更しません。ローカルD1テストは独立した一時DBへ `--local` でマイグレーションし、認証必須API、自動保存、競合、復元、画像の非公開保存、ログインリダイレクトを確認します。GitHub OAuthの交換・管理者照合・CSRF・無料枠エラーはモック付き結合テストで検証しています。実GitHubトークンや実Cloudflare認証は使いません。

## 利用開始に必要なアカウント設定

Wranglerへのログイン、無料プラン確認、新規専用DB作成・初回スキーマ適用、テストWorker配置まで実施済みです。GitHub OAuth Appと公開申請用の権限設定は未完了です。秘密情報をチャットへ書く必要はありません。

1. 利用者がCloudflareの無料アカウントへログインする。Workers Freeであることを確認し、有料プラン・R2を契約しない。
2. WranglerのOAuthログインを利用する。APIトークンの平文をチャットへ送らない。
3. FreeのD1データベースを1個作成し、実際に返された非秘密のDB IDを `wrangler.jsonc` へ設定する。実DB IDは設定済みです（非秘密）。
4. 接続先・DB名・IDを確認してから、初回スキーマを適用する。既存本番DBを作り直したり削除したりしない。`migrations/0001_admin.sql` は新規専用DB向け。
5. 生成した実際の `workers.dev` URLを使ってGitHub OAuth Appを登録し、コールバックを `/auth/callback` にする。存在しないURLを推測して登録しない。
6. `GITHUB_OAUTH_CLIENT_ID`、`GITHUB_OAUTH_CLIENT_SECRET`、32バイト以上のランダムな `SESSION_SECRET` をWorkers Secretsへ登録する。管理者名は `ADMIN_GITHUB_LOGIN`。GitHubへの公開申請を使う際だけ、対象リポジトリに限定した `ADMIN_GITHUB_TOKEN` を別のSecretとして登録する。ログイン用OAuthスコープは `read:user` に限定し、そのユーザートークンを公開トークンへ流用しない。
7. 認証・自動保存・再読込・画像・復元、FreeのCPU/容量、公開してよいテスト内容でのPR作成まで受入確認する。人間の承認なしにマージしない。
8. 成功後、確認済みの実URLだけを `admin/center-config.json` へ別PRで設定する。現在はdisabled。

DB作成・初回スキーマ適用・テストWorker配置は新規専用リソースに限って実施しました。入口有効化・本番切替・マージは未実施です。自動デプロイやPaidへの変更は設定しません。

### 2026-11-12 接続記録

- テストURL: https://bantai-admin-center.bantai-admin-center.workers.dev
- OAuthコールバック: https://bantai-admin-center.bantai-admin-center.workers.dev/auth/callback
- 新規D1: `bantai-admin-center`、APAC、`24da1473-581a-451a-8d50-1ccb378b569f`。作成直前の既存D1・Worker一覧は空でした。初回16 SQLコマンド適用成功。
- `SESSION_SECRET` はランダム生成して標準入力からWorkers Secretへ登録（値はリポジトリ・ログに保存しない）。GitHub OAuth App設定前はログイン不可のままです。
- ビルド、29件のテスト、実ローカルWorkers+D1結合テストは再実行して成功。
- 実URLの検証は作業環境のEnvoyプロキシが上流接続エラー503を返すため未完了。DNS解決とCloudflareへの配置完了は確認済み。APIによる認証拒否・実DB永続化・CPU上限の受入確認は残っています。
- `admin/center-config.json` は引き続きdisabled。公開記事・大学DB・元画像は未変更。

## バックアップ

D1 Freeには7日間のTime Travelがあります。加えて、所有者の認証でD1をSQLへエクスポートし、暗号化して公開リポジトリ外へ保管する運用を準備します。SQLには下書きや画像が入るため、GitHub Pagesや公開アセットへ置きません。復元は別のFree D1へインポートして確認し、稼働DBを無断で上書きしません。実アカウントでのエクスポート・別DB復元はまだ未検証です。
