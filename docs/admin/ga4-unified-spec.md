# Ban.Tai Education Design — GA4計測統一仕様書

## 1. 概要と基本方針

本サイト（Ban.Tai Education Design 公式サイト）におけるアクセス解析および主要アクション計測は、Google Analytics 4（GA4）を正本として一本化します。

- **GA4測定ID**: `G-KPGJ0R2KXR`
- **データ正本性**: 公開カウンター等のUI要素は新設せず、GA4管理画面およびLooker Studio連携データを公式指標の正本とします。
- **既存システムとの関係**: KARTEタグおよび教育計画PVの既存計測は破壊せず併用を維持します。

## 2. 対象ページ分類と設置基準

リポジトリ内の全98HTMLファイルは以下の4区分に厳密に分類され、公開ページのみにGA4タグを設置します。

| 区分 | ページ数 | GA4タグ設置 | 備考 |
|---|---|---|---|
| 公開・GA4対象 | 88 | 設置（統一スニペット） | トップ、商品一覧・詳細、学校DB、大学DB、コラム等 |
| 管理・GA4対象外 | 6 | 対象外（完全除外） | `admin/`、写真管理、写真審査等の内部ツール |
| テンプレート・GA4対象外 | 3 | 対象外（完全除外） | `templates/` 配下のHTMLテンプレート |
| 検証用・GA4対象外 | 1 | 対象外（完全除外） | `index-new.html`（リダイレクト検証用） |
| **合計** | **98** | - | `tools/audit_html_ga4.py` により自動検証 |

### 2.1 将来のタグ保守・更新方法
将来、GA4タグスニペットの仕様変更や測定ID更新等が発生した場合、88の公開HTMLファイルを手作業で編集するのではなく、本PRで整備した `tools/audit_html_ga4.py` などの自動化スクリプトを用いて一括適用・整合性検査を実施する運用とします。これにより更新漏れや表記揺れを防止します。

## 3. 本人除外（Pre-config Inline Exclusion）仕様

開発・管理作業によるアクセスが本番計測に混入することを防ぐため、`gtag('config')` を実行する**前**にインラインで除外判定を行います。

```html
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KPGJ0R2KXR"></script>
  <script>
    (function() {
      try {
        var url = new URL(window.location.href);
        var adminParam = url.searchParams.get('bantai_admin');
        if (adminParam === 'true') {
          localStorage.setItem('bantai_admin', 'true');
        } else if (adminParam === 'clear') {
          localStorage.removeItem('bantai_admin');
        }

        if (adminParam !== null) {
          url.searchParams.delete('bantai_admin');
          var cleanSearch = url.searchParams.toString();
          var newUrl = url.pathname + (cleanSearch ? '?' + cleanSearch : '') + url.hash;
          window.history.replaceState(null, '', newUrl);
        }
      } catch (e) {}

      var isLocal = window.location.hostname === 'localhost' ||
                    window.location.hostname === '127.0.0.1' ||
                    window.location.protocol === 'file:';
      var isExcluded = false;
      try {
        isExcluded = localStorage.getItem('bantai_admin') === 'true';
      } catch (e) {}

      if (isLocal || isExcluded) {
        window['ga-disable-G-KPGJ0R2KXR'] = true;
      }
    })();

    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-KPGJ0R2KXR');
  </script>
```

- **除外有効化**: `?bantai_admin=true` でアクセスすることで、ブラウザの `localStorage` にフラグが保存され恒久的に除外されます。
- **除外解除**: `?bantai_admin=clear` でアクセスすることでフラグが削除され、一時検証等が可能になります。
- **アドレスバーと履歴の即時消去**: `history.replaceState` により、`gtag('config')` 実行前にアドレスバーおよび閲覧履歴から `?bantai_admin=...` が安全に除去されます。これにより、ページ再読み込み時の意図しない再判定や、自動送信される `page_view` へのクエリ混入、URL共有時の誤送信を防止します。
- **ローカル環境の停止**: ホスト名が `localhost`, `127.0.0.1`, またはプロトコルが `file:` の場合は無条件で全通信が停止します。
- **クエリの非送信**: パラメータ `?bantai_admin=...` 自体はGA4へ送信されず完全に除去されます。

## 4. プライバシー保護・PIIサニタイズ仕様

