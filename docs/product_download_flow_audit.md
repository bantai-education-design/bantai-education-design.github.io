# 商品ページ 販売導線 点検報告書（試用版DL・BOOTH・Vector）

- 調査日: 2026-07-14
- 対象リポジトリ: bantai-education-design/bantai-education-design.github.io
- 対象コミット: 7a8c72b（origin/main 最新、調査前に fast-forward 済み）
- 作業範囲: 調査のみ。HTML修正・リンク変更・ZIP配置・Release作成・タグ作成は行っていない。

## 1. 点検の前提（新しい販売導線方針）

1. 試用版は公式HPから直接ダウンロードできるようにする。
2. 購入・ライセンス取得はBOOTHへ集約する。
3. Vectorは認知拡大・外部掲載用の補助導線として残す。
4. 商品ページのボタン順は「試用版DL → BOOTH購入 → Vector掲載」の順に整理する。

## 2. 商品別 導線一覧

凡例: ◯=あり ×=なし △=言及のみ（リンクなし） −=対象外

| 商品名 | 商品ページURL | 試用版DLの有無 | 試用版DLの現在のリンク先 | BOOTHリンクの有無 | Vectorリンクの有無 | 現在の導線順 | 修正が必要か | 推奨修正内容 | 備考 |
|---|---|---|---|---|---|---|---|---|---|
| 小学校教育計画作成・運営システム | /products/education-planning/ | △（モニター版） | BOOTH（items/8547376）。キーはGoogleフォーム登録の自動返信 | ◯（DL用として3ボタン） | × | 無料モニター登録（Googleフォーム）→ BOOTH DL | 要修正 | モニター版ZIPの公式HP直DLボタンを先頭に追加し、BOOTHは購入・DL窓口として2番目に整理。dl-gridの3ボタンが全て同一URLなので、実体に合わせて統合または個別URL化 | 「約130MB／約60MB／約70MB」と3種類の説明があるがリンク先は全て同一。navの「無料ダウンロード」の実体はBOOTH誘導 |
| Ban.Tai はじめての五線紙メーカー | /products/first-staff-paper/ | ◯（BOOTH経由） | BOOTH（items/8587307、0円バリエーション） | ◯ | ×（本文に「Vectorでは体験版配布のみ」の言及あり） | 試用版（BOOTH 0円）→ 製品版購入（BOOTH） | 要修正 | 試用版ZIPを公式HP直DLに切り替え（ボタン1）、BOOTH購入（ボタン2）、Vector掲載リンク（ボタン3）を追加。本文の「BOOTH/Gumroad経由」からGumroadを削除 | 導入フローStep1に「公式HP（本ページ）から無料体験版をダウンロード」と書かれているが、実際のボタンはBOOTH行きで本文と実装が矛盾している |
| 漢字練習帳 | /products/kanji-practice/ | △（アンカーのみ） | #trial セクション → 実体はBOOTH（items/8305799） | ◯（3箇所） | × | BOOTH購入 → 10日間無料体験版（アンカー） | 要修正 | ヒーローのボタン順を「試用版DL（公式HP直DL）→ BOOTH購入」に逆転。#trialセクションのボタンも試用版直DLに変更 | ヒーローで購入ボタンが試用版より先に来ており、方針4と逆順 |
| 方眼紙メーカー | /products/houganshi/ | △（BOOTH内バリエーション） | BOOTH（items/8479863、体験版・本体） | ◯（3箇所） | × | BOOTH購入のみ | 要修正 | 試用版（体験版・本体）の公式HP直DLボタンを先頭に追加。「ダウンロード導線はBOOTHに集約しています。公式HPからZIPやEXEへの直接リンクは掲載していません」という明文が新方針1と正面から矛盾するため削除・書き換え | 旧方針（BOOTH集約・直リンク禁止）がページ本文に明文化されている代表例 |
| 学級名簿メーカー（無料） | /products/class-roster/ | −（無料版そのもの） | GitHub Releases 直リンク（gakkyu-meibo-maker v0.6.5 ZIP） | ×（無料のため対象外） | × | 無料DL → 機能を見る | 原則不要（要方針確認） | 「公式HPから直接DL」をGitHub Releases直リンクで満たすと解釈するなら現状維持。/downloads/ 配下への集約を求めるなら要変更 | observation-cardページの「GitHubは一般利用者向けの直接配布先にはしません」という記述とサイト内で矛盾 |
| 絵日記・観察カード作成メーカー | /products/observation-card/ | △（BOOTH内で試用） | BOOTH（items/8579732） | ◯（ヒーロー1箇所） | △（「登録済み・URL反映待ち」カードのみ、リンクなし） | BOOTH購入 → 配布ページ → 注意事項 | 要修正 | 試用版の公式HP直DLボタンを先頭に追加。VectorのURLが確定したら配布ページカードにリンクを追加 | 「GitHubは開発管理用であり、一般利用者向けの直接配布先にはしません」の記述が無料ツール2製品のGitHub Releases配布と矛盾 |
| スマート履歴書ジェネレーター | /products/resume-generator/ | ×（公開準備中） | − | ×（準備中カードのみ） | ×（準備中カードのみ） | ボタンなし（アンカーのみ） | 現時点は不要 | 公開時に「試用版DL → BOOTH購入 → Vector掲載」の順で導線を新設 | 配布ページセクションにBOOTH・Vector・公式HP配布の3枠が準備中として既に用意されており、方針に沿った構成にしやすい |
| 画像文字入れくん | /products/text-overlay/ | ◯（Vector経由） | Vector（se528755.html） | × | ◯（購入もVector） | Vectorからダウンロード・購入のみ | 要修正（要判断） | 方針2に従うならBOOTHに出品し「試用版DL → BOOTH購入 → Vector掲載」に再構成。BOOTH出品しない場合はVector専売の例外として明示 | 現状、購入導線がVectorに集約されており方針2（購入はBOOTH集約）と矛盾する唯一の製品 |
| 証明写真メーカー | /products/id-photo/ | ×（試用版なし） | − | ◯（2箇所） | × | BOOTH購入 → note記事 | 軽微な修正 | 試用版を提供しないなら現状の導線順は方針に近い。section id="vector"（実体はBOOTH購入）の紛らわしいID・nav表記を修正。ほぼ同一の「プレビュー機能」セクションが2回重複しているので1つに統合 | 「公式ホームページから直接ZIPやEXEは配布しません」の明文あり。将来試用版を出す場合は方針1と衝突するため要書き換え |
| Ban.Tai バナースタジオ（無料） | /products/banner-studio/ | −（無料版そのもの） | 公式HP内 /downloads/BanTai_BannerStudio_v3.0.0.zip | × | × | 無料DL → 感想を送る | 軽微な修正 | 導線自体は方針に合致（公式HP直DLの実装済み前例）。本文の「このページのボタンは、サイト内のZIPファイルを直接ダウンロードする形にします。」という制作メモ調の一文を削除 | /downloads/ に旧版 BanTai_BannerStudioV2_Final.zip とプレースホルダーtxt（ここに_..._を入れてください.txt）が残存。整理候補 |
| 楽譜・五線紙 作成メーカー | /products/staff-paper/ | ×（案内休止中） | − | ×（入門版のBOOTHへ誘導のみ） | × | 休止案内 → 購入済み者向けライセンス申請フォーム | 現時点は不要 | 再開時に方針4の順で導線を新設 | products.json には hasTrial:true / boothUrl（items/8302315）が残っており、一覧カードの data-has-trial="true" と休止状態が不整合（表示への実害はなし） |
| 学級座席デザイナー（無料） | /products/classroom-seat-designer/ | −（無料版そのもの） | Web版（公式HP内）＋ GitHub Releases（詳細ページはタグページ、一覧カードはZIP直リンク） | × | × | Web版 → Windows版DL | 原則不要（軽微） | 詳細ページ（releasesタグページ）と一覧カード（ZIP直リンク）でリンク先の粒度が不統一。どちらかに揃えると親切 | 無料公開版。BOOTH・Vector・note掲載は別途残作業として記録済み |

