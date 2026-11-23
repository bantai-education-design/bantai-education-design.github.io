#!/usr/bin/env python3
"""Antigravity PreToolUse safety gate. Reads one JSON event on stdin."""
import json
import re
import sys

COMMAND_KEYS = ("CommandLine", "command", "cmd")
WRITE_TOOLS = {"write_to_file", "replace_file_content", "multi_replace_file_content"}
PATH_KEYS = ("TargetFile", "path", "FilePath")
PROTECTED = "simple-public-flow.marker"


def decide(event):
    call = event.get("toolCall")
    if not isinstance(call, dict) or not isinstance(call.get("args"), dict):
        return {"decision": "deny", "reason": "Invalid hook payload; cannot check safety."}
    name = call.get("name", "")
    args = call["args"]
    if name == "run_command":
        command = next((args.get(key) for key in COMMAND_KEYS if isinstance(args.get(key), str)), "")
        if not command:
            return {"decision": "deny", "reason": "CommandLine missing; cannot inspect command."}
        # Check command invocations rather than a bare '--admin' used in comments or tests.
        if re.search(r"\bgh\s+pr\s+merge\b[^\r\n;|&]*--admin\b", command, re.I):
            return {"decision": "deny", "reason": "Ban.Tai policy: gh pr merge --admin is prohibited."}
        if re.search(r"\b(?:git\s+(?:add|rm|mv|restore|checkout)|(?:del|erase|rm|Remove-Item))\b[^\r\n;|&]*simple-public-flow\.marker\b", command, re.I):
            return {"decision": "deny", "reason": "Ban.Tai protected marker must not be changed."}
        if re.search(r"\b(?:git\s+push)\b[^\r\n;|&]*\s(?:--force|-f)(?:\s|$)", command, re.I):
            return {"decision": "deny", "reason": "Force push requires separate human review."}
    elif name in WRITE_TOOLS:
        target = next((args.get(key) for key in PATH_KEYS if isinstance(args.get(key), str)), "")
        if not target:
            return {"decision": "deny", "reason": "File target missing; cannot check safety."}
        if target.replace("\\", "/").rstrip("/").endswith("/" + PROTECTED) or target == PROTECTED:
            return {"decision": "deny", "reason": "Ban.Tai protected marker must not be changed."}
        normalized = target.replace("\\", "/")
        if (("/columns/" in "/" + normalized.lstrip("/") or "/books/" in "/" + normalized.lstrip("/"))
                and normalized.endswith((".md", ".txt"))
                and "**" in json.dumps(args, ensure_ascii=False)):
            return {"decision": "deny", "reason": "Editorial text contains forbidden ** markers."}
    return {"decision": "allow"}


def main():
    try:
        event = json.load(sys.stdin)
        result = decide(event) if isinstance(event, dict) else {"decision": "deny", "reason": "Invalid hook payload."}
    except (ValueError, TypeError) as exc:
        result = {"decision": "deny", "reason": f"Cannot parse hook payload: {exc}"}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
