#!/usr/bin/env python3
"""Read-only weekly site health audit for Ban.Tai Education Design.

Validates JSON datasets, sitemap.xml well-formedness, SEO metadata, GA4 tags,
product catalog consistency, and Antigravity guard/subagent/harness test suites.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_step(label: str, cmd: list[str]) -> tuple[str, bool, str]:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    ok = proc.returncode == 0
    tail = (proc.stdout + "\n" + proc.stderr).strip().splitlines()
    summary = tail[-1] if tail else ("OK" if ok else f"exit {proc.returncode}")
    return label, ok, summary


def check_json_and_sitemap() -> tuple[str, bool, str]:
    errors: list[str] = []
    # Validate sitemap.xml
    try:
        tree = ET.parse(ROOT / "sitemap.xml")
        locs = [el.text.strip() for el in tree.getroot().iter() if el.tag.endswith("loc") and el.text]
        if not locs:
            errors.append("sitemap.xml contains no URLs")
        if len(locs) != len(set(locs)):
            errors.append(f"Duplicate <loc> entries in sitemap.xml ({len(locs)} total, {len(set(locs))} unique)")
    except Exception as exc:
        errors.append(f"sitemap.xml parse error: {exc}")

    # Validate core JSON files
    json_targets = [
        ROOT / "data" / "columns.json",
        ROOT / "data" / "products.json",
        ROOT / "tools" / "university-database" / "music" / "data" / "university_music_contests.json",
    ]
    school_db_dir = ROOT / "data" / "school-database"
    # Required prefecture records must not silently disappear.
    required_prefectures = (
        "hokkaido aomori iwate miyagi akita yamagata fukushima "
        "ibaraki tochigi gunma saitama chiba tokyo kanagawa niigata "
        "toyama ishikawa fukui yamanashi nagano gifu shizuoka aichi "
        "mie shiga kyoto osaka hyogo nara wakayama tottori shimane "
        "okayama hiroshima yamaguchi tokushima kagawa ehime kochi "
        "fukuoka saga nagasaki kumamoto oita miyazaki kagoshima okinawa"
    ).split()
    json_targets.extend(school_db_dir / f"{slug}.json" for slug in required_prefectures)
    json_targets.extend(sorted(school_db_dir.glob("*.json")))
    json_targets = list(dict.fromkeys(json_targets))

    checked = 0
    for path in json_targets:
        if not path.is_file():
            errors.append(f"Missing required JSON: {path.relative_to(ROOT)}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
            checked += 1
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")

    if errors:
        return "JSON & Sitemap Integrity", False, "; ".join(errors[:5])
    return "JSON & Sitemap Integrity", True, f"Validated {checked} JSON files and {len(locs)} sitemap URLs"


def main() -> int:
    results: list[tuple[str, bool, str]] = [check_json_and_sitemap()]

    commands = [
        ("School DB SEO Metadata", [sys.executable, "tools/school-database/test_seo_metadata.py"]),
        ("GA4 Tracking Guard", [sys.executable, "scripts/check_ga_tracking.py"]),
        ("Product Catalog Check", [sys.executable, "tools/check_products.py"]),
        ("Product Detail Check", [sys.executable, "tools/check_product_detail.py"]),
        ("Antigravity Guard & Subagent Tests", [sys.executable, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_bantai_*.py", "-v"]),
        ("Long-Running Harness Tests", [sys.executable, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_long_running_harness.py", "-v"]),
    ]

    for label, cmd in commands:
        results.append(run_step(label, cmd))

    lines = ["## Ban.Tai Weekly Site Health Audit", "", "| Check | Result | Detail |", "| :--- | :---: | :--- |"]
    all_ok = True
    for label, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        lines.append(f"| {label} | {status} | {detail} |")

    report = "\n".join(lines) + "\n"
    print(report)

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as fh:
            fh.write(report)

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
