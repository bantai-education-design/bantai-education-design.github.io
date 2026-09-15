# Ban.Tai Education Design — 管理者・本人アクセス除外ガイド

## 1. 目的

本サイトの運営・更新・検証作業に伴う管理者自身のアクセスや操作が、GA4の本番計測データに混入することを防止するための設定ガイドです。

## 2. 正式仕様：URLパラメータによる本人除外操作

本サイトでは、`gtag('config')` が実行される直前にインラインスクリプトによって除外フラグを判定する仕組み（Pre-config Inline Exclusion）が組み込まれています。

| 操作目的 | 正式URLパラメータ | 内部動作 |
|---|---|---|
| **本人除外の有効化** | `?bantai_admin=true` | `localStorage.setItem('bantai_admin', 'true')` が実行され、除外フラグが恒久保持されます |
| **本人除外の解除** | `?bantai_admin=clear` | `localStorage.removeItem('bantai_admin')` が実行され、一般ユーザー状態に戻ります |

### 2.1 除外を有効にする手順（通常運用時）
管理者が使用するブラウザ（PC・スマートフォン）で以下のURLへアクセスします：
```text
https://bantai-education-design.github.io/?bantai_admin=true
```
- アクセスした瞬間にブラウザの `localStorage` にフラグが保存され、以降はトップページ以外のどのページを閲覧しても恒久的にGA4計測から除外されます。
- クエリパラメータ `?bantai_admin=true` 自体はスクリプトで即座に処理され、GA4の送信URLからはサニタイズ（除去）されるため計測データにクエリが残ることはありません。

> [!CAUTION]
> 除外解除URL（`?bantai_admin=clear`）は通常利用者へ案内・公開しないでください。

### 2.2 ローカル環境での自動停止
`localhost`, `127.0.0.1`, または `file:` プロトコルでページを開いた場合は、URLパラメータの有無に関わらず自動的に `window['ga-disable-G-KPGJ0R2KXR'] = true` が適用され、GA4への通信は一切発生しません。

## 3. 現在の除外状態を確認する方法

ブラウザの開発者ツール（F12）のコンソールで以下を実行します：

```javascript
// 1. GA4無効化フラグの確認（除外されていれば true）
window['ga-disable-G-KPGJ0R2KXR']

// 2. localStorage保持状態の確認（除外設定済みなら "true"）
localStorage.getItem('bantai_admin')
```

また、ネットワーク（Network）タブで `collect` を検索し、ページ読み込み時やボタンクリック時に `google-analytics.com` への通信が発生していないことでも確認できます。

## 4. DebugView確認時の一時的計測有効化と再除外手順

マージ後や検証時に、GA4管理画面の「DebugView」で新規イベントの着信を確認する場合は、次の手順で安全にテストを行います：

1. **除外を一時解除する**:
   ブラウザで `https://bantai-education-design.github.io/?bantai_admin=clear` にアクセスします。
2. **DebugViewで受信を確認する**:
   Chrome拡張機能「Google Analytics Debugger」をONにするか、通常ブラウザとして操作し、GA4管理画面（管理 > DebugView）でイベントがリアルタイム受信されることを確認します。
3. **作業終了後、直ちに再除外する**:
   確認作業が完了したら、速やかに `https://bantai-education-design.github.io/?bantai_admin=true` にアクセスし、本人除外状態へ復帰させます。
4. **復帰の確認**:
   コンソールで `window['ga-disable-G-KPGJ0R2KXR']` が `true` に戻ったことを確認します。

## 5. 補足：Google公式オプトアウトアドオン

PC用ブラウザ（Chrome, Edge, Firefox等）において、すべてのGoogle アナリティクス計測を一括停止したい場合は、Google公式の拡張機能も併用可能です。

- **Google アナリティクス オプトアウト アドオン**:
  [https://tools.google.com/dlpage/gaoptout](https://tools.google.com/dlpage/gaoptout)
