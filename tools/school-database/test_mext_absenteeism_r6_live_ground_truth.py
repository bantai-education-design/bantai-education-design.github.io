#!/usr/bin/env python3
"""Live Ground Truth audit for MEXT FY2024 absenteeism table 4-15.

Downloads the official e-Stat workbook on every CI run, locates the 47-prefecture
国公私立 table mechanically, and compares all six published values per prefecture
with the committed canonical JSON. There is no proportional calibration or fallback.
"""
from __future__ import annotations

import io
import json
import re
import unicodedata
from pathlib import Path

import openpyxl
import requests

ROOT = Path(__file__).resolve().parents[2]
MASTER_PATH = ROOT / "data" / "school-database" / "mext-absenteeism-r6-ground-truth.json"
URL = "https://www.e-stat.go.jp/stat-search/file-download?fileKind=0&statInfId=000040366363"


def norm(v: object) -> str:
    if v is None:
        return ""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(v)))


def num(v: object) -> float | None:
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = norm(v).replace(",", "").replace("%", "")
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def metric_window(row_values: list[object], start_col: int) -> tuple[int, float, int, float, int, float] | None:
    values = [num(v) for v in row_values[start_col:]]
    values = [v for v in values if v is not None]
    for i in range(max(0, len(values) - 5)):
        a, b, c, d, e, f = values[i:i + 6]
        if not (a.is_integer() and c.is_integer() and e.is_integer()):
            continue
        if int(a) <= 0 or int(c) <= 0 or int(e) != int(a) + int(c):
            continue
        if not (0 <= b <= 200 and 0 <= d <= 200 and 0 <= f <= 200):
            continue
        return int(a), round(b, 1), int(c), round(d, 1), int(e), round(f, 1)
    return None


def fetch_live() -> tuple[dict[str, dict[str, float | int]], dict[str, float | int]]:
    r = requests.get(URL, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    assert r.content[:2] == b"PK", f"MEXT e-Stat payload is not XLSX: {r.headers.get('content-type')}"
    print(f"[MEXT Absenteeism Live Audit] workbook downloaded ({len(r.content):,} bytes)")
    wb = openpyxl.load_workbook(io.BytesIO(r.content), data_only=True)

    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    by_name = {p["prefecture_name"]: p for p in master["prefectures"]}
    names = set(by_name)
    best: tuple[int, dict[str, dict[str, float | int]], dict[str, float | int] | None, str] | None = None

    for ws in wb.worksheets:
        found: dict[str, dict[str, float | int]] = {}
        national = None
        for row in ws.iter_rows(values_only=True):
            cells = list(row)
            normalized = [norm(v) for v in cells]
            target_name = next((name for name in names if name in normalized), None)
            nat = "全国" in normalized
            if target_name is None and not nat:
                continue
            name_idx = normalized.index(target_name) if target_name else normalized.index("全国")
            metrics = metric_window(cells, name_idx + 1)
            if metrics is None:
                continue
            ecount, erate, jcount, jrate, ccount, crate = metrics
            rec = {
                "elem_absenteeism_count": ecount,
                "elem_absenteeism_rate": erate,
                "jhs_absenteeism_count": jcount,
                "jhs_absenteeism_rate": jrate,
                "absenteeism_combined_count": ccount,
                "absenteeism_combined_rate": crate,
            }
            if target_name:
                found[target_name] = rec
            elif nat:
                national = rec
        score = len(found)
        if best is None or score > best[0]:
            best = (score, found, national, ws.title)

    assert best is not None, "No MEXT absenteeism table candidate found"
    score, found, national, sheet_name = best
    assert score == 47, f"Expected 47 prefectures, found {score} on best sheet {sheet_name!r}"
    assert national is not None, f"National row not found on sheet {sheet_name!r}"
    print(f"[MEXT Absenteeism Live Audit] sheet={sheet_name!r}, prefectures=47")
    return found, national


def test_live_ground_truth() -> None:
    master = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    assert master["source"]["stat_inf_id"] == "000040366363"
    assert len(master["prefectures"]) == 47
    live, national = fetch_live()
    assert national == master["national"], f"National mismatch: live={national}, committed={master['national']}"
    for p in master["prefectures"]:
        name = p["prefecture_name"]
        expected = {k: p[k] for k in (
            "elem_absenteeism_count", "elem_absenteeism_rate",
            "jhs_absenteeism_count", "jhs_absenteeism_rate",
            "absenteeism_combined_count", "absenteeism_combined_rate",
        )}
        assert live[name] == expected, f"{name}: live={live[name]} committed={expected}"
    assert sum(p["elem_absenteeism_count"] for p in master["prefectures"]) == 137704
    assert sum(p["jhs_absenteeism_count"] for p in master["prefectures"]) == 216266
    assert sum(p["absenteeism_combined_count"] for p in master["prefectures"]) == 353970


if __name__ == "__main__":
    test_live_ground_truth()
    print("ALL 47 PREFECTURES MEXT R6 ABSENTEEISM VALUES PASSED LIVE OFFICIAL GROUND TRUTH!")
