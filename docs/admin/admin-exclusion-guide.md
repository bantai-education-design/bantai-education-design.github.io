# Ban.Tai Education Design — 管理者・本人アクセス除外ガイド

## 1. 目的

本サイトの運営・更新・検証作業に伴う管理者自身のアクセスや操作が、GA4の本番計測データに混入することを防止するための設定ガイドです。

## 2. 実装済みの本人除外機能（Pre-config Inline Exclusion）

本サイトでは、`gtag('config')` が実行される直前にインラインスクリプトによって除外フラグを判定する仕組み（Pre-config Inline Exclusion）が組み込まれています。

### 2.1 URLパラメータによるワンクリック除外設定（推奨）

管理者が使用するブラウザで以下のURLへアクセスするだけで、そのブラウザの `localStorage` に除外フラグが恒久保存され、以降のアクセスがすべてGA4計測から除外されます。

- **本人除外を有効にする**:
  `https://bantai-education-design.github.io/?bantai_ga_disable=1`
  （アクセスすると `localStorage.getItem('bantai_ga_disable')` が `'true'` にセットされます）

- **本人除外を解除する（一般ユーザー状態に戻す）**:
  `https://bantai-education-design.github.io/?bantai_ga_disable=0`
  （アクセスすると `localStorage` から除外フラグが削除されます）

### 2.2 ローカル環境での自動停止
`localhost`, `127.0.0.1`, または `file:` プロトコルでページを開いた場合は、設定不要で自動的に `window['ga-disable-G-KPGJ0R2KXR'] = true` が適用され、GA4への通信は一切発生しません。

## 3. ブラウザでの設定確認方法

1. ブラウザでサイトを開き、`F12` キー（または右クリック > 「検証」）を押して開発者ツールを開きます。
2. **「Console（コンソール）」** タブを開きます。
3. 以下のコマンドを入力して Enter を押します：
   ```javascript
   window['ga-disable-G-KPGJ0R2KXR']
   ```
4. 結果として `true` が返ってくれば、正常に除外されています。
5. **「Network（ネットワーク）」** タブを開き、URLフィルタに `collect` と入力してページを再読み込みした際、`google-analytics.com` への通信リクエストが一切発生していないことを確認できます。

## 4. 補足：Google公式オプトアウトアドオン

PC用ブラウザ（Chrome, Edge, Firefox等）において、すべてのGoogle アナリティクス計測を一括停止したい場合は、Google公式の拡張機能も利用可能です。

- **Google アナリティクス オプトアウト アドオン**:
  [https://tools.google.com/dlpage/gaoptout](https://tools.google.com/dlpage/gaoptout)