- **URLサニタイズ**: 送信するURLからクエリパラメータ、URLハッシュ、個人情報（メールアドレス、電話番号等）を除去します。
- **連絡先除外**: `mailto:` リンクは `mailto:[redacted]`、`tel:` リンクは `tel:[redacted]` にマスキングされます。
- **フォーム入力値の非送信**: ユーザーの入力テキストや個人情報は一切GA4イベントパラメータに含めません。

## 5. 主要イベント仕様

### 5.1 サイト共通アクション (`assets/js/analytics-events.js`)

| イベント名 | パラメータ名 | 説明・トリガー条件 |
|---|---|---|
| `booth_click` | `item_name`, `product_name`, `link_url` | BOOTH（販売・配布ページ）リンクのクリック |
| `monitor_form_click` | `item_name`, `product_name`, `link_url` | モニター登録フォーム（Googleフォーム）リンクのクリック |
| `license_form_click` | `item_name`, `product_name`, `link_url` | ライセンス申請フォームリンクのクリック |
| `product_detail_click` | `item_name`, `product_name`, `link_url` | 製品画像・パネルからの詳細ページ遷移 |
| `database_nav_click` | `database_name`, `link_url` | 学校DB・大学DB・地域統計等のDB間遷移 |
| `contact_click` | `contact_type`, `link_url` | お問い合わせページまたはメールリンクのクリック |

### 5.2 コラム閲覧アクション (`assets/js/columns.js`)

| イベント名 | パラメータ名 | 判定基準・仕様 |
|---|---|---|
| `column_view` | `column_id`, `column_title`, `column_category` | コラムモーダルが開いた瞬間に送信 |
| `column_engagement` | `column_id`, `column_title`, `column_category`, `read_time_sec`, `duration_seconds`, `is_engaged`, `engagement_type` | モーダル終了、別記事切替、記事内リンク、離脱時に**1回だけ**送信 |
| `column_next_action` | `column_id`, `column_title`, `link_url`, `action_type` | 記事内の関連リンク等をクリックした際に送信 |

#### 滞在時間（閲覧時間）の判定基準
- **5秒未満**: 誤操作とみなし、`column_engagement` は**送信しない**。
- **5秒以上15秒未満**: `is_engaged: false`, `engagement_type: 'short_view'` として送信。
- **15秒以上**: `is_engaged: true`, `engagement_type: 'engaged_view'` として送信。
  - ※ 15秒以上は「**一定時間閲覧**」と定義し、完了と誤認させる表現は使用しません。

### 5.3 ファイルダウンロード（拡張計測機能の前提）

- **コード側の二重送信防止**: コード側での手動 `file_download` イベント送信は行いません。
- **GA4管理画面側の前提条件**: ファイルダウンロード（ZIP, EXE, PDF等）が自動収集されるには、GA4管理画面（管理 > データストリーム > ウェブストリームの詳細 > 拡張計測機能）において「**ファイルのダウンロード**」が有効になっている必要があります。

## 6. カスタム定義（必要最小限の確定一覧）

月次レポート「Ban.Tai 今月の状況」で実際に使用するカスタム定義（カスタムディメンション・カスタム指標）の一覧です。不要な定義は作成せず、以下の確定パラメータのみを登録します。

| 表示名 | イベントパラメータ名 | ディメンション/指標 | スコープ | 単位 | 使用するレポート |
|---|---|---|---|---|---|
| **製品名** | `product_name` | カスタムディメンション | イベント | なし | BOOTH・モニター移動集計 |
| **アイテム名** | `item_name` | カスタムディメンション | イベント | なし | 導線・アクション別詳細集計 |
| **コラムID** | `column_id` | カスタムディメンション | イベント | なし | コラム閲覧・一定時間閲覧集計 |
| **コラムタイトル** | `column_title` | カスタムディメンション | イベント | なし | コラム記事別レポート |
| **一定時間閲覧フラグ** | `is_engaged` | カスタムディメンション | イベント | なし | コラムエンゲージメント分析 |
| **DB名称** | `database_name` | カスタムディメンション | イベント | なし | データベース利用動向レポート |
| **コラム閲覧秒数** | `read_time_sec` | カスタム指標 | イベント | 秒 | 記事別の合計・平均閲覧時間 |
