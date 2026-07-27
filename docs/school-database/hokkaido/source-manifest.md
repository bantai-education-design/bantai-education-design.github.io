# 北海道学校宛先データベース 出典一覧

収録件数: 1,998校・園（令和7〜8年度版データを統合）

## 公立小学校・中学校・義務教育学校・幼稚園（教育局別）

北海道教育委員会は14教育局ごとに管内公立小中学校一覧を独自形式（HTML表・PDF・市町村別ページ）で公開しているため、局ごとに個別の一次資料を使用しています。

| 教育局 | 形式 | URL |
|---|---|---|
| 空知教育局 | HTML表 | https://www.dokyoi.pref.hokkaido.lg.jp/hk/stk/soragatukouitiran.html |
| 石狩教育局 | PDF | https://www.dokyoi.pref.hokkaido.lg.jp/hk/ikk/ishidata.html |
| 後志教育局 | PDF | https://www.dokyoi.pref.hokkaido.lg.jp/hk/sbk/youran.html |
| 胆振教育局 | HTML表（市町村別11ページ） | https://www.dokyoi.pref.hokkaido.lg.jp/hk/ibk/gakko_kyoikuiinkai_ichiran.html |
| 日高教育局 | HTML表 | https://www.dokyoi.pref.hokkaido.lg.jp/hk/hdk/gakkouitiran.html |
| 渡島教育局 | PDF（要覧「渡島の教育」） | https://www.dokyoi.pref.hokkaido.lg.jp/hk/oky/11_soumu/125972.html |
| 檜山教育局 | HTML表 | https://www.dokyoi.pref.hokkaido.lg.jp/hk/hyk/gakkouichiran.html |
| 上川教育局 | PDF（要覧「上川の教育」） | https://www.dokyoi.pref.hokkaido.lg.jp/hk/kkk/kamikawayouran.html |
| 留萌教育局 | PDF（要覧） | https://www.dokyoi.pref.hokkaido.lg.jp/hk/rky/youran.html |
| 宗谷教育局 | PDF | https://www.dokyoi.pref.hokkaido.lg.jp/hk/syk/156121.html |
| オホーツク教育局 | PDF | https://www.dokyoi.pref.hokkaido.lg.jp/hk/okh/school.html |
| 十勝教育局 | PDF（要覧「十勝の教育」） | https://www.dokyoi.pref.hokkaido.lg.jp/hk/tky/65283.html |
| 釧路教育局 | HTML表 | https://www.dokyoi.pref.hokkaido.lg.jp/hk/krk/page03/gakkouitiran.html |
| 根室教育局 | HTML表 | https://www.dokyoi.pref.hokkaido.lg.jp/hk/nky/kannnaikouritugaltukou.html |

石狩教育局の一覧には政令指定都市・札幌市分は含まれません（札幌市は別途市教育委員会のページから取得）。

## 札幌市立小学校・中学校

- 小学校: https://www.city.sapporo.jp/kyoiku/top/school/ichiran/shogaku.html
- 中学校: https://www.city.sapporo.jp/kyoiku/top/school/ichiran/chugaku.html

区ごとのHTML表（学校名・所在地・電話番号）。郵便番号は原本に掲載がないため、日本郵便の郵便番号データ（下記）から住所照合により補完しています。

## 公立高等学校・中等教育学校

北海道教育委員会 高校教育課「公立高等学校一覧」（令和8年度版）
https://www.dokyoi.pref.hokkaido.lg.jp/hk/kki/gakkou.html

## 特別支援学校

北海道教育委員会 特別支援教育課「特別支援学校所在地等一覧」（令和7年度版、画像PDF）
https://www.dokyoi.pref.hokkaido.lg.jp/hk/tkk/yoran.html

原本がスキャン画像PDFでテキストレイヤーを持たないため、目視で書き起こしています（道立・市立札幌市立・国立・私立の全73校・分校を収録）。

## 国立学校

北海道教育大学 附属学校園一覧
https://www.hokkyodai.ac.jp/attached/school_list/

## 私立学校（幼稚園・小学校・中学校・高等学校・特別支援学校・専修学校・各種学校）

北海道庁 総務部行政局学事課「学校検索・一覧」（令和7年度版）
https://www.pref.hokkaido.lg.jp/sm/gkj/allschoolseach.html

振興局×校種別に分割されたExcelファイル（58本）から収集。専修学校・各種学校は、本データベースが対象とする学校種の範囲外のため収録していません。原本に郵便番号列がないため、日本郵便の郵便番号データから住所照合により補完しています。

## 郵便番号補完について

私立学校（幼稚園・小中高・特別支援）および札幌市立小中学校の原本には郵便番号が含まれていないため、日本郵便が公開する「住所の郵便番号（1レコード1行、UTF-8形式）」データ（令和8年6月版）を用いて、市区町村＋町域名の一致により郵便番号を補完しています。
https://www.post.japanpost.jp/zipcode/download.html

町域名の表記ゆれ（丁目範囲の分割、条丁目の算用数字/漢数字表記差）等により、一部の学校（62校・園、全体の約3.1%）では自動補完ができず郵便番号欄が空欄のままとなっています。該当校は検索結果画面で郵便番号欄が空白表示されます。

## 除外したレコードについて

石狩教育局・宗谷教育局・十勝教育局のPDFの一部で、ページ境界をまたぐ行の抽出崩れにより市町村名を確定できなかった約54件（全体の約2.6%）は、必須項目未充足として収録対象から除外しています。主に該当教育局管内の一部小中学校です。今後、原本PDFの構造を精査した上での追加収録を検討します。

## データ処理上の注記

- 学校名・住所・電話番号は原本の表記に基づいています。
- 「認定こども園」は「幼保連携型認定こども園」として分類しています。
- 重複データ（学校名・住所・電話番号が完全一致するもの）は1件に統合しています。
- 休校・休園中と原本に明記された学校は収録対象から除外しています。
