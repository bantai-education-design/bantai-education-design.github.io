# Ban.Tai Long-Running Harness (Phase 4)

47都道府県を対象とした全国学校DB・音楽コンクール・研究指定校などの長時間調査を、中断・再開・重複防止・失敗時復旧つきで安全に実行するための進捗管理ハーネスです。

## 構成ファイル

- 実装: `tools/school-database/long_running_harness.py`
- 自動テスト: `scripts/test_long_running_harness.py`
- CIワークフロー: `.github/workflows/long-running-harness-tests.yml`

## 主な安全設計

1. 原子的な状態保存（Atomic Checkpointing）
   - 各都道府県の状態（`pending` / `in_progress` / `completed` / `failed` / `skipped`）、試行回数、出典URL、件数、検証ステータス（`PASS` / `FAIL` / `NOT VERIFIED`）を `state.json` に永続化します。
   - 一時ファイルへの書き込み・`fsync`・`os.replace` により、処理途中の強制終了でも `state.json` が破損しません。
2. 重複実行防止（Exclusive Lock & Idempotency）
   - `os.O_CREAT | os.O_EXCL` による `.lock` ファイルで同一ランの同時実行を拒否します。
   - 完了済み（`completed`）の都道府県は再開時に自動でスキップされ、再実行による重複処理を防ぎます。
   - 既存ランに対する `init` は `--resume` を明示しない限りエラーとし、誤上書きを防止します。
3. 中断・再開と失敗時復旧
   - 予期しない中断で `in_progress` のまま残った都道府県は `recover-stale` で安全に `pending` へ戻します（`completed` 済みの成果は維持）。
   - 一時的なネットワーク障害等で `failed` になった都道府県は、`next --retry-failed --max-attempts 3` で再試行し、成功時に `last_error` を自動クリアします。
4. 3役割Subagentsとの連携（Handoff）
   - `handoff --slug <pref>` により、`bantai-source-researcher` → `bantai-record-integrator` → `bantai-independent-verifier` へ渡す構造化JSONパケットを生成します。
   - `verification_status` の初期値は常に `NOT VERIFIED` とし、独立検証なしで `PASS` へ昇格させません。

## 基本的な使い方（実行例）

状態ファイルはリポジトリ外の作業ディレクトリまたは `.gitignore` 対象の `scratch/` 配下に保存し、公開リポジトリへ一時状態を混入させません。

```powershell
# 1. 47都道府県ランの初期化
python tools/school-database/long_running_harness.py --run-dir scratch/runs/research-2026 init --run-id research-2026 --job-name "令和8年度研究指定校調査"

# 2. 中断後の復旧（in_progress を pending に戻す）
python tools/school-database/long_running_harness.py --run-dir scratch/runs/research-2026 recover-stale

# 3. 次の未処理都道府県を取得して着手
python tools/school-database/long_running_harness.py --run-dir scratch/runs/research-2026 next

# 4. Subagents連携用パケット出力
python tools/school-database/long_running_harness.py --run-dir scratch/runs/research-2026 handoff --slug hokkaido

# 5. 完了記録（検証前は NOT VERIFIED のまま記録）
python tools/school-database/long_running_harness.py --run-dir scratch/runs/research-2026 complete --slug hokkaido --verification "NOT VERIFIED" --source-url "https://www.dokyoi.pref.hokkaido.lg.jp/"

# 6. 進捗確認
python tools/school-database/long_running_harness.py --run-dir scratch/runs/research-2026 status
```
