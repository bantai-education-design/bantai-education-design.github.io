#!/usr/bin/env python3
"""Focused unit tests for the Antigravity PreToolUse safety hook."""
import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".agents" / "scripts" / "bantai_guard.py"
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
            event("write_file", Path="simple-public-flow.marker", Content="changed"),
            event("edit_file", Path="C:/repo/simple-public-flow.marker", Replacement="x"),
            event("write_to_file", TargetFile="simple-public-flow.marker", CodeContent="changed"),
            event("replace_file_content", TargetFile="C:/repo/simple-public-flow.marker", ReplacementContent="x"),
            event("run_command", CommandLine="git add simple-public-flow.marker"),
        ):
            with self.subTest(item=item):
                self.assertEqual(guard.decide(item)["decision"], "deny")

    def test_editorial_text_marker_denied(self):
        for item in (
            event("write_file", Path="columns/example/article.html", Content="<p>**bold**</p>"),
            event("edit_file", Path="books/book2/index.html", Replacement="<p>**強調**</p>"),
            event("write_to_file", TargetFile="columns/example/article.md", CodeContent="This is **bold**"),
        ):
            with self.subTest(item=item):
                self.assertEqual(guard.decide(item)["decision"], "deny")

    def test_normal_editorial_text_allowed(self):
        for item in (
            event("write_file", Path="columns/example/article.md", Content="普通の日本語"),
            event("write_to_file", TargetFile="columns/example/article.md", CodeContent="普通の日本語"),
        ):
            with self.subTest(item=item):
                self.assertEqual(guard.decide(item)["decision"], "allow")

    def test_missing_arguments_fail_closed(self):
        self.assertEqual(guard.decide({"toolCall": {"name": "run_command", "args": {}}})["decision"], "deny")


if __name__ == "__main__":
    unittest.main()
