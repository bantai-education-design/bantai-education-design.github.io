# 本人写真掲載 API（Vercel）

`api/publish.js` は GitHub Pages とは別の Vercel Project にデプロイする。ブラウザは公開鍵や GitHub token を持たず、API は main を直接変更しない。

## 必須環境変数

- `OWNER_PUBLISH_KEY`: 本人・Ban.Tai管理者にだけ安全な経路で配布する掲載キー
- `OWNER_PUBLISH_GITHUB_TOKEN`: 次の最小権限を持つ当該リポジトリ限定の GitHub fine-grained token
- `OWNER_PUBLISH_REPOSITORY`: `bantai-education-design/bantai-education-design.github.io`
- `OWNER_PUBLISH_ALLOWED_ORIGIN`: `https://bantai-education-design.github.io`

これらは Vercel の Environment Variables にのみ置く。公開リポジトリ、JavaScript、JSON、GitHub Pages へ入れてはいけない。

GitHub fine-grained token の推奨権限は次のとおり。

- Actions: Read-only
- Administration: Read-only
- Contents: Read and write
- Pull requests: Read and write

Checks 権限は不要。必要CIの状態は owner PR の `head_sha` に対する Actions workflow runs と jobs から取得する。

## API の安全条件

- 大学IDは main の `universities_tokyo_all.generated.json` にあるIDだけを許可する。
- JPEG/PNG/WebP 以外、1枚2 MiB超、合計10 MiB超、9枚超を拒否する。公開カードは実デコードした 720×405 JPEG だけを保存する。
- 現在の owner レコードと画面を開いた時点の `base_owner_record` が異なる場合は競合として失敗する。
- main の写真台帳はサーバーが読み直し、対象大学のレコードだけを置換または削除する。したがって他大学の変更を上書きしない。
- GitHub Tree API で画像と台帳を単一コミットにし、専用ブランチと掲載用PRを作る。main は一切書き換えない。
- `main` の branch protection または ruleset に必須CIがある場合だけ、API は掲載用PRを ready-for-review で作り、GitHub auto-merge を依頼する。GitHub が必須CIの成功を確認するまで main へは入らない。
- 必須CIを要求する保護設定がない場合は、掲載用PRを Draft にして `review_required` を返す。画面は「掲載申請を受け付けました。管理者確認待ちです」と表示し、公開完了やPages待機を表示しない。
- `GET /api/publish?university_id=<id>&request_id=<id>` は同じ掲載キーでPR状態を返す。`merged` を確認した時だけクライアントがPages反映待ちへ移行する。

デプロイ後に初めて `owner-publish-config.json` の `enabled` を `true` にし、ステージング大学で「保護なしの確認待ち」「必須CI失敗」「必須CI成功→auto-merge→Pages反映」を確認する。
