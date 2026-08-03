#!/usr/bin/env python3
"""Compute land-adjacency between the 47 prefectures directly from MLIT's
国土数値情報 行政区域データ (N03), the same raw source used by
generate_prefecture_silhouettes.py (PR #96) — not from any third-party
website list. Run this (with data-source/n03-2026/ present) whenever
PREFECTURE_ADJACENCY in generate_seo_metadata.py needs re-verification.

Method:
  1. For each prefecture, dissolve all municipality-level polygons in its
     N03 GeoJSON into a single prefecture polygon (union_all).
  2. For every pair of prefectures, intersect their boundaries.
  3. Classify the intersection:
     - empty: not adjacent (includes cases separated by sea, even where a
       bridge/tunnel connects them — N03 polygons represent land area
       only, so a strait always leaves a real gap between the two
       polygons; a bridge/tunnel is not part of either prefecture's land
       area in this dataset).
     - a single Point / MultiPoint with total length 0: point-only
       contact. NOT counted as adjacent (a shared corner is not a shared
       border in the everyday sense used by the related-prefectures
       links).
     - any LineString/MultiLineString component with total length above
       MIN_BORDER_LENGTH_M (50m): adjacent candidate.
  4. Sea-strait islet filter: some adjacent candidates (e.g. across the
     Seto Inland Sea, where a Honshu-Shikoku bridge crosses many small
     islands) are technically-touching only because two small, mutually
     close islands happen to be administered by different prefectures —
     not because the prefectures share a continuous coastline. To catch
     this, cluster the intersection's line fragments spatially (union-find
     over a cKDTree neighbor query, CLUSTER_GAP_M gap) and require the
     LARGEST single cluster to reach MIN_DOMINANT_CLUSTER_LENGTH_M. Every
     confirmed genuine border in this dataset (even short ones, e.g.
     tochigi-saitama's 4.19km) clears this bar; the two known Seto Inland
     Sea false positives (hiroshima-ehime 0.1km max cluster, okayama-kagawa
     3.2km max cluster) do not.
  5. Adjacency is symmetric by construction (pairwise check, both
     directions recorded identically).

Prints a full report and writes prefecture_adjacency_ground_truth.json —
diff this against PREFECTURE_ADJACENCY in generate_seo_metadata.py; they
must match exactly (enforced by test_seo_metadata.py's
test_adjacency_matches_geospatial_ground_truth)."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "data-source" / "n03-2026"

PREFECTURES = [
    ("01", "hokkaido"), ("02", "aomori"), ("03", "iwate"), ("04", "miyagi"),
    ("05", "akita"), ("06", "yamagata"), ("07", "fukushima"), ("08", "ibaraki"),
    ("09", "tochigi"), ("10", "gunma"), ("11", "saitama"), ("12", "chiba"),
    ("13", "tokyo"), ("14", "kanagawa"), ("15", "niigata"), ("16", "toyama"),
    ("17", "ishikawa"), ("18", "fukui"), ("19", "yamanashi"), ("20", "nagano"),
    ("21", "gifu"), ("22", "shizuoka"), ("23", "aichi"), ("24", "mie"),
    ("25", "shiga"), ("26", "kyoto"), ("27", "osaka"), ("28", "hyogo"),
    ("29", "nara"), ("30", "wakayama"), ("31", "tottori"), ("32", "shimane"),
    ("33", "okayama"), ("34", "hiroshima"), ("35", "yamaguchi"), ("36", "tokushima"),
    ("37", "kagawa"), ("38", "ehime"), ("39", "kochi"), ("40", "fukuoka"),
    ("41", "saga"), ("42", "nagasaki"), ("43", "kumamoto"), ("44", "oita"),
    ("45", "miyazaki"), ("46", "kagoshima"), ("47", "okinawa"),
]

MIN_BORDER_LENGTH_M = 50.0
CLUSTER_GAP_M = 5000.0
# 実データにおける真正な最短国境(栃木県⇔埼玉県 4.19km)と、瀬戸内海を挟む
# 離島間接触の最大値(岡山県⇔香川県 3.2km)の間にある自然な境界。
MIN_DOMINANT_CLUSTER_LENGTH_M = 4000.0


def load_prefecture_polygon(code: str):
    zip_path = SOURCE_DIR / f"N03-20260101_{code}_GML.zip"
    with zipfile.ZipFile(zip_path) as z:
        with z.open(f"N03-20260101_{code}.geojson") as f:
            gdf = gpd.read_file(io.BytesIO(f.read()))
    gdf = gdf.set_crs(epsg=6668, allow_override=True).to_crs(epsg=3857)
    return gdf.union_all()


def line_fragments(inter):
    geoms = list(inter.geoms) if hasattr(inter, "geoms") else [inter]
    return [g for g in geoms if getattr(g, "length", 0.0) > 0]


def cluster_lengths(fragments, gap_m=CLUSTER_GAP_M):
    """Cluster line fragments by centroid proximity (union-find via a
    cKDTree radius query) and return each cluster's total length,
    descending. A genuine shared land border forms one dominant cluster
    (even split into thousands of tiny digitization fragments); scattered
    islet-to-islet touches across open water form several small,
    widely-separated clusters instead."""
    pts = np.array([[g.centroid.x, g.centroid.y] for g in fragments])
    n = len(pts)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for i, j in cKDTree(pts).query_pairs(r=gap_m):
        union(i, j)

    totals: dict[int, float] = {}
    for i in range(n):
        r = find(i)
        totals[r] = totals.get(r, 0.0) + fragments[i].length
    return sorted(totals.values(), reverse=True)


def main() -> None:
    polygons = {}
    for code, slug in PREFECTURES:
        polygons[slug] = load_prefecture_polygon(code)
        print(f"loaded {slug} ({code})")

    slugs = [slug for _, slug in PREFECTURES]
    adjacency: dict[str, list[str]] = {slug: [] for slug in slugs}
    line_lengths: dict[str, dict[str, float]] = {slug: {} for slug in slugs}
    rejected_sea_strait: list[dict] = []
    point_only_pairs: list[tuple[str, str]] = []

    for i, a in enumerate(slugs):
        for b in slugs[i + 1 :]:
            poly_a, poly_b = polygons[a], polygons[b]
            if not poly_a.intersects(poly_b):
                continue
            inter = poly_a.boundary.intersection(poly_b.boundary)
            fragments = line_fragments(inter)
            total_length = sum(f.length for f in fragments)

            if not fragments:
                point_only_pairs.append((a, b))
                continue
            if total_length < MIN_BORDER_LENGTH_M:
                point_only_pairs.append((a, b))
                continue

            clusters = cluster_lengths(fragments)
            if clusters[0] < MIN_DOMINANT_CLUSTER_LENGTH_M:
                rejected_sea_strait.append({
                    "a": a, "b": b, "total_length_m": total_length,
                    "cluster_lengths_m": clusters,
                })
                continue

            adjacency[a].append(b)
            adjacency[b].append(a)
            line_lengths[a][b] = total_length
            line_lengths[b][a] = total_length

    for slug in adjacency:
        adjacency[slug].sort()

    out_path = ROOT / "tools" / "school-database" / "prefecture_adjacency_ground_truth.json"
    out_path.write_text(json.dumps(adjacency, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== adjacency (border length in km) ===")
    for slug in slugs:
        neighbors = adjacency[slug]
        details = ", ".join(f"{n}({line_lengths[slug][n]/1000:.1f}km)" for n in neighbors)
        print(f"{slug} ({len(neighbors)}): {details}")

    print("\n=== rejected as sea-strait islet contact (no dominant cluster >= "
          f"{MIN_DOMINANT_CLUSTER_LENGTH_M/1000:.1f}km) ===")
    for r in rejected_sea_strait:
        print(f"  {r['a']}-{r['b']}: total={r['total_length_m']/1000:.2f}km, "
              f"clusters_km={[round(c/1000,2) for c in r['cluster_lengths_m']]}")

    print("\n=== point-only / below-threshold pairs (not counted as adjacent) ===")
    for a, b in point_only_pairs:
        print(f"  {a} - {b}")

    print(f"\nwrote: {out_path}")


if __name__ == "__main__":
    main()
