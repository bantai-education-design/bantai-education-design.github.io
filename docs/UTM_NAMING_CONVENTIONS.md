# Ban.Tai Education Design 外部媒体UTM命名規則（候補B）

note・はてなブログ・X（旧Twitter）などの外部媒体からBan.Tai公式HP（`bantai-education-design.github.io`）へ誘導する際のリンクパラメータ規則です。既存のGA4計測（`G-KPGJ0R2KXR`）を変更せずに流入元別の実測比較を可能にします。

## 基本フォーマット

```text
https://bantai-education-design.github.io/<path>/?utm_source=<source>&utm_medium=<medium>&utm_campaign=<campaign>&utm_content=<content>
```

- `utm_source`（必須・流入媒体）:
  - `note`（note記事・プロフィール）
  - `hatena`（はてなブログ記事）
  - `x`（Xの投稿・プロフィール）
  - `booth`（BOOTH商品ページからの戻り導線）
- `utm_medium`（必須・流入種別）:
  - `article`（note・はてなブログ等の記事本文リンク）
  - `social`（Xの通常投稿・リプライ）
  - `profile`（各サービスのプロフィール固定リンク）
- `utm_campaign`（必須・企画または製品・DB識別子、英小文字とハイフンのみ）:
  - 製品例: `class-canvas`, `houganshi`, `class-roster`, `pitapasha`
  - データベース例: `school-db`, `university-db`, `music-db`
  - 書籍例: `book-hogosha-hitokoto`, `book-hiyoko`
- `utm_content`（任意・記事slugや設置位置、英小文字とハイフンのみ）:
  - 例: `20261123-intro-cta`, `footer-link`, `summary-card`

## 禁止事項と注意点

1. 日本語・スペース・大文字・個人情報（メールアドレスやアカウントID等）はパラメータに含めない。
2. 公式サイト内の内部リンク（トップページから製品ページへの移動など）にはUTMを付けない（GA4のセッションが分断されるため）。
3. 既存の `assets/js/analytics-events.js` はプライバシー保護のためクリック先 `link_url` のクエリを除去する仕様ですが、外部媒体から公式HPへ流入した際のUTMパラメータはGA4標準の `page_view` で自動記録されます。

## 記述例

- note記事から「みんなのクラス・キャンバス」製品ページへ誘導する場合:
  `https://bantai-education-design.github.io/products/class-canvas/?utm_source=note&utm_medium=article&utm_campaign=class-canvas&utm_content=20261123-body`
- はてなブログから全国学校データベースへ誘導する場合:
  `https://bantai-education-design.github.io/tools/school-database/?utm_source=hatena&utm_medium=article&utm_campaign=school-db&utm_content=20261123-sports`
- X投稿から書籍紹介ページへ誘導する場合:
  `https://bantai-education-design.github.io/books/?utm_source=x&utm_medium=social&utm_campaign=book-hogosha-hitokoto&utm_content=20261123-post`
