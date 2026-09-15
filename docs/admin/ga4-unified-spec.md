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

## 3. 本人除外（Pre-config Inline Exclusion）仕様

開発・管理作業によるアクセスが本番計測に混入することを防ぐため、`gtag('config')` を実行する**前**にインラインで除外判定を行います。

```javascript
(function() {
  try {
    var params = new URLSearchParams(window.location.search);
    if (params.get('bantai_ga_disable') === '1') {
      localStorage.setItem('bantai_ga_disable', 'true');
    } else if (params.get('bantai_ga_disable') === '0') {
      localStorage.removeItem('bantai_ga_disable');
    }
  } catch (e) {}

  var isLocal = window.location.hostname === 'localhost' ||
                window.location.hostname === '127.0.0.1' ||
                window.location.protocol === 'file:';
  var isExcluded = false;
  try {
    isExcluded = localStorage.getItem('bantai_ga_disable') === 'true';
  } catch (e) {}

  if (isLocal || isExcluded) {
    window['ga-disable-G-KPGJ0R2KXR'] = true;
  }
})();
```

- **ローカル環境の停止**: ホスト名が `localhost`, `127.0.0.1`, またはプロトコルが `file:` の場合は無条件で `window['ga-disable-G-KPGJ0R2KXR'] = true` が設定され、通信が発生しません。
- **管理者ブラウザの除外**: `localStorage` に `bantai_ga_disable = 'true'` がある場合も同様に全通信が停止します。
- **停止範囲**: 標準ページビュー、GA4拡張計測、およびJavaScriptによる独自イベント送信のすべてが停止します。

## 4. プライバシー保護・PIIサニタイズ仕様

- **URLサニタイズ**: 送信するURLからクエリパラメータ、URLハッシュ、個人情報（メールアドレス、電話番号等）を除去します。
- **連絡先除外**: `mailto:` リンクは `mailto:[redacted]`、`tel:` リンクは `tel:[redacted]` にマスキングされます。
- **フォーム入力値の非送信**: ユーザーの入力テキストや個人情報は一切GA4イベントパラメータに含めません。

## 5. 主要イベント仕様

### 5.1 サイト共通アクション (`assets/js/analytics-events.js`)

| イベント名 | パラメータ | トリガー条件 |
|---|---|---|
| `booth_click` | `item_name`, `product_name`, `link_url` | BOOTH（販売・配布ページ）リンクのクリック |
| `monitor_form_click` | `item_name`, `product_name`, `link_url` | モニター登録フォーム（Googleフォーム）リンクのクリック |
| `license_form_click` | `item_name`, `product_name`, `link_url` | ライセンス申請フォームリンクのクリック |
| `product_detail_click` | `item_name`, `product_name`, `link_url` | 製品画像・パネルからの詳細ページ遷移 |
| `database_nav_click` | `database_name`, `link_url` | 学校DB・大学DB・地域統計等のDB間遷移 |
| `contact_click` | `contact_type`, `link_url` | お問い合わせページまたはメールリンクのクリック |

※ **ファイルダウンロードに関する特記事項**:
ファイルダウンロード（ZIP, EXE, PDF等）はGA4標準の拡張計測機能（Enhanced Measurement）の `file_download` イベントで自動計測されるため、JavaScript側での手動イベント二重送信は行いません。

### 5.2 コラム閲覧アクション (`assets/js/columns.js`)

コラム（モーダル表示）の利用状況を正確に把握するため、以下の3イベントを送信します。

| イベント名 | パラメータ | 判定基準・仕様 |
|---|---|---|
| `column_view` | `column_id`, `column_title`, `column_category` | コラムモーダルが開いた瞬間に送信 |
| `column_engagement` | `column_id`, `column_title`, `column_category`, `duration_seconds`, `is_engaged`, `engagement_type` | モーダルを閉じる、別記事へ切り替える、記事内リンクを押す、ページを離脱する際に**1回だけ**送信 |
| `column_next_action` | `column_id`, `column_title`, `link_url`, `action_type` | 記事内の関連リンク等をクリックした際に送信 |

#### 滞在時間（閲覧時間）の判定基準
- **5秒未満**: 誤操作または即座の誤タップとみなし、`column_engagement` は**送信しない**。
- **5秒以上15秒未満**: `is_engaged: false`, `engagement_type: 'short_view'` として送信。
- **15秒以上**: `is_engaged: true`, `engagement_type: 'engaged_view'` として送信。
  - ※ 15秒以上は「**一定時間閲覧**」と定義し、完了と誤認させる表現は使用しません。
