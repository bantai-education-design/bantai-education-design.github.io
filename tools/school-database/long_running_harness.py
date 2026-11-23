#!/usr/bin/env python3
"""Long-Running Harness for Ban.Tai 47-prefecture database investigations.

Provides:
- Persistent per-prefecture checkpointing with atomic file writes
- Duplicate-run prevention via exclusive lockfiles
- Interrupt/resume and stale in-progress recovery
- Failure tracking with retry support
- Structured Subagent handoff packets (researcher -> integrator -> verifier)
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

SCHEMA_VERSION = "1.0"

PREFECTURES_47: tuple[tuple[str, str], ...] = (
    ("hokkaido", "北海道"),
    ("aomori", "青森県"),
    ("iwate", "岩手県"),
    ("miyagi", "宮城県"),
    ("akita", "秋田県"),
    ("yamagata", "山形県"),
    ("fukushima", "福島県"),
    ("ibaraki", "茨城県"),
    ("tochigi", "栃木県"),
    ("gunma", "群馬県"),
    ("saitama", "埼玉県"),
    ("chiba", "千葉県"),
    ("tokyo", "東京都"),
    ("kanagawa", "神奈川県"),
    ("niigata", "新潟県"),
    ("toyama", "富山県"),
    ("ishikawa", "石川県"),
    ("fukui", "福井県"),
    ("yamanashi", "山梨県"),
    ("nagano", "長野県"),
    ("gifu", "岐阜県"),
    ("shizuoka", "静岡県"),
    ("aichi", "愛知県"),
    ("mie", "三重県"),
    ("shiga", "滋賀県"),
    ("kyoto", "京都府"),
    ("osaka", "大阪府"),
    ("hyogo", "兵庫県"),
    ("nara", "奈良県"),
    ("wakayama", "和歌山県"),
    ("tottori", "鳥取県"),
    ("shimane", "島根県"),
    ("okayama", "岡山県"),
    ("hiroshima", "広島県"),
    ("yamaguchi", "山口県"),
    ("tokushima", "徳島県"),
    ("kagawa", "香川県"),
    ("ehime", "愛媛県"),
    ("kochi", "高知県"),
    ("fukuoka", "福岡県"),
    ("saga", "佐賀県"),
    ("nagasaki", "長崎県"),
    ("kumamoto", "熊本県"),
    ("oita", "大分県"),
    ("miyazaki", "宮崎県"),
    ("kagoshima", "鹿児島県"),
    ("okinawa", "沖縄県"),
)

VALID_STATUSES = frozenset({"pending", "in_progress", "completed", "failed", "skipped"})
VALID_VERIFICATIONS = frozenset({"PASS", "FAIL", "NOT VERIFIED"})


class RunLockError(RuntimeError):
    """Raised when another active process already holds the run lock."""


class HarnessError(RuntimeError):
    """Raised for invalid harness state transitions or missing runs."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    try:
        with tmp_path.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


