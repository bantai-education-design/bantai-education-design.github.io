# 試用版ZIP候補 安全確認結果（第2段階A-2）

- 確認日: 2026-07-14
- 前提文書: [棚卸し結果](trial_zip_inventory.md) / [実装計画書](product_download_flow_implementation_plan.md)
- 確認方法: ZIPを展開せずにエントリ一覧を走査し、同梱テキスト・HTML単体版のみ一時領域に抽出して内容を確認した。リポジトリへのZIPコピー・/downloads/trials/ の作成は行っていない。

## 結論

- 方眼紙メーカー v3.1.2 体験版: 配置可。安全上の問題なし。
- 絵日記・観察カード作成メーカー v1.2.0: 安全上の問題なし。ただし同梱READMEの表題が「Vector掲載・配布向け」のままのため、そのまま置くか、公式HP用に案内文のみ差し替えるかの判断が1点残る。

## 1. 方眼紙メーカー v3.1.2 体験版

- 元ファイル: C:\Users\User\Documents\アプリ\方眼紙メーカー\release\方眼紙メーカー-v3.1.2-体験版.zip
- サイズ: 73.8MB（100MB未満・配置可）
- ZIPは正常に開封可能。エントリは4件のみ:
  1. HouganshiMaker-Setup-3.1.2.exe（73.8MB・インストーラ）
  2. manual.pdf（0.3MB・操作マニュアル）
  3. README_体験版.txt
  4. はじめにお読みください.txt

確認結果:

- ライセンスキー.txt は含まれていない。
- license_key / serial / secret / token / api_key / password / 購入者 / 注文 等の危険語を含むファイル名はゼロ件。
- 同梱テキスト2件を全文確認。購入者情報・個人情報・キー情報は含まれていない。
- 内容はチャネル中立（BOOTH・Vector・Gumroadいずれの固有表記もなし）。「体験版・本体」であること、10日間試用、SAMPLE透かし、継続利用には製品版ライセンスキーが必要であることが明記されており、試用版として配布してよい構成。
- BOOTH購入方針との矛盾はなし。ただしREADMEにはライセンスキーの購入先（BOOTH URL）が書かれていない。矛盾ではないため配置の妨げにはならないが、次回ビルド時にBOOTH商品ページURLを追記するとより親切（任意・今回は対応しない）。
- 公式HP用ファイル名案 bantai_graph_paper_trial_v3.1.2.zip は妥当。

判定: 合格。そのまま /downloads/trials/ に配置できる。

## 2. 絵日記・観察カード作成メーカー v1.2.0

- 元ファイル: C:\Users\User\Documents\アプリ\観察カード\04_Release\絵日記・観察カード作成メーカー-v1.2.0-Vector-Trial-Windows.zip
- サイズ: 76.9MB（100MB未満・配置可）
- ZIPは正常に開封可能。エントリは7件:
  1. BantaiObservationCardMaker-1.2.0-win-x64.exe（76.9MB・インストーラ）
  2. html版\絵日記・観察カード作成メーカー.html（HTML単体版・保険用）
  3. CHANGELOG.md
  4. MANUAL.md
  5. README_Vector.txt
  6. VERSION
  7. はじめにお読みください.txt

確認結果:

- ライセンスキー.txt は含まれていない。危険語を含むファイル名はゼロ件。
- 同梱テキスト4件（README_Vector.txt、はじめにお読みください.txt、CHANGELOG.md、MANUAL.md）を確認。購入者情報・個人情報・キー情報は含まれていない。
- HTML単体版はアプリ本体のため中身も検査した。ライセンス検証は LICENSE_HASHES 配列に対する SHA-256 ハッシュ照合方式で、平文のライセンスキーは埋め込まれていない。既存のBOOTH・Vector配布と同一の方式であり、公式HP配布によって新たな露出は生じない。
- BOOTH購入方針との整合: README_Vector.txt は「ライセンスキーはBOOTHの商品ページで購入できます（480円）」とBOOTH商品URL・公式HP商品ページURLを明記しており、方針と一致している。矛盾記述なし。
- 気づいた点2件（安全上の問題ではない）:
  1. README_Vector.txt の表題が「Vector掲載・配布向け説明（10日間試用版）」で、公式HPから配るZIPとしてはチャネル表記が不自然。
  2. はじめにお読みください.txt が「BOOTHで入手した場合: README_BOOTH.txt」を参照しているが、このZIPに README_BOOTH.txt は同梱されていない（BOOTH版ビルドにのみ存在すると思われる）。
- 公式HP用ファイル名案 bantai_observation_card_trial_v1.2.0.zip は妥当。

判定: 安全上は合格。配置方法について次の2案から要判断。

- 案A: このZIPをそのまま新ファイル名で配置する（最速。README表題の不自然さは残るが、内容はBOOTH誘導で正しい）。
- 案B: README_Vector.txt を「README_試用版.txt」相当（チャネル中立の表題・同内容）に差し替えた公式HP用ZIPを作ってから配置する（丁寧。ZIP再作成の手間が1回発生）。

## 共通確認事項

- 両ZIPとも、棚卸しで注意喚起した 99_Archive_危険_キー同梱ZIP_使用禁止 配下のファイルではないこと、ファイル名に「使用禁止」「キー同梱」を含まないことを確認済み。
- 両ZIPとも100MB未満で、GitHubの1ファイル制限に抵触しない。

## 次の作業（第2段階B の想定）

1. 観察カードの案A／案Bの判断。
2. /downloads/trials/ を作成し、確定した2ファイルを新ファイル名でコピー・コミット。
3. data/products.json への trial_download_url 追加（build_products.py 改修とセット）。
