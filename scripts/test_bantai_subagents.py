#!/usr/bin/env python3
"""Static policy checks for the first read-only Antigravity subagents."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
AGENTS = {
    "bantai-source-researcher",
    "bantai-record-integrator",
    "bantai-independent-verifier",
}
ALLOWED_TOOLS = {"view_file", "grep_search"}


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        raise ValueError("Missing YAML frontmatter")
    closing = text.find("\n---\n", 4)
    if closing < 0:
        raise ValueError("Missing closing YAML delimiter")
    lines = text[4:closing].splitlines()
    parsed = {}
    key = None
    for line in lines:
        if re.match(r"^[A-Za-z][A-Za-z0-9]*:", line):
            k, v = line.split(":", 1)
            key = k
            parsed[key] = [] if not v.strip() else v.strip()
        elif line.startswith("  - ") and key and isinstance(parsed[key], list):
            parsed[key].append(line[4:].strip())
        else:
            raise ValueError(f"Unexpected frontmatter: {line}")
    return parsed, text[closing + 5:]


class SubagentConfigTests(unittest.TestCase):
    def test_all_definitions_present_and_read_only(self):
        for name in AGENTS:
            with self.subTest(agent=name):
                path = ROOT / ".agents" / "agents" / f"{name}.md"
                self.assertTrue(path.is_file(), str(path))
                fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
                self.assertEqual(fm.get("name"), name)
                self.assertTrue(fm.get("description"))
                self.assertEqual(fm.get("subagent"), "true")
                self.assertEqual(fm.get("mainAgent"), "false")
                self.assertEqual(fm.get("commandExecutionPolicy"), "off")
                self.assertTrue(set(fm.get("tools", [])) <= ALLOWED_TOOLS)
                self.assertTrue(body.strip())

    def test_pilot_documentation_present(self):
        doc = ROOT / "docs" / "ANTIGRAVITY_SUBAGENTS_20261123.md"
        self.assertTrue(doc.is_file())
        text = doc.read_text(encoding="utf-8")
        for name in AGENTS:
            self.assertIn(name, text)
        self.assertIn("NOT VERIFIED", text)


if __name__ == "__main__":
    unittest.main()
