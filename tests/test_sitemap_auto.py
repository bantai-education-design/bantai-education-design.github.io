import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "update_sitemap_for_new_pages.py"
spec = importlib.util.spec_from_file_location("sitemap_auto", MODULE)
sitemap_auto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sitemap_auto)

EMPTY = ('<?xml version="1.0" encoding="UTF-8"?>\n'
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
         '</urlset>\n')

class SitemapAutoTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "sitemap.xml").write_text(EMPTY, encoding="utf-8")

    def page(self, group, slug, body=""):
        path = self.root / group / slug / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('<!doctype html><html><head>' + body + '</head><body>公開</body></html>', encoding="utf-8")
        return path

    def test_new_pages_are_added_once(self):
        self.page("books", "new-book")
        self.page("products", "new-app")
        self.page("columns", "new-column")
        sitemap = self.root / "sitemap.xml"
        self.assertEqual(sitemap_auto.generate(self.root, sitemap, False), 0)
        content = sitemap.read_text(encoding="utf-8")
        for path in ("/books/new-book/", "/products/new-app/", "/columns/new-column/"):
            self.assertEqual(content.count(path), 1)
        self.assertEqual(sitemap_auto.generate(self.root, sitemap, False), 0)
        self.assertEqual(sitemap.read_text(encoding="utf-8"), content)

    def test_noindex_page_not_added(self):
        self.page("books", "private", '<meta name="robots" content="noindex,follow">')
        self.assertEqual(sitemap_auto.missing_entries(self.root, self.root / "sitemap.xml"), [])

    def test_external_canonical_not_added(self):
        self.page("products", "redirect", '<link rel="canonical" href="https://elsewhere.example.com/">')
        self.assertEqual(sitemap_auto.missing_entries(self.root, self.root / "sitemap.xml"), [])

    def test_check_mode_does_not_write(self):
        self.page("books", "new")
        sitemap = self.root / "sitemap.xml"
        self.assertEqual(sitemap_auto.generate(self.root, sitemap, True), 2)
        self.assertEqual(sitemap.read_text(encoding="utf-8"), EMPTY)

if __name__ == "__main__":
    unittest.main()
