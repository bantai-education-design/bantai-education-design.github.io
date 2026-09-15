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
- アクセスした瞬間にブラウザの `localStorage` にフラグが保存され、`history.replaceState` によりアドレスバーおよび閲覧履歴から即座にクエリが除去されます。これにより、ページ再読み込み時の意図しない再処理や、URL共有時の誤送信、自動送信される `page_view` へのクエリ混入リスクが完全に防止されます。
- 以降はトップページ以外のどのページを閲覧しても恒久的にGA4計測から除外されます。

> [!CAUTION]
> 除外解除URL（`?bantai_admin=clear`）は通常利用者へ案内・公開しないでください。

### 2.2 ローカル環境での自動停止
`localhost`, `127.0.0.1`, または `file:` プロトコルでページを開いた場合は、URLパラメータの有無に関わらず自動的に `window['ga-disable-G-KPGJ0R2KXR'] = true` が適用され、GA4への通信は一切発生しません。

## 3. 本人除外の確認方法（リアルタイム確認を第一選択とする）

本人除外が正常に機能しているかの確認は、**GA4管理画面の「リアルタイム」レポートを確認することを第一選択**とします。短時間かつ確実にご自身のアクセスが除外されているかを検証できます。

### 3.1 手順 1：GA4リアルタイムレポートでの確認（推奨・第一選択）
1. 管理者のブラウザで `https://bantai-education-design.github.io/?bantai_admin=true` にアクセスします。
2. 別途、GA4管理画面（[Google アナリティクス](https://analytics.google.com/)）を開き、左メニューの「レポート」>「リアルタイム」を表示します。
3. サイト内の複数ページ（トップ、商品一覧、コラム等）を回遊します。
4. リアルタイムレポートの「過去30分間のユーザー」マップやカードにご自身のアクセスが反映されない（カウントが増加しない）ことを確認します。

### 3.2 手順 2：ブラウザ開発者ツール（F12）での確認（補助確認）
ブラウザの開発者ツール（F12）のコンソールで以下を実行して確認することも可能です：

```javascript
// 1. GA4無効化フラグの確認（除外されていれば true）
window['ga-disable-G-KPGJ0R2KXR']

// 2. localStorage保持状態の確認（除外設定済みなら "true"）
localStorage.getItem('bantai_admin')
```

また、ネットワーク（Network）タブで `collect` を検索し、ページ読み込み時やボタンクリック時に `google-analytics.com` への通信が発生していないことでも確認できます。

## 4. 詳細検証・DebugView使用時の手順（Tag Assistant / Debugger連携）

GA4管理画面の「DebugView」は、Chrome拡張機能「Google Analytics Debugger」または「Google Tag Assistant」連携が必要となる**詳細検証用の機能**です。新規イベントのパラメータ詳細や発火タイミングをテストしたい場合にのみ、以下の手順で利用します。

### 4.1 テスト手順
1. **本人除外を一時解除する**:
   ブラウザで `https://bantai-education-design.github.io/?bantai_admin=clear` にアクセスします（アドレスバーからクエリは自動消去されます）。
2. **デバッグツールを起動する**:
   - 方法A（推奨）: Chrome拡張機能「Google Analytics Debugger」をONにする。
   - 方法B: [Google Tag Assistant](https://tagassistant.google.com/) からサイトURLを入力してデバッグセッションを開始する。
3. **DebugViewで受信・パラメータを確認する**:
   GA4管理画面（管理 > データの表示 > DebugView）を開き、ページ遷移やボタンクリック（BOOTH、モニター、コラム閲覧等）を行ってイベントとパラメータがリアルタイム着信することを確認します。
4. **検証完了後、直ちに本人除外へ戻す**:
   テスト作業が完了したら、速やかに `https://bantai-education-design.github.io/?bantai_admin=true` にアクセスし、本人除外状態へ復帰させます。
5. **復帰の確認**:
   リアルタイムレポートまたはコンソールで `window['ga-disable-G-KPGJ0R2KXR'] === true` に戻ったことを確認します。

## 5. 補足：Google公式オプトアウトアドオン

PC用ブラウザ（Chrome, Edge, Firefox等）において、すべてのGoogle アナリティクス計測を一括停止したい場合は、Google公式の拡張機能も併用可能です。

- **Google アナリティクス オプトアウト アドオン**:
  [https://tools.google.com/dlpage/gaoptout](https://tools.google.com/dlpage/gaoptout)