class LongRunningHarness:
    """Manages persistent, resumable multi-prefecture investigation runs."""

    def __init__(self, run_dir: Path | str) -> None:
        self.run_dir = Path(run_dir)
        self.state_path = self.run_dir / "state.json"
        self.lock_path = self.run_dir / ".lock"

    @contextlib.contextmanager
    def acquire_lock(self, *, force_unlock: bool = False) -> Iterator[None]:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        if force_unlock and self.lock_path.exists():
            self.lock_path.unlink()

        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(self.lock_path), flags)
        except FileExistsError as exc:
            existing = ""
            try:
                existing = self.lock_path.read_text(encoding="utf-8").strip()
            except OSError:
                pass
            raise RunLockError(
                f"Run directory is already locked ({self.lock_path}): {existing}"
            ) from exc

        try:
            meta = json.dumps({"pid": os.getpid(), "acquired_at": utc_now()})
            os.write(fd, meta.encode("utf-8"))
            os.close(fd)
            yield
        finally:
            if self.lock_path.exists():
                try:
                    self.lock_path.unlink()
                except OSError:
                    pass

    def init_run(
        self,
        *,
        run_id: str,
        job_name: str,
        items: list[tuple[str, str]] | None = None,
        resume: bool = False,
    ) -> dict[str, Any]:
        if self.state_path.exists():
            if resume:
                return self.load_state()
            raise HarnessError(
                f"Run state already exists at {self.state_path}. Pass resume=True to continue."
            )

        targets = items if items is not None else list(PREFECTURES_47)
        now = utc_now()
        state: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "job_name": job_name,
            "created_at": now,
            "updated_at": now,
            "items": {
                slug: {
                    "slug": slug,
                    "name": name,
                    "status": "pending",
                    "attempts": 0,
                    "started_at": None,
                    "completed_at": None,
                    "verification_status": "NOT VERIFIED",
                    "source_urls": [],
                    "counts": {},
                    "last_error": None,
                    "notes": [],
                }
                for slug, name in targets
            },
            "order": [slug for slug, _ in targets],
        }
        atomic_write_json(self.state_path, state)
        return state

    def load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            raise HarnessError(f"Run state not found: {self.state_path}")
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def save_state(self, state: dict[str, Any]) -> None:
        state["updated_at"] = utc_now()
        atomic_write_json(self.state_path, state)

    def recover_stale(self) -> list[str]:
        """Reset any interrupted in_progress items back to pending without touching completed items."""
        state = self.load_state()
        recovered: list[str] = []
        now = utc_now()
        for slug in state["order"]:
            item = state["items"][slug]
            if item["status"] == "in_progress":
                item["status"] = "pending"
                item["notes"].append(f"Recovered from interrupted in_progress at {now}")
                recovered.append(slug)
        if recovered:
            self.save_state(state)
        return recovered

    def claim_next(self, *, retry_failed: bool = False, max_attempts: int = 3) -> dict[str, Any] | None:
        """Atomically claim the next pending (or retryable failed) prefecture."""
        state = self.load_state()
        eligible = {"pending"}
        if retry_failed:
            eligible.add("failed")

        for slug in state["order"]:
            item = state["items"][slug]
            if item["status"] not in eligible:
                continue
            if item["status"] == "failed" and item["attempts"] >= max_attempts:
                continue
            item["status"] = "in_progress"
            item["attempts"] += 1
            item["started_at"] = utc_now()
            self.save_state(state)
            return dict(item)
        return None

    def mark_completed(
        self,
        slug: str,
        *,
        verification_status: str = "NOT VERIFIED",
        source_urls: list[str] | None = None,
        counts: dict[str, Any] | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        if verification_status not in VALID_VERIFICATIONS:
            raise ValueError(f"Invalid verification_status: {verification_status}")

        state = self.load_state()
        if slug not in state["items"]:
            raise HarnessError(f"Unknown item slug: {slug}")

        item = state["items"][slug]
        item["status"] = "completed"
        item["completed_at"] = utc_now()
        item["verification_status"] = verification_status
        item["last_error"] = None
        if source_urls is not None:
            item["source_urls"] = list(dict.fromkeys(source_urls))
        if counts is not None:
            item["counts"] = dict(counts)
        if note:
            item["notes"].append(note)
        self.save_state(state)
        return dict(item)

    def mark_failed(self, slug: str, *, error: str) -> dict[str, Any]:
        state = self.load_state()
        if slug not in state["items"]:
            raise HarnessError(f"Unknown item slug: {slug}")

        item = state["items"][slug]
        item["status"] = "failed"
        item["last_error"] = error
        item["notes"].append(f"Failed at {utc_now()}: {error}")
        self.save_state(state)
        return dict(item)

    def summary(self) -> dict[str, Any]:
        state = self.load_state()
        counts = {s: 0 for s in VALID_STATUSES}
        verif = {v: 0 for v in VALID_VERIFICATIONS}
        for slug in state["order"]:
            item = state["items"][slug]
            counts[item["status"]] = counts.get(item["status"], 0) + 1
            verif[item["verification_status"]] = verif.get(item["verification_status"], 0) + 1
        total = len(state["order"])
        done = counts["completed"] + counts["skipped"]
        return {
            "run_id": state["run_id"],
            "job_name": state["job_name"],
            "total": total,
            "progress_pct": round((done / total) * 100, 1) if total else 0.0,
            "statuses": counts,
            "verifications": verif,
            "updated_at": state["updated_at"],
        }

    def build_subagent_handoff(self, slug: str) -> dict[str, Any]:
        state = self.load_state()
        if slug not in state["items"]:
            raise HarnessError(f"Unknown item slug: {slug}")
        item = state["items"][slug]
        return {
            "run_id": state["run_id"],
            "job_name": state["job_name"],
            "prefecture_slug": slug,
            "prefecture_name": item["name"],
            "target_db_file": f"data/school-database/{slug}.json",
            "current_status": item["status"],
            "attempts": item["attempts"],
            "pipeline": [
                "bantai-source-researcher",
                "bantai-record-integrator",
                "bantai-independent-verifier",
            ],
            "prior_sources": item["source_urls"],
            "verification_status": item["verification_status"],
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ban.Tai 47-prefecture Long-Running Harness CLI")
    parser.add_argument("--run-dir", required=True, help="Directory to store state.json and .lock")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize a 47-prefecture run")
    p_init.add_argument("--run-id", required=True)
    p_init.add_argument("--job-name", required=True)
    p_init.add_argument("--resume", action="store_true")

    p_next = sub.add_parser("next", help="Claim next pending prefecture")
    p_next.add_argument("--retry-failed", action="store_true")
    p_next.add_argument("--max-attempts", type=int, default=3)

    sub.add_parser("recover-stale", help="Reset interrupted in_progress items to pending")

    p_comp = sub.add_parser("complete", help="Mark prefecture completed")
    p_comp.add_argument("--slug", required=True)
    p_comp.add_argument("--verification", default="NOT VERIFIED", choices=sorted(VALID_VERIFICATIONS))
    p_comp.add_argument("--source-url", action="append", default=[])
    p_comp.add_argument("--counts-json", default="{}")
    p_comp.add_argument("--note", default=None)

    p_fail = sub.add_parser("fail", help="Mark prefecture failed")
    p_fail.add_argument("--slug", required=True)
    p_fail.add_argument("--error", required=True)

    sub.add_parser("status", help="Show run progress summary")

    p_handoff = sub.add_parser("handoff", help="Emit Subagent handoff packet JSON")
    p_handoff.add_argument("--slug", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    harness = LongRunningHarness(args.run_dir)

    if args.command == "status":
        print(json.dumps(harness.summary(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "handoff":
        print(json.dumps(harness.build_subagent_handoff(args.slug), ensure_ascii=False, indent=2))
        return 0

    with harness.acquire_lock():
        if args.command == "init":
            harness.init_run(run_id=args.run_id, job_name=args.job_name, resume=args.resume)
            print(json.dumps(harness.summary(), ensure_ascii=False, indent=2))
        elif args.command == "next":
            item = harness.claim_next(retry_failed=args.retry_failed, max_attempts=args.max_attempts)
            print(json.dumps(item, ensure_ascii=False, indent=2))
        elif args.command == "recover-stale":
            recovered = harness.recover_stale()
            print(json.dumps({"recovered": recovered}, ensure_ascii=False, indent=2))
        elif args.command == "complete":
            item = harness.mark_completed(
                args.slug,
                verification_status=args.verification,
                source_urls=args.source_url,
                counts=json.loads(args.counts_json),
                note=args.note,
            )
            print(json.dumps(item, ensure_ascii=False, indent=2))
        elif args.command == "fail":
            item = harness.mark_failed(args.slug, error=args.error)
            print(json.dumps(item, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
