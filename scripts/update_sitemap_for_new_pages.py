#!/usr/bin/env python3
"""Published app, book and column pages → existing XML sitemap (additive only)."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

BASE = "https://bantai-education-design.github.io"
GROUPS = ("products", "books", "columns")
INDEX_GLOBS = tuple(f"{group}/*/index.html" for group in GROUPS)


def canonical_for(path: Path) -> str:
    return BASE + "/" + path.parent.as_posix().strip("/") + "/"


def page_is_eligible(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")[:32000]
    if re.search(r'<meta\s+[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', text, re.I):
        return False
    if re.search(r'<meta\s+[^>]*content=["\'][^"\']*noindex[^"\']*["\'][^>]*name=["\']robots', text, re.I):
        return False
    match = re.search(r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', text, re.I)
    if match:
        actual = urlsplit(match.group(1))
        expected = urlsplit(canonical_for(path))
        if actual.scheme not in ("http", "https") or actual.netloc != expected.netloc:
            return False
        if actual.path.rstrip("/") != expected.path.rstrip("/"):
            return False
    return True


def lastmod_for(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path)],
            check=True, text=True, capture_output=True
        )
        date = result.stdout.strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            return date
    except (OSError, subprocess.CalledProcessError):
        pass
    # Never claim today's date if source's modification date is unknown.
    return ""


def missing_entries(root: Path, sitemap: Path) -> list[tuple[str, str]]:
    raw = sitemap.read_text(encoding="utf-8")
    urlset = ET.fromstring(raw)
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    known = {(e.text or "").strip() for e in urlset.iter(ns + "loc")}
    missing = []
    for glob in INDEX_GLOBS:
        for path in sorted(root.glob(glob)):
            if not path.is_file() or not page_is_eligible(path.relative_to(root) if False else path):
                continue
            rel = path.relative_to(root)
            link = canonical_for(rel)
            if link in known:
                continue
            missing.append((link, lastmod_for(rel)))
            known.add(link)
    return sorted(missing)


def generate(root: Path, sitemap: Path, check: bool) -> int:
    missing = missing_entries(root, sitemap)
    if not missing:
        print("サイトマップに未登録の対象ページはありません")
        return 0
    print("サイトマップへの追加対象:", len(missing))
    for link, _ in missing:
        print("  ", link)
    if check:
        return 2
    current = sitemap.read_text(encoding="utf-8")
    if "</urlset>" not in current:
        raise ValueError("サイトマップ末尾の urlset がありません")
    chunks = []
    for loc, date in missing:
        date_element = f"\n    <lastmod>{escape(date)}</lastmod>" if date else ""
        chunks.append(f"  <url>\n    <loc>{escape(loc)}</loc>{date_element}\n  </url>\n")
    updated = current.replace("</urlset>", "".join(chunks) + "</urlset>", 1)
    ET.fromstring(updated)
    sitemap.write_text(updated, encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    sitemap = root / "sitemap.xml"
    return generate(root, sitemap, args.check)


if __name__ == "__main__":
    sys.exit(main())
