#!/usr/bin/env python3
"""Regression tests for required JSON and sitemap checks in weekly health audit."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "weekly_health_audit.py"
spec = importlib.util.spec_from_file_location("weekly_health_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class WeeklyHealthAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.patch = patch.object(audit, "ROOT", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        (self.root / "data" / "school-database").mkdir(parents=True)
        (self.root / "tools" / "university-database" / "music" / "data").mkdir(parents=True)
        (self.root / "sitemap.xml").write_text(
            '<?xml version="1.0"?><urlset><url><loc>https://example.org/</loc></url></urlset>',
            encoding="utf-8",
        )
        (self.root / "data" / "columns.json").write_text("[]", encoding="utf-8")
        (self.root / "data" / "products.json").write_text("[]", encoding="utf-8")
        (self.root / "tools" / "university-database" / "music" / "data" / "university_music_contests.json").write_text("[]", encoding="utf-8")
        for slug in audit_required_prefectures():
            (self.root / "data" / "school-database" / (slug + ".json")).write_text("{}", encoding="utf-8")

    def test_complete_core_passes(self):
        label, ok, msg = audit.check_json_and_sitemap()
        self.assertTrue(ok, msg)
        self.assertIn("50 JSON files", msg)

    def test_missing_core_json_fails(self):
        (self.root / "data" / "columns.json").unlink()
        _, ok, msg = audit.check_json_and_sitemap()
        self.assertFalse(ok)
        self.assertIn("data/columns.json", msg)

    def test_missing_prefecture_fails(self):
        (self.root / "data" / "school-database" / "tokyo.json").unlink()
        _, ok, msg = audit.check_json_and_sitemap()
        self.assertFalse(ok)
        self.assertIn("tokyo.json", msg)

    def test_invalid_extra_json_fails(self):
        (self.root / "data" / "school-database" / "other.json").write_text("{oops", encoding="utf-8")
        _, ok, msg = audit.check_json_and_sitemap()
        self.assertFalse(ok)
        self.assertIn("other.json", msg)

    def test_empty_sitemap_fails(self):
        (self.root / "sitemap.xml").write_text("<urlset/>", encoding="utf-8")
        _, ok, msg = audit.check_json_and_sitemap()
        self.assertFalse(ok)
        self.assertIn("no URLs", msg)


def audit_required_prefectures():
    return (
        "hokkaido aomori iwate miyagi akita yamagata fukushima "
        "ibaraki tochigi gunma saitama chiba tokyo kanagawa niigata "
        "toyama ishikawa fukui yamanashi nagano gifu shizuoka aichi "
        "mie shiga kyoto osaka hyogo nara wakayama tottori shimane "
        "okayama hiroshima yamaguchi tokushima kagawa ehime kochi "
        "fukuoka saga nagasaki kumamoto oita miyazaki kagoshima okinawa"
    ).split()


if __name__ == "__main__":
    unittest.main()