## 3. 商品一覧ページ・トップページの状況

- products/index.html（商品一覧）は tools/build_products.py による自動生成。カードのボタン順は render_actions() のロジックで決まり、現在は「無料DL（status=無料のみ）→ BOOTH → Vector → note → 分野を見る → 詳細を見る」の順。
- 現行ロジックには「試用版DL」という概念が存在しない。hasTrial はバッジ・data属性にしか使われず、試用版DLボタンは生成されない。有料製品のカードは必ず「BOOTHで購入・ダウンロードする」が先頭になる。
- トップページ index.html にも製品ごとのCTAボタンが手書きで存在する（バナースタジオ=公式HP直DL、学級名簿=GitHub Releases、有料5製品=BOOTH、画像文字入れくん=Vector）。build_products.py はトップページの統計プレースホルダーしか更新しないため、トップページのボタンは手動修正が必要。
- カテゴリページ（/products/music-tools/、/products/school-work/）には配布リンクはない。修正不要。

## 4. 実装時に修正すべきファイル（build_products.py 関連）

商品一覧のボタンを方針4の順にするには、次の3点セットの修正が必要になる。

1. data/products.json — 試用版DL先を持つフィールド（例: trialDownloadUrl）を新設し、各製品に公式HP内の試用版ZIPパスを設定する。
2. tools/build_products.py — render_actions() に試用版DLボタンの生成を追加し、出力順を「試用版DL → BOOTH → Vector → note」に変更する（現在は BOOTH が最優先）。
3. 実行 — products.json 編集後は必ず tools/build_products.py を実行して products/index.html を再生成する（手編集しない）。

