#!/usr/bin/env python3
"""Focused unit tests for the Antigravity PreToolUse safety hook."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "bantai_guard.py"
spec = importlib.util.spec_from_file_location("bantai_guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def event(name, **args):
    return {"toolCall": {"name": name, "args": args}}


class GuardTests(unittest.TestCase):
    def test_normal_commands_allowed(self):
        for cmd in ("python -m unittest", "gh pr checks 123 --watch", "gh pr merge 123 --merge"):
            with self.subTest(cmd=cmd):
                self.assertEqual(guard.decide(event("run_command", CommandLine=cmd))["decision"], "allow")

    def test_admin_merge_denied(self):
        self.assertEqual(guard.decide(event("run_command", CommandLine="gh pr merge 15 --admin"))["decision"], "deny")

    def test_force_push_denied(self):
        self.assertEqual(guard.decide(event("run_command", CommandLine="git push origin main --force"))["decision"], "deny")

    def test_protected_marker_denied(self):
        for item in (
            event("write_to_file", TargetFile="simple-public-flow.marker", CodeContent="changed"),
            event("replace_file_content", TargetFile="C:/repo/simple-public-flow.marker", ReplacementContent="x"),
            event("run_command", CommandLine="git add simple-public-flow.marker"),
        ):
            with self.subTest(item=item):
                self.assertEqual(guard.decide(item)["decision"], "deny")

    def test_editorial_text_marker_denied(self):
        self.assertEqual(
            guard.decide(event("write_to_file", TargetFile="columns/example/article.md", CodeContent="This is **bold**"))["decision"],
            "deny",
        )

    def test_normal_editorial_text_allowed(self):
        self.assertEqual(
            guard.decide(event("write_to_file", TargetFile="columns/example/article.md", CodeContent="普通の日本語"))["decision"],
            "allow",
        )

    def test_missing_arguments_fail_closed(self):
        self.assertEqual(guard.decide({"toolCall": {"name": "run_command", "args": {}}})["decision"], "deny")


if __name__ == "__main__":
    unittest.main()
