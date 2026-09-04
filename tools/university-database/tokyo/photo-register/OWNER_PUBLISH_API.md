# 本人写真掲載 API（Vercel）

`api/owner-photo-publish.js` は GitHub Pages とは別の Vercel Project にデプロイする。ブラウザは公開鍵や GitHub token を持たず、API は main を直接変更しない。検証後に `owner-photo/<大学ID>-<request-id>` ブランチと Draft PR だけを作る。

## 必須環境変数

- `OWNER_PUBLISH_KEY`: 本人・Ban.Tai管理者にだけ安全な経路で配布する掲載キー
- `OWNER_PUBLISH_GITHUB_TOKEN`: 当該リポジトリの Contents と Pull requests への書込み権限を持つ GitHub fine-grained token
- `OWNER_PUBLISH_REPOSITORY`: `bantai-education-design/bantai-education-design.github.io`
- `OWNER_PUBLISH_ALLOWED_ORIGIN`: `https://bantai-education-design.github.io`

これらは Vercel の Environment Variables にのみ置く。公開リポジトリ、JavaScript、JSON、GitHub Pages へ入れてはいけない。

## API の安全条件

- 大学IDは main の `universities_tokyo_all.generated.json` にあるIDだけを許可する。
- JPEG/PNG/WebP 以外、1枚2 MiB超、合計10 MiB超、9枚超を拒否する。公開カードは実デコードした 720×405 JPEG だけを保存する。
- 現在の owner レコードと画面を開いた時点の `base_owner_record` が異なる場合は競合として失敗する。
- main の写真台帳はサーバーが読み直し、対象大学のレコードだけを置換または削除する。したがって他大学の変更を上書きしない。
- GitHub Tree API で画像と台帳を単一コミットにし、専用ブランチと Draft PR が作れた時だけ成功を返す。main は一切書き換えない。

デプロイ後に初めて `owner-publish-config.json` の `enabled` を `true` にし、ステージング大学で作成された Draft PR、必須CI、Pages反映までを確認する。
