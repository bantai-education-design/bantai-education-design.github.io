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

MARKER_MUTATION_RE = re.compile(
    r"(?:"
    r">>?"
    r"|\b(?:git\s+(?:add|rm|mv|restore|checkout|reset)|del|erase|rm|mv|cp|tee|touch|sed|truncate)"
    r"|\b(?:Set-Content|Add-Content|Out-File|New-Item|Remove-Item|Move-Item|Copy-Item|Clear-Content|Rename-Item)"
    r"|\b(?:python|python3|py|node|pwsh|powershell|cmd|bash|sh)\b"
    r")",
    re.I,
)


def normalize_command(command: str) -> str:
    """Collapse line continuations and strip simple quote/backtick obfuscation."""
    # Join shell/PowerShell line continuations (\ or ` followed by newline)
    collapsed = re.sub(r"[\\`]\r?\n", " ", command)
    # Strip quotes and PowerShell escape backticks inside tokens (e.g. "--ad"min, `--admin)
    dequoted = re.sub(r"[\"'`]", "", collapsed)
    return dequoted


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


def check_command_segment(segment: str) -> dict | None:
    if re.search(r"\bgh\s+pr\s+merge\b.*--admin\b", segment, re.I):
        return {"decision": "deny", "reason": "Ban.Tai policy: gh pr merge --admin is prohibited."}
    if re.search(r"\b(?:iex|Invoke-Expression|eval)\b", segment, re.I) and re.search(
        r"\b(?:gh|git|admin|force|simple-public-flow\.marker)\b", segment, re.I
    ):
        return {
            "decision": "deny",
            "reason": "Ban.Tai policy: dynamic shell evaluation (iex/Invoke-Expression/eval) with git/gh/protected targets is prohibited.",
        }
    if re.search(r"simple-public-flow\.marker", segment, re.I) and MARKER_MUTATION_RE.search(segment):
        return {"decision": "deny", "reason": "Ban.Tai protected marker must not be changed."}
    if re.search(r"\bgit\s+push\b.*(?:\s(?:--force|-f|--force-with-lease)(?:\s|$)|\s\+[^\s]+)", segment, re.I):
        return {"decision": "deny", "reason": "Force push requires separate human review."}
    return None


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
        norm = normalize_command(command)
        # Check each chained command segment (;, &&, ||, |, newline)
        for seg in re.split(r"[\r\n;|&]+", norm):
            seg = seg.strip()
            if not seg:
                continue
            verdict = check_command_segment(seg)
            if verdict is not None:
                return verdict
        # Cross-segment variable splitting bypass (e.g. $flag='--admin'; gh pr merge 1 $flag)
        if re.search(r"\bgh\s+pr\s+merge\b", norm, re.I) and re.search(r"--admin\b", norm, re.I):
            return {"decision": "deny", "reason": "Ban.Tai policy: split/variable --admin with gh pr merge is prohibited."}
        if re.search(r"\bgit\s+push\b", norm, re.I) and re.search(r"(?:--force|--force-with-lease)\b", norm, re.I):
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
