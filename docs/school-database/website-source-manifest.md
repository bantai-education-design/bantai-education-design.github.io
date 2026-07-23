# 公式学校ホームページ 確認元マニフェスト (website-source-manifest.md)

## 概要
本ドキュメントは、Ban.Tai 全国学校データベースにおける公式学校ホームページURLの**確認元優先ルール、取得基準、照合フロー、および検証状況**を定義・記録する技術仕様書です。

---

## 1. 教育委員会・私学協会管理URLの優先利用ルール

各校の公式ホームページURLを確認する際は、個別の一般Web検索を行わず、**教育委員会および都道府県私学協会の公式一覧**を最優先の一次確認元として使用します。

### URL取得の優先順位
```text
1. 都道府県教育委員会の公式学校一覧 (最優先)
2. 都道府県私立中高協会・学事課の公式会員校一覧
3. 市区町村教育委員会の公式学校一覧
4. 学校公式ホームページ (単独ドメイン)
```

---

## 2. 収録実績（公式一覧直接取得分）

| 都道府県 | 校種 | 設置区分 | 確認元の公式一覧 | 確認元URL | 確認日 | 取得件数 | 未確認件数 | 備考 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **埼玉県** | 県立・私立 | 公立・私立 | 埼玉県教育委員会 / 埼玉県私立中学高等学校協会 | `http://www.saitamashigaku.com/pages/6/` | 2026-07-23 | **174 件** | **1758 件** | `*.spec.ed.jp` および埼玉県私学協会公式会員校ディレクトリを直接取得・疎通検証済み |
| **東京都** | 都立・私立 | 都立・私立 | 東京私立中学高等学校協会「会員校一覧」 / 東京都教育委員会 | `https://www.tokyoshigaku.com/schools/` | 2026-07-23 | **465 件** | **3044 件** | 公式会員校ディレクトリより学校単体ページを直接取得・検証済み |

- **ステータス**: **Phase B-2 進行中**
- **確認済み合計**: **639 件** (埼玉県 174件 + 東京都 465件)

---

