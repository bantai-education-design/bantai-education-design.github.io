#!/usr/bin/env python3
"""Live official audit for 2025 prefecture population movement.

Downloads the Statistics Bureau 2025 annual report PDF on every CI run and parses
Table 7 (incoming/outgoing/net counts) and Table 27 (movement rates/net rate).
All 47 prefectures are compared with the committed canonical JSON.
"""
from __future__ import annotations

import io
import json
import re
import unicodedata
from pathlib import Path

import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
MASTER_PATH = ROOT / "data" / "school-database" / "population-movement-2025.json"
PDF_URL = "https://www.stat.go.jp/data/idou/2025np/jissu/pdf/2025all.pdf"


def compact(v: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", v or ""))


def numbers(line: str) -> list[float]:
    vals = re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", unicodedata.normalize("NFKC", line))
    return [float(v.replace(",", "")) for v in vals]


def find_table_page(reader: PdfReader, marker: str, secondary: str) -> str:
    candidates = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        c = compact(text)
        if compact(marker) in c and compact(secondary) in c:
            candidates.append((idx, text))
    assert candidates, f"Official PDF table not found: {marker} / {secondary}"
    idx, text = candidates[-1]
    print(f"[Population Movement Live Audit] {marker} found on PDF page index {idx}")
    return text


def find_pref_line(text: str, name: str, minimum_numbers: int) -> list[float]:
    target = compact(name)
    lines = text.splitlines()
    for i, line in enumerate(lines):
        joined = line
        # Some PDF extractors split a prefecture name over adjacent text fragments.
        for extra in range(0, 3):
            if extra:
                if i + extra >= len(lines):
                    break
                joined += " " + lines[i + extra]
            if target not in compact(joined):
                continue
            vals = numbers(joined)
            if len(vals) >= minimum_numbers:
                return vals
    # Fallback: search a short window in the continuous text after whitespace normalization.
    raw = unicodedata.normalize("NFKC", text)
    pos = compact(raw).find(target)
    raise AssertionError(f"Could not parse row for {name}; normalized name present={pos >= 0}")


def fetch_live() -> tuple[dict[str, dict[str, float | int]], dict[str, float | int]]:
    r = requests.get(PDF_URL, timeout=90, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    assert r.content[:4] == b"%PDF", "Statistics Bureau live source is not a PDF"
    print(f"[Population Movement Live Audit] official PDF downloaded ({len(r.content):,} bytes)")
    reader = PdfReader(io.BytesIO(r.content))
    count_text = find_table_page(reader, "表7", "都道府県別転入者数")
    rate_text = find_table_page(reader, "表27", "転入超過率")

    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    live: dict[str, dict[str, float | int]] = {}
    for p in master["prefectures"]:
        name = p["prefecture_name"]
        cv = find_pref_line(count_text, name, 6)
        # Table 7 order: 2025 in, out, net; 2024 in, out, net.
        in_count, out_count, net_count = map(int, cv[:3])
        assert in_count - out_count == net_count, f"{name}: count identity failed {cv[:3]}"

        rv = find_pref_line(rate_text, name, 9)
        # Table 27: 2025/2024/diff for in-rate, out-rate, net-rate.
        net_rate = round(float(rv[6]), 2)
        live[name] = {
            "interpref_in_migrants": in_count,
            "interpref_out_migrants": out_count,
            "net_migration_2025": net_count,
            "net_migration_rate_2025": net_rate,
        }

    assert len(live) == 47
    national_counts = find_pref_line(count_text, "全国", 6)
    national_rates = find_pref_line(rate_text, "全国", 9)
    national = {
        "interpref_in_migrants": int(national_counts[0]),
        "interpref_out_migrants": int(national_counts[1]),
        "net_migration_2025": int(national_counts[2]),
        "net_migration_rate_2025": round(float(national_rates[6]), 2),
    }
    return live, national


def test_live_ground_truth() -> None:
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    assert len(master["prefectures"]) == 47
    live, national = fetch_live()
    assert national == master["national"], f"National mismatch: live={national} committed={master['national']}"
    for p in master["prefectures"]:
        name = p["prefecture_name"]
        expected = {k: p[k] for k in (
            "interpref_in_migrants", "interpref_out_migrants",
            "net_migration_2025", "net_migration_rate_2025",
        )}
        assert live[name] == expected, f"{name}: live={live[name]} committed={expected}"
    assert sum(p["interpref_in_migrants"] for p in master["prefectures"]) == 2515731
    assert sum(p["interpref_out_migrants"] for p in master["prefectures"]) == 2515731
    assert sum(p["net_migration_2025"] for p in master["prefectures"]) == 0


if __name__ == "__main__":
    test_live_ground_truth()
    print("ALL 47 PREFECTURES 2025 POPULATION MOVEMENT VALUES PASSED LIVE OFFICIAL GROUND TRUTH!")
