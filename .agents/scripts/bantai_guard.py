#!/usr/bin/env python3
"""Antigravity PreToolUse safety and editorial guard for Ban.Tai Education Design."""

import json
import re
import sys

PROTECTED_MARKER = "simple-public-flow.marker"

EDITORIAL_PATH_PATTERNS = (
    "/columns/",
    "/books/",
    "/book2/",
    "/drafts/",
    "/data/columns/",
)

EDITORIAL_EXTENSIONS = (".html", ".htm", ".md", ".txt", ".json")


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").lower()


def is_editorial_target(path: str) -> bool:
    norm = normalize_path(path)
    if not norm.endswith(EDITORIAL_EXTENSIONS):
        return False
    return any(pattern in norm for pattern in EDITORIAL_PATH_PATTERNS)


def check_run_command(args: dict) -> dict:
    cmd = str(args.get("CommandLine") or args.get("commandLine") or "")

    if re.search(r"\bgh\s+pr\s+merge\b", cmd) and re.search(r"(^|\s)--admin(\s|$)", cmd):
        return {
            "decision": "deny",
            "reason": (
                "Ban.Taiルール違反: gh pr merge に --admin は使用禁止です。"
                "全CIチェック通過後に通常マージ（gh pr merge <num> --merge --delete-branch）を実行してください。"
            ),
        }

    if PROTECTED_MARKER in cmd:
        return {
            "decision": "deny",
            "reason": (
                f"Ban.Taiルール違反: {PROTECTED_MARKER} への操作は禁止されています。"
            ),
        }

    return {"decision": "allow"}


def check_file_write(tool_name: str, args: dict) -> dict:
    path = str(args.get("Path") or args.get("path") or "")
    norm = normalize_path(path)

    if norm.endswith(PROTECTED_MARKER):
        return {
            "decision": "deny",
            "reason": (
                f"Ban.Taiルール違反: {PROTECTED_MARKER} は変更禁止です。"
            ),
        }

    if is_editorial_target(path):
        content = ""
        if tool_name == "write_file":
            content = str(args.get("Content") or args.get("content") or "")
        elif tool_name == "edit_file":
            content = str(args.get("Replacement") or args.get("replacement") or "")

        if "**" in content:
            return {
                "decision": "deny",
                "reason": (
                    "Ban.Tai執筆ルール違反: コラム・書籍・記事ファイル内にマークダウン太字記号(**)は使用禁止です。"
                    "プレーンな日本語、カギ括弧（「」）、または見出しタグで表現してください。"
                ),
            }

    return {"decision": "allow"}


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"decision": "allow"}, ensure_ascii=False))
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print(json.dumps({"decision": "allow"}, ensure_ascii=False))
        return 0

    tool_call = payload.get("toolCall") or {}
    tool_name = str(tool_call.get("name") or "")
    args = tool_call.get("args") or {}

    if tool_name == "run_command":
        result = check_run_command(args)
    elif tool_name in ("write_file", "edit_file"):
        result = check_file_write(tool_name, args)
    else:
        result = {"decision": "allow"}

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
