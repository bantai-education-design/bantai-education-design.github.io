#!/usr/bin/env python3
"""Antigravity PreToolUse safety and editorial guard for Ban.Tai Education Design."""

import json
import re
import sys

PROTECTED_MARKER = "simple-public-flow.marker"
WRITE_TOOLS = frozenset({
    "write_file",
    "edit_file",
    "write_to_file",
    "replace_file_content",
    "multi_replace_file_content",
})
COMMAND_KEYS = ("CommandLine", "commandLine", "command")
PATH_KEYS = ("Path", "path", "TargetFile", "targetFile")
CONTENT_KEYS = (
    "Content",
    "content",
    "Replacement",
    "replacement",
    "CodeContent",
    "codeContent",
    "ReplacementContent",
    "replacementContent",
)
EDITORIAL_DIRS = ("/columns/", "/books/", "/book2/", "/drafts/")
EDITORIAL_EXTS = (".md", ".txt", ".html", ".htm")


def extract_written_text(args: dict) -> str:
    parts = []
    for key in CONTENT_KEYS:
        val = args.get(key)
        if isinstance(val, str):
            parts.append(val)
    chunks = args.get("ReplacementChunks") or args.get("replacementChunks")
    if isinstance(chunks, list):
        for chunk in chunks:
            if isinstance(chunk, dict):
                rc = chunk.get("ReplacementContent") or chunk.get("replacementContent")
                if isinstance(rc, str):
                    parts.append(rc)
    return "\n".join(parts)


def decide(event: dict) -> dict:
    call = event.get("toolCall")
    if not isinstance(call, dict) or not isinstance(call.get("args"), dict):
        return {"decision": "deny", "reason": "Invalid hook payload; cannot check safety."}

    name = str(call.get("name") or "")
    args = call["args"]

    if name == "run_command":
        command = next((args.get(k) for k in COMMAND_KEYS if isinstance(args.get(k), str)), "")
        if not command:
            return {"decision": "deny", "reason": "CommandLine missing; cannot inspect command."}
        if re.search(r"\bgh\s+pr\s+merge\b[^\r\n;|&]*--admin\b", command, re.I):
            return {"decision": "deny", "reason": "Ban.Tai policy: gh pr merge --admin is prohibited."}
        if re.search(
            r"\b(?:git\s+(?:add|rm|mv|restore|checkout)|(?:del|erase|rm|Remove-Item))\b[^\r\n;|&]*simple-public-flow\.marker\b",
            command,
            re.I,
        ):
            return {"decision": "deny", "reason": "Ban.Tai protected marker must not be changed."}
        if re.search(r"\bgit\s+push\b[^\r\n;|&]*\s(?:--force|-f)(?:\s|$)", command, re.I):
            return {"decision": "deny", "reason": "Force push requires separate human review."}
    elif name in WRITE_TOOLS:
        target = next((args.get(k) for k in PATH_KEYS if isinstance(args.get(k), str)), "")
        if not target:
            return {"decision": "deny", "reason": "File target missing; cannot check safety."}
        normalized = target.replace("\\", "/")
        if normalized.rstrip("/").endswith("/" + PROTECTED_MARKER) or normalized == PROTECTED_MARKER:
            return {"decision": "deny", "reason": "Ban.Tai protected marker must not be changed."}
        prefixed = "/" + normalized.lstrip("/").lower()
        if any(d in prefixed for d in EDITORIAL_DIRS) and prefixed.endswith(EDITORIAL_EXTS):
            if "**" in extract_written_text(args):
                return {"decision": "deny", "reason": "Editorial text contains forbidden ** markers."}

    return {"decision": "allow"}


def main() -> int:
    try:
        event = json.load(sys.stdin)
        result = decide(event) if isinstance(event, dict) else {"decision": "deny", "reason": "Invalid hook payload."}
    except (ValueError, TypeError) as exc:
        result = {"decision": "deny", "reason": f"Cannot parse hook payload: {exc}"}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
