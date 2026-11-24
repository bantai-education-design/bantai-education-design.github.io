#!/usr/bin/env python3
"""Conservative, sampled HTTP link check of Ban.Tai's public sitemap URLs.

Only 404 and 410 are definite failures. Rate limits, permission denials,
timeouts and server errors are UNKNOWN, never falsely labeled broken.
"""
from __future__ import annotations

import argparse
from datetime import date
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://bantai-education-design.github.io"
PRIORITY_PATHS = ("/", "/tools/school-database/", "/columns/", "/books/")


def sitemap_urls(path: Path) -> list[str]:
    root = ET.parse(path).getroot()
    urls = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "loc" or not element.text:
            continue
        url = element.text.strip()
        parts = urllib.parse.urlsplit(url)
        if parts.scheme != "https" or parts.netloc != "bantai-education-design.github.io":
            raise ValueError(f"Unexpected sitemap origin: {url}")
        urls.append(url)
    if not urls or len(urls) != len(set(urls)):
        raise ValueError("Sitemap empty or duplicated")
    return urls


def choose_urls(urls: list[str], limit: int, week: int) -> list[str]:
    if limit < 1:
        raise ValueError("limit must be positive")
    important = [url for path in PRIORITY_PATHS for url in urls
                 if urllib.parse.urlsplit(url).path == path]
    important = list(dict.fromkeys(important))[:limit]
    others = sorted(set(urls) - set(important))
    remaining = limit - len(important)
    if not others or not remaining:
        return important
    start = (week * remaining) % len(others)
    selected = [others[(start + i) % len(others)] for i in range(min(remaining, len(others)))]
    return important + selected


def classify_http(status: int) -> str:
    if status in (404, 410):
        return "BROKEN"
    if 200 <= status < 400:
        return "OK"
    return "UNKNOWN"


def probe(url: str, timeout: float = 8, attempts: int = 2) -> tuple[str, str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "BanTai-Site-Health-Audit/1.0 (+public sitemap sampling)",
                 "Range": "bytes=0-0"},
        method="GET",
    )
    last = ("UNKNOWN", "not attempted")
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return classify_http(response.status), str(response.status)
        except urllib.error.HTTPError as exc:
            result = classify_http(exc.code)
            last = (result, f"HTTP {exc.code}")
            if result == "BROKEN" or exc.code in (401, 403, 429):
                return last
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = ("UNKNOWN", type(exc).__name__)
        if attempt + 1 < attempts:
            time.sleep(1)
    return last


def main() -> int:
    parser = argparse.ArgumentParser(description="Sampled live sitemap URL check")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--week", type=int, default=date.today().isocalendar().week)
    parser.add_argument("--timeout", type=float, default=8)
    parser.add_argument("--all", action="store_true", help="Explicit full check, may be slow")
    args = parser.parse_args()
    try:
        urls = sitemap_urls(ROOT / "sitemap.xml")
        selected = urls if args.all else choose_urls(urls, args.limit, args.week)
    except (ValueError, ET.ParseError, OSError) as exc:
        print(f"FAIL: cannot inspect sitemap: {exc}")
        return 1
    records = []
    for url in selected:
        state, detail = probe(url, timeout=args.timeout)
        records.append((state, url, detail))
    counts = {key: sum(r[0] == key for r in records) for key in ("OK", "BROKEN", "UNKNOWN")}
    summary = (f"Checked {len(selected)}/{len(urls)} sitemap URLs: "
               f"OK={counts['OK']}, BROKEN={counts['BROKEN']}, UNKNOWN={counts['UNKNOWN']}")
    print(summary)
    for state, url, detail in records:
        if state != "OK":
            print(f"{state}: {url} ({detail})")
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as stream:
            stream.write("### Ban.Tai public link audit\n\n" + summary + "\n\n")
            for state, url, detail in records:
                if state != "OK":
                    stream.write(f"- {state}: {url} ({detail})\n")
    # Network outages and access restrictions are inconclusive, not broken links.
    return 1 if counts["BROKEN"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
