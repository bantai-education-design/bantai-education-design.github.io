#!/usr/bin/env python3
"""Offline regression tests for conservative sampled URL audit."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import urllib.error

SCRIPT = Path(__file__).resolve().parent / "check_public_links.py"
spec = importlib.util.spec_from_file_location("check_public_links", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class PublicLinkTests(unittest.TestCase):
    def test_classification(self):
        for status in (200, 206, 301, 302):
            self.assertEqual(checker.classify_http(status), "OK")
        for status in (404, 410):
            self.assertEqual(checker.classify_http(status), "BROKEN")
        for status in (401, 403, 429, 500, 503):
            self.assertEqual(checker.classify_http(status), "UNKNOWN")

    def test_rotating_sample_and_priority(self):
        urls = [checker.ORIGIN + path for path in
                ["/", "/tools/school-database/", "/columns/", "/a", "/b", "/c", "/d"]]
        first = checker.choose_urls(urls, 5, 0)
        second = checker.choose_urls(urls, 5, 1)
        self.assertEqual(len(first), 5)
        self.assertEqual(len(set(first)), 5)
        self.assertIn(checker.ORIGIN + "/", first)
        self.assertNotEqual(first, second)

    def test_reject_external_origins_and_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sitemap.xml"
            path.write_text("<urlset><url><loc>https://example.org/</loc></url></urlset>")
            with self.assertRaises(ValueError):
                checker.sitemap_urls(path)
            path.write_text("<urlset><url><loc>" + checker.ORIGIN +
                            "/</loc></url><url><loc>" + checker.ORIGIN + "/</loc></url></urlset>")
            with self.assertRaises(ValueError):
                checker.sitemap_urls(path)

    def test_404_is_broken_but_403_unknown(self):
        for status, expected in [(404, "BROKEN"), (403, "UNKNOWN")]:
            error = urllib.error.HTTPError(checker.ORIGIN, status, "error", {}, None)
            with self.subTest(status=status), patch.object(checker.urllib.request, "urlopen", side_effect=error):
                self.assertEqual(checker.probe(checker.ORIGIN, attempts=1)[0], expected)

    def test_timeout_is_unknown(self):
        with patch.object(checker.urllib.request, "urlopen", side_effect=TimeoutError()):
            self.assertEqual(checker.probe(checker.ORIGIN, attempts=1)[0], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
