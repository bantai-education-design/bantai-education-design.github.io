# サーバーを所有しない運用者向けの配置案

**準備済みの配置案です。クラウドサービスの契約・課金・デプロイはまだ行っていません。**

主案はRenderのマネージドWebサービス＋永続ディスクです。運用者がVPS・OS・SSH・Dockerサーバーを用意する必要はありません。HTTPSと公開URLはRenderが提供し、下書き・画像はサービス専用の非公開ディスクへ保存します。

## 料金と承認する内容

2026-11-11に公式資料を取得して確認した見積り：

| 項目 | 設定 | 月額の目安 |
| --- | --- | --- |
| Webサービス | 0.5 CPU / 512MB、plan `0.5c-512mb` | US$7 |
| 永続ディスク | 1GB | US$0.25 |
| 合計 | 1サービス・1ディスク | **US$7.25程度** |

税金、為替、帯域・ビルド等の従量超過、追加サービスは別です。契約直前の画面で最新料金を確認します。無料Webサービスは永続ディスクの構成に適さないため、今回の本番案には採用していません。1GBにはSQLiteと画像・バックアップが入るので、使用量を監視し、必要時の増量も料金確認後に行います。

確認元： [料金](https://render.com/pricing) / [Blueprint仕様](https://render.com/docs/blueprint-spec) / [永続ディスク](https://render.com/docs/disks) / [標準環境変数](https://render.com/docs/environment-variables)

有料契約の承認後に必要な利用者側の操作は、Renderへのログイン、GitHubの対象リポジトリへの接続許可、秘密設定の入力です。秘密値はチャットへ送らず、サービスの秘密設定に直接登録します。こちらからRenderアカウントを操作できる接続は現在ありません。既存Vercel接続にはチーム権限不足があり、現在のSQLiteをそのままVercelの一時ファイルシステムへ置く方法は採用しません。

## 具体的な配置設定

リポジトリ直下の `render.yaml` を用意しています。Render DashboardのBlueprint作成で、対象リポジトリと `feat/bantai-admin-center` ブランチを選びます。**作成ボタンを押すと有料リソースが作成されるため、費用の承認前には実行しません。**

- Node.js 24.22.2で、コミット済みの編集画面とサーバーを起動。
- データ保存先は `/var/data/bantai-admin/live`。マウント `/var/data/bantai-admin` 内だけが永続領域。
- 管理画面のoriginはRenderの `RENDER_EXTERNAL_URL` を使う。自前ドメイン不要。独自ドメインへ移す場合だけ `ADMIN_ORIGIN` を明示する。
- `/healthz` は機密情報を含まない起動確認用。管理APIは認証必須。
- 自動デプロイはoff。mainへのマージやブランチ更新だけではサービスを自動変更しない。
- 初回は管理パスワードのscryptハッシュだけをRenderの `ADMIN_PASSWORD_HASH` に登録。`sync: false` により値をYAMLへ書かない。
- GitHubへの公開申請を有効にする段階で、対象リポジトリ限定の `ADMIN_GITHUB_TOKEN` をRenderの秘密設定へ登録する。未設定でも下書き保存・画像・プレビューは利用でき、公開申請は失敗を明示する。

パスワードハッシュは `node services/admin-center/src/hash-password.js /リポジトリ外の保存先` の非表示入力で生成します。ハッシュも公開ファイル・チャットへ記載しません。トークンも同じく秘密設定のみです。設定済みのCodex/GitHub接続トークンを勝手に転用しません。

デプロイ後は、HTTPSログイン、ログアウト、自動保存→再起動→再読込、画像・プレビュー、バックアップ・別領域復元を受入確認します。公開申請の受入試験は公開してよい内容で、PR作成までに止めます。人間の承認なしにマージしません。最後に、確認した実URLのみを `admin/center-config.json` へ別PRで設定します。現在はdisabledのままです。

## バックアップと、元データを上書きしない復元

`src/backup.js` はSQLiteのオンラインバックアップ機能を使用します。アップロード画像はハッシュ名・変更不可・無断削除なしを前提に、DBのスナップショット後にコピーし、チェックサム付きmanifestを保存します。アップロード中などの整合性エラーでは成功扱いにせず、manifestのない不完全な保存先を復元に使用しません。

RenderのShellから、未使用の保存先名を指定して実行します。下記 `SNAPSHOT_NAME` と `RESTORE_NAME` は置換用の名前です。

```sh
mkdir -p /var/data/bantai-admin/snapshots
node services/admin-center/src/backup.js create /var/data/bantai-admin/live /var/data/bantai-admin/snapshots/SNAPSHOT_NAME
node services/admin-center/src/backup.js restore /var/data/bantai-admin/snapshots/SNAPSHOT_NAME /var/data/bantai-admin/RESTORE_NAME
```

- 既存ディレクトリへは保存・復元しない。liveを上書きしない。
- 復元前に全チェックサムとSQLite整合性を検査する。
- 復元したコピーのセッションを失効させる。元の稼働中セッション・データは変更しない。
- 復元内容を確認後に、停止・保存先切替・再起動の実施内容をレビューする。切替はこのスクリプトでは行わない。
- 同じディスク内だけのバックアップはディスク障害対策にならない。暗号化したコピーを別媒体・別サービスへ保管する運用先も、契約・接続先の確認後に設定する。自動削除や自動世代整理はしない。

## Dockerによる検証済みの代替構成

`deploy/Dockerfile` は非root、固定ダイジェストのNodeイメージ、秘密を含めないビルドコンテキストを使います。実行時だけ `ADMIN_PASSWORD_HASH_FILE` / `ADMIN_GITHUB_TOKEN_FILE` から秘密を読みます。アプリ領域は読み取り専用にでき、データとバックアップは別ボリュームです。

```sh
docker build -f services/admin-center/deploy/Dockerfile -t bantai-admin-center:local .
node services/admin-center/test/container.mjs
```

コンテナテストはテスト専用の名前・秘密値・ボリュームを作って、起動、認証、Secure Cookie、再起動後の保存、バックアップ・別領域復元、Compose/Caddy設定を確認します。実際の本番ボリュームやGitHubへは書き込みません。

`compose.yml` はCaddy付き、`compose.existing-proxy.yml` は既存HTTPSプロキシ向けです。後者はCaddyを起動せず、アプリをホストの127.0.0.1だけへ公開します。これは将来別の管理者・サービスがDockerホストを用意する場合の代替で、今回の利用者にサーバー準備を求めるものではありません。秘密ファイルの所有者はコンテナUID1000、親ディレクトリ0700・ファイル0400とし、リポジトリ外へ配置します。

Dockerビルドとローカル検証は成功済みです。Render固有の実デプロイ・証明書発行・ディスク再配置と、実際の料金画面の確認は契約承認後の未検証項目です。