商品詳細ページ（products/<slug>/index.html）は、ヘッダーコメント上は data/product-details/<slug>.json ＋ tools/build_product_detail.py の生成物とされているが、直近の実ページは手書きHTMLで管理されており detail JSON は実態と乖離している。詳細ページの導線修正はHTMLを直接編集するのが安全。トップページ index.html のCTAも手動修正。

## 5. 横断的な矛盾・古い表現の一覧

1. 方眼紙メーカー: 「ダウンロード導線はBOOTHに集約しています。公式HPからZIPやEXEへの直接リンクは掲載していません。」— 旧方針の明文。新方針1と矛盾。
2. 証明写真メーカー: 「公式ホームページから直接ZIPやEXEは配布しません。」— 同上（試用版がない製品のため当面の実害は小さい）。
3. はじめての五線紙メーカー: 導入フローStep1「公式HP（本ページ）から無料体験版をダウンロード」と実際のボタン（BOOTH行き）が矛盾。奇しくも本文側が新方針と一致しているため、実装をボタン側で追い付かせる形になる。
4. はじめての五線紙メーカー: 「必ずこちらの公式HPおよびBOOTH/Gumroad経由で行ってください」— Gumroadは現行チャネルにない。削除候補。
5. 絵日記・観察カード: 「GitHubは開発管理用であり、一般利用者向けの直接配布先にはしません。」— 学級名簿メーカー・学級座席デザイナーのGitHub Releases配布とサイト内で矛盾。無料ツールの配布場所方針を決めて表現を統一する必要がある。
6. 証明写真メーカー: section id="vector"・navアンカー「購入・ダウンロード」→ #vector だが、実体はBOOTH購入セクション。Vector掲載実績もない。ID・表記の残骸。
7. 証明写真メーカー: 「プレビュー機能」セクションがほぼ同一内容で2回出現（重複）。
8. バナースタジオ: 「このページのボタンは、サイト内のZIPファイルを直接ダウンロードする形にします。」— 利用者向け文章に制作メモが露出。
9. 教育計画システム: dl-grid の3つのDLボタンが説明（約130MB／約60MB／約70MB）だけ異なり、リンク先は全て同一のBOOTH商品。実体と表示の不一致。
10. downloads/ ディレクトリ: 旧版ZIP（BanTai_BannerStudioV2_Final.zip）と配置指示用プレースホルダーtxtが残存。
11. products.json: 楽譜・五線紙作成メーカー（休止中）に hasTrial:true と旧BOOTH URLが残存。

## 6. 無料ツールと有料・試用版アプリの区別

- 無料ツール（学級名簿メーカー、バナースタジオ、学級座席デザイナー）は「無料」バッジと「無料でダウンロードする」ボタンで統一されており、有料製品との混同は起きていない。
- 有料側は「10日間無料体験」「販売中」などのバッジで区別されているが、体験版のダウンロード自体がBOOTH内にあるため、「無料体験」バッジから利用者が期待する動き（すぐDLできる）と実際の動き（BOOTHへ遷移して0円購入）にずれがある。方針1の実装（公式HP直DL）でこのずれは解消される。
- 注意点として、無料ツールのDL先が「公式HP内（/downloads/）」と「GitHub Releases」の2方式に分かれている。方針1を無料ツールにも適用するかどうか（GitHub Releases直リンクを「公式HPから直接DL」とみなすか）は要判断。

## 7. 推奨する実装順序（次フェーズの参考）

1. 方針判断が必要な2点を先に決める: (a) 試用版ZIPの置き場所（/downloads/ 直置きか GitHub Releases か）、(b) 画像文字入れくんのBOOTH出品有無。
2. 試用版ZIPを決めた場所に配置（対象: はじめての五線紙、漢字練習帳、方眼紙、絵日記・観察カード、教育計画モニター版）。
3. products.json に trialDownloadUrl を追加し、build_products.py の render_actions() を「試用版DL → BOOTH → Vector → note」順に改修 → 実行して一覧を再生成。
4. 各商品詳細ページのボタンと本文（矛盾表現11件）を手動修正。
5. トップページ index.html のCTAを同じ順序に手動修正。
