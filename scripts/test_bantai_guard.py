#!/usr/bin/env python3
"""Focused unit and end-to-end tests for the Antigravity PreToolUse safety hook."""
import importlib.util
import json
import shlex
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / ".agents"
SCRIPT = HOOKS_DIR / "scripts" / "bantai_guard.py"
spec = importlib.util.spec_from_file_location("bantai_guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def event(name, **args):
    return {"toolCall": {"name": name, "args": args}}


class GuardTests(unittest.TestCase):
    def test_hook_config_points_to_existing_script_relative_to_hooks_dir(self):
        """Antigravity runs hook commands with cwd set to the directory containing hooks.json (.agents/)."""
        hooks = json.loads((HOOKS_DIR / "hooks.json").read_text(encoding="utf-8"))
        for entry in hooks["bantai-guard"]["PreToolUse"]:
            for hook in entry["hooks"]:
                command = shlex.split(hook["command"])
                self.assertGreaterEqual(len(command), 2)
                self.assertTrue((HOOKS_DIR / command[1]).is_file(), hook["command"])

    def test_hook_command_end_to_end_from_hooks_dir(self):
        hooks = json.loads((HOOKS_DIR / "hooks.json").read_text(encoding="utf-8"))
        cmd = shlex.split(hooks["bantai-guard"]["PreToolUse"][0]["hooks"][0]["command"])

        deny_proc = subprocess.run(
            cmd,
            cwd=HOOKS_DIR,
            input=json.dumps(event("run_command", CommandLine="gh pr merge 15 --admin")),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(json.loads(deny_proc.stdout)["decision"], "deny")

        allow_proc = subprocess.run(
            cmd,
            cwd=HOOKS_DIR,
            input=json.dumps(event("run_command", CommandLine="gh pr merge 15 --merge --delete-branch")),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(json.loads(allow_proc.stdout)["decision"], "allow")

    def test_normal_commands_allowed(self):
        for cmd in (
            "python -m unittest",
            "gh pr checks 123 --watch",
            "gh pr merge 123 --merge",
            "Get-Content simple-public-flow.marker",
            "git status --short",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(guard.decide(event("run_command", CommandLine=cmd))["decision"], "allow")

    def test_admin_merge_and_bypasses_denied(self):
        for cmd in (
            "gh pr merge 15 --admin",
            'gh pr merge 15 "--admin"',
            "gh pr merge 15 --ad'min'",
            "gh pr merge 15 `\n --admin",
            "$flag = '--admin'; gh pr merge 15 $flag",
            "iex 'gh pr merge 15 --admin'",
            "Invoke-Expression 'gh pr merge 15'",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(guard.decide(event("run_command", CommandLine=cmd))["decision"], "deny")

    def test_force_push_and_bypasses_denied(self):
        for cmd in (
            "git push origin main --force",
            "git push origin main -f",
            "git push origin main --force-with-lease",
            "git push origin +main",
            "$f='--force'; git push origin main $f",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(guard.decide(event("run_command", CommandLine=cmd))["decision"], "deny")

    def test_protected_marker_mutations_denied(self):
        for item in (
            event("write_file", Path="simple-public-flow.marker", Content="changed"),
            event("edit_file", Path="C:/repo/simple-public-flow.marker", Replacement="x"),
            event("write_to_file", TargetFile="simple-public-flow.marker", CodeContent="changed"),
            event("replace_file_content", TargetFile="C:/repo/simple-public-flow.marker", ReplacementContent="x"),
            event("run_command", CommandLine="git add simple-public-flow.marker"),
            event("run_command", CommandLine="echo x > simple-public-flow.marker"),
            event("run_command", CommandLine="Set-Content -Path simple-public-flow.marker -Value x"),
            event("run_command", CommandLine="python -c \"open('simple-public-flow.marker','w').write('x')\""),
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