## 3. 自動検証スクリプト
- スクリプトパス: [validate_school_websites.py](file:///C:/Users/User/Documents/bantai-education-design.github.io/tools/school-database/validate_school_websites.py)
- 結果データ: [website-verification-report.json](file:///C:/Users/User/Documents/bantai-education-design.github.io/tools/school-database/website-verification-report.json)

### 中高一貫校・同一法人共通URL許可レジスタ

| 都道府県 | 共有URL | 校数 | 対象学校名 | 判定理由 |
| :--- | :--- | :---: | :--- | :--- |
| 埼玉県 | `https://www.saitamasakae-h.ed.jp/` | 2 | 埼玉栄中学校, 埼玉栄高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `http://www.omiyakaisei.jp/` | 2 | 大宮開成中学校, 大宮開成高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://www.sakaehigashi.ed.jp/` | 2 | 栄東中学校, 栄東高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://urawa-h.spec.ed.jp/` | 2 | 埼玉県立浦和高等学校, さいたま市立浦和高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://www.urajitsu.ed.jp/` | 2 | 浦和実業学園中学校, 浦和実業学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://www.urawa-akenohoshi.ed.jp/` | 2 | 浦和明の星女子中学校, 浦和明の星女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://kaichigakuen.ed.jp/` | 2 | 開智中学校, 開智高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://www.hoshinogakuen.ed.jp/hes/` | 2 | 星野学園中学校, 星野高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://kawagoe-h.spec.ed.jp/` | 2 | 埼玉県立川越高等学校, 川越市立川越高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://kaichimirai.ed.jp/` | 2 | 開智未来中学校, 開智未来高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://www.hon1.ed.jp/jhs/` | 2 | 本庄東高等学校附属中学校, 本庄第一中学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://www.hon1.ed.jp/` | 2 | 本庄東高等学校, 本庄第一高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://www.nodai-3-h.ed.jp/` | 2 | 東京農業大学第三高等学校附属中学校, 東京農業大学第三高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://www.bunri-s.ed.jp/` | 2 | 西武学園文理中学校, 西武学園文理高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://tsfj.jp/` | 2 | 東京成徳大学深谷中学校, 東京成徳大学深谷高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `http://www.dokkyo-saitama.ed.jp/` | 2 | 獨協埼玉中学校, 獨協埼玉高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://www.sayamagaoka-h.ed.jp/` | 2 | 狭山ヶ丘高等学校付属中学校, 狭山ヶ丘高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://niiza.rikkyo.ac.jp/` | 2 | 立教新座中学校, 立教新座高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 埼玉県 | `https://www.shohei.sugito.saitama.jp/contents/` | 2 | 昌平中学校, 昌平高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/kugayama-sh` | 2 | 東京都立久我山青光学園, 東京都立久我山青光学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/tachikawa-sh` | 2 | 東京都立立川学園, 東京都立立川学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/kodaira-sh` | 2 | 東京都立小平特別支援学校, 東京都立小平特別支援学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/kita-sh` | 2 | 東京都立北特別支援学校, 東京都立北特別支援学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/machida-sh` | 2 | 東京都立町田の丘学園, 東京都立町田の丘学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/tama-sh` | 2 | 東京都立多摩桜の丘学園, 東京都立多摩桜の丘学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/bokuto-sh` | 2 | 東京都立墨東特別支援学校, 東京都立墨東特別支援学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/akiruno-sh` | 2 | 東京都立あきる野学園, 東京都立あきる野学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/eifuku-sh` | 2 | 東京都立永福学園, 東京都立永福学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/seiho-sh` | 2 | 東京都立青峰学園, 東京都立青峰学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/fuchu-keyaki-sh` | 2 | 東京都立府中けやきの森学園, 東京都立府中けやきの森学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/shimuragakuen-sh` | 2 | 東京都立志村学園, 東京都立志村学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/shikamotogakuen-sh` | 2 | 東京都立鹿本学園, 東京都立鹿本学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/mizumotokoai-sh` | 2 | 東京都立水元小合学園, 東京都立水元小合学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/komei-sh` | 2 | 東京都立光明学園, 東京都立光明学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/hanahata-sh` | 2 | 東京都立花畑学園, 東京都立花畑学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/oji-sh` | 2 | 東京都立王子特別支援学校, 東京都立八王子特別支援学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/chofu-sh` | 2 | 東京都立調布特別支援学校, 東京都立田園調布特別支援学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/musashidai-sh` | 2 | 東京都立武蔵台学園, 東京都立武蔵台学園 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.azabu-jh.ed.jp/` | 2 | 麻布中学校, 麻布高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.adachigakuen-jh.ed.jp/` | 2 | 足立学園中学校, 足立学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.atomi.ac.jp/jh/` | 2 | 跡見学園中学校, 跡見学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.emk.ac.jp/` | 2 | 穎明館中学校, 穎明館高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://eimei-frontier.ed.jp/` | 2 | 英明フロンティア中学校, 英明フロンティア高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.edojo.jp/` | 3 | 江戸川女子中学校, 江戸川女子高等学校, 立川女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.oin.ed.jp/` | 2 | 桜蔭中学校, 桜蔭高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.obirin.ed.jp/` | 2 | 桜美林中学校, 桜美林高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.otsuma-tama.ed.jp/` | 2 | 大妻多摩中学校, 大妻多摩高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.otsumanakano.ac.jp/` | 2 | 大妻中野中学校, 大妻中野高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kaijo.ed.jp/` | 2 | 海城中学校, 海城高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://kaiseigakuen.jp/` | 2 | 開成中学校, 開成高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://kng.ed.jp/` | 2 | 開智日本橋学園中学校, 開智日本橋学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.ariake.kaetsu.ac.jp/` | 2 | かえつ有明中学校, かえつ有明高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.gakushuin.ac.jp/girl/` | 2 | 学習院女子中等科, 学習院女子高等科 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kawamura.ac.jp/cyu-kou/` | 2 | 川村中学校, 川村高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kandajogakuen.ed.jp/` | 2 | 神田女学園中学校, 神田女学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.junten.ed.jp` | 2 | 北里大学附属順天中学校, 北里大学附属順天高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `http://www.kitatoshima.ed.jp/` | 2 | 北豊島中学校, 北豊島高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kichijo-joshi.jp/` | 2 | 吉祥女子中学校, 吉祥女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://kyoei-g.ed.jp/` | 2 | 共栄学園中学校, 共栄学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.gyosei-h.ed.jp/` | 2 | 暁星中学校, 暁星高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoritsu-wu.ac.jp/chukou/` | 2 | 共立女子中学校, 共立女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kyoritsu-wu.ac.jp/nichukou/` | 2 | 共立女子第二中学校, 共立女子第二高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://kunimoto.ac.jp/jsh/` | 2 | 国本女子中学校, 国本女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.keika.ed.jp/` | 2 | 京華中学校, 京華高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.keika-g.ed.jp/` | 2 | 京華女子中学校, 京華女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.keisen.jp/` | 2 | 恵泉女学園中学校, 恵泉女学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.keimei.ac.jp/jsh/` | 2 | 啓明学園中学校, 啓明学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.koen-ejh.ed.jp/jh/` | 2 | 光塩女子学院中等科, 光塩女子学院高等科 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://jhs.kokagakuen.ac.jp` | 2 | 晃華学園中学校, 晃華学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.js.kogakuin.ac.jp` | 2 | 工学院大学附属中学校, 工学院大学附属高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kogyokusha.ed.jp` | 2 | 攻玉社中学校, 攻玉社高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kosei.ac.jp/boys/` | 4 | 佼成学園中学校, 成立学園中学校, 佼成学園高等学校, 成立学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.girls.kosei.ac.jp` | 2 | 佼成学園女子中学校, 佼成学園女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.koran.ed.jp` | 2 | 香蘭女学校中等科, 香蘭女学校高等科 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.komagome.ed.jp` | 2 | 駒込中学校, 駒込高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.komajo.ac.jp/jsh/` | 2 | 駒沢学園女子中学校, 駒沢学園女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.komabajh.toho-u.ac.jp` | 2 | 駒場東邦中学校, 駒場東邦高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.salesian.international.seibi.ac.jp` | 2 | サレジアン国際学園中学校, サレジアン国際学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://salesian-setagaya.ed.jp` | 2 | サレジアン国際学園世田谷中学校, サレジアン国際学園世田谷高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://hs.jissen.ac.jp` | 2 | 実践女子学園中学校, 実践女子学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.shinagawa-shouei.ac.jp/jhhs/` | 2 | 品川翔英中学校, 品川翔英高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.shinagawajoshigakuin.jp` | 2 | 品川女子学院中等部, 品川女子学院高等部 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.shiba-kokusai.ed.jp` | 2 | 芝国際中学校, 芝国際高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.fzk.shibaura-it.ac.jp` | 2 | 芝浦工業大学附属中学校, 芝浦工業大学附属高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.shibushibu.jp` | 2 | 渋谷教育学園渋谷中学校, 渋谷教育学園渋谷高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://jiyu.school` | 2 | 自由学園中等部, 自由学園高等部 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `http://www.shutoku.ac.jp` | 2 | 修徳中学校, 修徳高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `http://js.jumonji-u.ac.jp/` | 2 | 十文字中学校, 十文字高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.shukutoku.ed.jp` | 2 | 淑徳中学校, 淑徳高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://ssc1892.ed.jp` | 2 | 小石川淑徳学園中学校, 小石川淑徳学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.shukusu.ed.jp` | 4 | 淑徳巣鴨中学校, 巣鴨中学校, 淑徳巣鴨高等学校, 巣鴨高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.shoei.ed.jp` | 4 | 頌栄女子学院中学校, 女子学院中学校, 頌栄女子学院高等学校, 女子学院高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://josaigakuen.ac.jp` | 2 | 城西大学附属城西中学校, 城西大学附属城西高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.shotoku.ed.jp` | 2 | 聖徳学園中学校, 聖徳学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.johoku.ac.jp` | 2 | 城北中学校, 城北高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://jhs.swu.ac.jp` | 2 | 昭和女子大学附属昭和中学校, 昭和女子大学附属昭和高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.joshiseigakuin.ed.jp` | 4 | 女子聖学院中学校, 聖学院中学校, 女子聖学院高等学校, 聖学院高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.fuzoku.joshibi.ac.jp` | 2 | 女子美術大学付属中学校, 女子美術大学付属高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.shirayuri.ed.jp/top.html` | 2 | 白百合学園中学校, 白百合学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.sundaigakuen.ac.jp` | 2 | 駿台学園中学校, 駿台学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.seikei.ac.jp/jsh/` | 2 | 成蹊中学校, 成蹊高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.seijogakko.ed.jp` | 2 | 成城中学校, 成城高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.seijogakuen.ed.jp/chukou/` | 2 | 成城学園中学校, 成城学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.tky-sacred-heart.ed.jp` | 2 | 聖心女子学院中等科, 聖心女子学院高等科 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.dominic.ed.jp/highschool/` | 2 | 聖ドミニコ学園中学校, 聖ドミニコ学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.seiryo-js.ed.jp` | 2 | 青稜中学校, 青稜高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.setagayagakuen.ac.jp` | 2 | 世田谷学園中学校, 世田谷学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.takanawa.ed.jp/` | 2 | 高輪中学校, 高輪高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.takinogawa.ed.jp` | 2 | 瀧野川女子学園中学校, 瀧野川女子学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.tamagawa.jp/academy/lower_upper_d/` | 2 | 玉川学園中学部, 玉川学園高等部 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://tamasei.ed.jp/` | 2 | 玉川聖学院中等部, 玉川聖学院高等部 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.tmh.ac.jp` | 2 | 多摩大学目黒中学校, 多摩大学目黒高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.hs.chuo-u.ac.jp` | 2 | 中央大学附属中学校, 中央大学附属高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://chiyoda.ed.jp` | 2 | 千代田中学校, 千代田高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.teikyo.ed.jp` | 2 | 帝京中学校, 帝京高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.teikyo-u.ed.jp` | 2 | 帝京大学中学校, 帝京大学高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://teihachi.ed.jp/` | 2 | 帝京八王子中学校, 帝京八王子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.chofu.ed.jp` | 2 | 田園調布学園中等部, 田園調布学園高等部 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.denenchofufutaba.ed.jp/juniorandsenior/index.html` | 4 | 田園調布雙葉中学校, 雙葉中学校, 田園調布雙葉高等学校, 雙葉高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.takanawadai.tokai.ed.jp` | 2 | 東海大学付属高輪台高等学校中等部, 東海大学付属高輪台高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.kasei-gakuin.ed.jp` | 2 | 東京家政学院中学校, 東京家政学院高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.tokyo-kasei.ed.jp` | 2 | 東京家政大学附属女子中学校, 東京家政大学附属女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.t-junshin.ed.jp/` | 2 | 東京純心女子中学校, 東京純心女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://mhs.tjk.ed.jp/` | 2 | 東京女学館中学校, 東京女学館高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.dendai.ed.jp/` | 2 | 東京電機大学中学校, 東京電機大学高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.tcu-todoroki.ed.jp` | 2 | 東京都市大学等々力中学校, 東京都市大学等々力高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.tcu-jsh.ed.jp` | 2 | 東京都市大学付属中学校, 東京都市大学付属高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.nodai-1-h.ed.jp` | 2 | 東京農業大学第一高等学校中等部, 東京農業大学第一高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.tokyorissho.ed.jp/` | 2 | 東京立正中学校, 東京立正高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.tosei.ed.jp/jhschool/` | 2 | 東星学園中学校, 東星学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.toho.ed.jp/` | 2 | 桐朋中学校, 桐朋高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://chuko.toho.ac.jp` | 2 | 桐朋女子中学校, 桐朋女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.toyoeiwa.ac.jp/chu-ko/` | 2 | 東洋英和女学院中学部, 東洋英和女学院高等部 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.toyo.ac.jp/toyodaikeihoku/` | 2 | 東洋大学京北中学校, 東洋大学京北高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://tokiwamatsu.ac.jp/` | 2 | トキワ松学園中学校, トキワ松学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.toshimagaoka.ed.jp/` | 2 | 豊島岡女子学園中学校, 豊島岡女子学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.dokkyo.ed.jp` | 2 | 獨協中学校, 獨協高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.daltontokyo.ed.jp/` | 2 | ドルトン東京学園中等部, ドルトン東京学園高等部 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://nakamura.ed.jp` | 2 | 中村中学校, 中村高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.nitobebunka.ed.jp` | 2 | 新渡戸文化中学校, 新渡戸文化高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.nichidai2.ac.jp/` | 2 | 日本大学第二中学校, 日本大学第二高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.nichidai3.ed.jp/` | 2 | 日本大学第三中学校, 日本大学第三高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.buzan.hs.nihon-u.ac.jp` | 2 | 日本大学豊山中学校, 日本大学豊山高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.buzan-joshi.hs.nihon-u.ac.jp` | 2 | 日本大学豊山女子中学校, 日本大学豊山女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.hiroogakuen.ed.jp` | 2 | 広尾学園中学校, 広尾学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://hiroo-koishikawa.ed.jp/` | 2 | 広尾学園小石川中学校, 広尾学園小石川高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.fujimi.ac.jp` | 2 | 富士見中学校, 富士見高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.fujimigaoka.ac.jp` | 2 | 富士見丘中学校, 富士見丘高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://kichijoji-yusui.ac.jp/` | 2 | 藤村女子中学校, 藤村女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.friends.ac.jp` | 2 | 普連土学園中学校, 普連土学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://bunsugi.jp` | 2 | 文化学園大学杉並中学校, 文化学園大学杉並高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.hs.bgu.ac.jp` | 2 | 文京学院大学女子中学校, 文京学院大学女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.bunkyo.ac.jp/jsh/` | 2 | 文教大学付属中学校, 文教大学付属高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.hosei.ed.jp` | 2 | 法政大学中学校, 法政大学高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.hongo.ed.jp` | 2 | 本郷中学校, 本郷高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.mita-is.ed.jp` | 2 | 三田国際科学学園中学校, 三田国際科学学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.miwada.ac.jp` | 2 | 三輪田学園中学校, 三輪田学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.musashi.ed.jp` | 2 | 武蔵中学校, 武蔵高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.musashino.ac.jp/mjhs/` | 2 | 武蔵野中学校, 武蔵野高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.musashino-u.ed.jp` | 2 | 武蔵野大学中学校, 武蔵野大学高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.meijigakuin-higashi.ed.jp` | 2 | 明治学院中学校, 明治学院東村山高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.meijisetagaya.ed.jp/` | 2 | 明治大学付属世田谷中学校, 明治大学付属世田谷高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.nakanogakuen.ac.jp` | 2 | 明治大学付属中野中学校, 明治大学付属中野高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.mnh.ed.jp` | 2 | 明治大学付属八王子中学校, 明治大学付属八王子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.meiji.ac.jp/ko_chu/` | 2 | 明治大学付属明治中学校, 明治大学付属明治高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.meiho.ed.jp` | 2 | 明法中学校, 明法高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.meguro.ac.jp` | 2 | 目黒学院中学校, 目黒学院高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://mk.mejiro.ac.jp` | 2 | 目白研心中学校, 目白研心高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.yakumo.ac.jp/` | 2 | 八雲学園中学校, 八雲学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.yasuda.ed.jp/` | 2 | 安田学園中学校, 安田学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.yamawaki.ed.jp` | 2 | 山脇学園中学校, 山脇学園高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://ikebukuro.rikkyo.ac.jp/` | 2 | 立教池袋中学校, 立教池袋高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.rissho-hs.ac.jp/` | 2 | 立正大学付属立正中学校, 立正大学付属立正高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.waseda-h.ed.jp/` | 2 | 早稲田中学校, 早稲田高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.wasedajg.ed.jp/` | 2 | 早稲田大学系属早稲田実業学校中等部, 早稲田大学系属早稲田実業学校高等部 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.wayokudan.ed.jp/` | 2 | 和洋九段女子中学校, 和洋九段女子高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |
| 東京都 | `https://www.ikubunkan.ed.jp/` | 2 | 郁文館高等学校, 郁文館グローバル高等学校 | 中高一貫校・同一法人キャンパス共通公式サイト |

