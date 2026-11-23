#!/usr/bin/env python3
"""Unit and CLI tests for the Ban.Tai 47-prefecture Long-Running Harness."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS_PATH = REPO_ROOT / "tools" / "school-database" / "long_running_harness.py"
spec = importlib.util.spec_from_file_location("long_running_harness", HARNESS_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class LongRunningHarnessTests(unittest.TestCase):
    def test_47_prefectures_match_existing_school_db_files(self):
        self.assertEqual(len(mod.PREFECTURES_47), 47)
        slugs = [s for s, _ in mod.PREFECTURES_47]
        self.assertEqual(len(slugs), len(set(slugs)))
        for slug in slugs:
            self.assertTrue(
                (REPO_ROOT / "data" / "school-database" / f"{slug}.json").is_file(),
                f"Missing school DB file for {slug}",
            )

    def test_interrupt_recover_and_resume_without_duplication(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = mod.LongRunningHarness(Path(tmp) / "run1")
            h.init_run(run_id="r1", job_name="research-2026")

            first = h.claim_next()
            self.assertEqual(first["slug"], "hokkaido")
            h.mark_completed(
                "hokkaido",
                verification_status="PASS",
                source_urls=["https://example.go.jp/hokkaido"],
                counts={"matched": 12, "unmatched": 0},
            )

            second = h.claim_next()
            self.assertEqual(second["slug"], "aomori")
            # Simulate abrupt interruption while aomori is in_progress
            recovered = h.recover_stale()
            self.assertEqual(recovered, ["aomori"])

            # Resume: hokkaido must not be re-claimed; aomori resumes cleanly
            resumed = h.claim_next()
            self.assertEqual(resumed["slug"], "aomori")
            self.assertEqual(resumed["attempts"], 2)

            summary = h.summary()
            self.assertEqual(summary["total"], 47)
            self.assertEqual(summary["statuses"]["completed"], 1)
            self.assertEqual(summary["statuses"]["in_progress"], 1)
            self.assertEqual(summary["verifications"]["PASS"], 1)
            self.assertEqual(summary["verifications"]["NOT VERIFIED"], 46)

    def test_duplicate_run_lock_prevents_concurrent_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            h1 = mod.LongRunningHarness(Path(tmp) / "run_lock")
            h2 = mod.LongRunningHarness(Path(tmp) / "run_lock")
            with h1.acquire_lock():
                with self.assertRaises(mod.RunLockError):
                    with h2.acquire_lock():
                        pass
            # After release, second acquire succeeds
            with h2.acquire_lock():
                pass

    def test_failure_and_retry_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = mod.LongRunningHarness(Path(tmp) / "run_retry")
            h.init_run(
                run_id="r2",
                job_name="retry-test",
                items=[("tokyo", "東京都"), ("osaka", "大阪府")],
            )
            item = h.claim_next()
            self.assertEqual(item["slug"], "tokyo")
            h.mark_failed("tokyo", error="HTTP 503 timeout")

            # Without retry_failed, moves on to osaka
            next_item = h.claim_next(retry_failed=False)
            self.assertEqual(next_item["slug"], "osaka")
            h.mark_completed("osaka", verification_status="NOT VERIFIED")

            # With retry_failed, retries tokyo and clears last_error on completion
            retry_item = h.claim_next(retry_failed=True, max_attempts=3)
            self.assertEqual(retry_item["slug"], "tokyo")
            self.assertEqual(retry_item["attempts"], 2)
            done = h.mark_completed("tokyo", verification_status="PASS")
            self.assertIsNone(done["last_error"])
            self.assertEqual(h.summary()["progress_pct"], 100.0)

    def test_init_is_protected_against_accidental_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = mod.LongRunningHarness(Path(tmp) / "run_idem")
            h.init_run(run_id="r3", job_name="idem-test")
            with self.assertRaises(mod.HarnessError):
                h.init_run(run_id="r3", job_name="idem-test", resume=False)
            state = h.init_run(run_id="r3", job_name="idem-test", resume=True)
            self.assertEqual(state["run_id"], "r3")

    def test_cli_end_to_end_and_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = str(Path(tmp) / "cli_run")
            base = [sys.executable, str(HARNESS_PATH), "--run-dir", run_dir]

            subprocess.run(base + ["init", "--run-id", "cli1", "--job-name", "music-2026"], check=True, capture_output=True)
            nxt = json.loads(subprocess.run(base + ["next"], check=True, capture_output=True, text=True).stdout)
            self.assertEqual(nxt["slug"], "hokkaido")

            handoff = json.loads(
                subprocess.run(base + ["handoff", "--slug", "hokkaido"], check=True, capture_output=True, text=True).stdout
            )
            self.assertEqual(handoff["target_db_file"], "data/school-database/hokkaido.json")
            self.assertEqual(
                handoff["pipeline"],
                ["bantai-source-researcher", "bantai-record-integrator", "bantai-independent-verifier"],
            )

            subprocess.run(
                base + ["complete", "--slug", "hokkaido", "--verification", "NOT VERIFIED", "--source-url", "https://example.jp"],
                check=True,
                capture_output=True,
            )
            st = json.loads(subprocess.run(base + ["status"], check=True, capture_output=True, text=True).stdout)
            self.assertEqual(st["statuses"]["completed"], 1)
            self.assertEqual(st["verifications"]["NOT VERIFIED"], 47)


if __name__ == "__main__":
    unittest.main()
