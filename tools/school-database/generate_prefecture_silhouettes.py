#!/usr/bin/env python3
"""Generate 47 prefecture "silhouette" SVGs from MLIT's 国土数値情報
行政区域データ (N03, administrative area boundaries).

This is NOT a reproduction of any prefectural crest, flag, or official
symbol. It is Ban.Tai's own derived "prefecture silhouette" mark: the
outline shape of each prefecture's administrative area, dissolved from
thousands of municipality-level polygons and simplified for small-icon
display.

Source: 国土数値情報 行政区域データ（N03）, 国土交通省国土地理院・総務省
Reference date: 2026-01-01
License: 政府標準利用規約に基づく二次利用（複製・翻案・商用利用可、CC BY 4.0
互換）。出典表記が必要（本スクリプトが生成するSVGを使う画面側で別途表示する）。
https://nlftp.mlit.go.jp/ksj/other/agreement_01.html

Input: data-source/n03-2026/N03-20260101_{code}_GML.zip (not committed to
git — see docs/school-database/prefecture-silhouettes-source-manifest.md
for the download URLs, reference date, and per-file SHA-256 so the exact
input can be re-fetched and verified).

Method: the raw shapefile represents each prefecture as thousands of
disjoint polygons (one per contiguous parcel/settlement fragment; adjacent
municipality borders do not share exact vertices, so a plain vector
unary_union leaves ~9,000+ "islands" that are mostly floating-point gap
artifacts, not real islands). Rather than trying to vector-snap thousands
of near-touching edges, this script rasterizes all polygons onto a grid,
closes small gaps and removes sub-pixel noise with binary morphology, then
traces the resulting silhouette back into vector contours. This is robust
to gap size and naturally distinguishes genuine islands (multiple
pixels wide) from digitization noise (isolated single pixels).
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "data-source" / "n03-2026"
OUTPUT_DIR = ROOT / "assets" / "images" / "prefecture-silhouettes"

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

# 東京都のみ特例: 本土（23区部・多摩地域）だけを抽出する。
# 東京都の行政区域は本土から沖ノ鳥島まで約2,000km四方に及び、島しょ部を
# 含めた全域をシルエット化すると32px表示で本土が判別不能になるため、
# カード上での識別性を優先し、23区部・多摩地域のみを対象とする（伊豆
# 諸島・小笠原諸島・沖ノ鳥島・南鳥島は含まない）。他の46都道府県には
# この特例は適用しない。
# 行政コード（N03_007）は次の通り確認済み（data-source/n03-2026/
# N03-20260101_13_GML.zipのN03-20260101_13.geojsonを実際に読み取って
# 確認、13000=所属未定地は対象外とした）。
TOKYO_MAINLAND_CODES = frozenset(
    [
        # 23区部
        "13101", "13102", "13103", "13104", "13105", "13106", "13107", "13108",
        "13109", "13110", "13111", "13112", "13113", "13114", "13115", "13116",
        "13117", "13118", "13119", "13120", "13121", "13122", "13123",
        # 多摩地域（市）
        "13201", "13202", "13203", "13204", "13205", "13206", "13207", "13208",
        "13209", "13210", "13211", "13212", "13213", "13214", "13215", "13218",
        "13219", "13220", "13221", "13222", "13223", "13224", "13225", "13227",
        "13228", "13229",
        # 多摩地域（西多摩郡の町村）
        "13303", "13305", "13307", "13308",
    ]
)

PROJECTED_CRS = "EPSG:3857"  # メートル単位。アイコン用シルエットのため単純な投影で十分。

RASTER_LONG_SIDE = 700  # 長辺のピクセル数。この解像度でラスタ化してから輪郭抽出する。
CLOSING_ITERATIONS = 2  # 隣接する市区町村間の微小な隙間を埋める（膨張→収縮）。
OPENING_ITERATIONS = 1  # 1px以下の孤立ノイズ（データ上の点状アーティファクト）だけを除去する。
CONTOUR_SIMPLIFY_TOLERANCE_PX = 1.2  # 輪郭の簡略化許容誤差（ピクセル単位）。
PADDING_FRACTION = 0.04
COORD_PRECISION = 1


def load_prefecture_polygons(code: str) -> list:
    zip_path = SOURCE_DIR / f"N03-20260101_{code}_GML.zip"
    if not zip_path.is_file():
        raise FileNotFoundError(f"{zip_path} が見つかりません（先にダウンロードしてください）")

    shp_members = [f"N03-20260101_{code}{ext}" for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg")]

    with zipfile.ZipFile(zip_path) as zf:
        extract_dir = SOURCE_DIR / "_extract" / code
        extract_dir.mkdir(parents=True, exist_ok=True)
        for member in shp_members:
            if member not in zf.namelist():
                raise ValueError(f"{zip_path} 内に {member} がありません")
            zf.extract(member, extract_dir)

    gdf = gpd.read_file(extract_dir / f"N03-20260101_{code}.shp")
    if gdf.empty:
        raise ValueError(f"{code}: シェープファイルにレコードがありません")

    admin_code = gdf["N03_007"].astype(str).str[:2]
    if not (admin_code == code).all():
        bad = sorted(set(admin_code) - {code})
        raise ValueError(f"{code}: 想定外の都道府県コードが混入しています: {bad}")

    if code == "13":
        full_code = gdf["N03_007"].astype(str)
        gdf = gdf[full_code.isin(TOKYO_MAINLAND_CODES)]
        if gdf.empty:
            raise ValueError("13: 東京都本土フィルタ適用後にレコードが0件になりました")
        found_codes = set(full_code[full_code.isin(TOKYO_MAINLAND_CODES)])
        missing = TOKYO_MAINLAND_CODES - found_codes
        if missing:
            raise ValueError(f"13: 東京都本土の行政コードが原本に見つかりません: {sorted(missing)}")

    gdf = gdf.to_crs(PROJECTED_CRS)

    polygons = []
    for geom in gdf.geometry:
        if geom is None or geom.is_empty:
            continue
        if geom.geom_type == "Polygon":
            polygons.append(geom)
        elif geom.geom_type == "MultiPolygon":
            polygons.extend(geom.geoms)
    if not polygons:
        raise ValueError(f"{code}: 有効なポリゴンがありません")
    return polygons


def rasterize(polygons: list, code: str) -> tuple:
    minx = min(p.bounds[0] for p in polygons)
    miny = min(p.bounds[1] for p in polygons)
    maxx = max(p.bounds[2] for p in polygons)
    maxy = max(p.bounds[3] for p in polygons)
    width_m = maxx - minx
    height_m = maxy - miny
    if width_m <= 0 or height_m <= 0:
        raise ValueError(f"{code}: 不正な外接矩形です")

    if width_m >= height_m:
        px_w = RASTER_LONG_SIDE
        px_h = max(int(round(RASTER_LONG_SIDE * height_m / width_m)), 1)
    else:
        px_h = RASTER_LONG_SIDE
        px_w = max(int(round(RASTER_LONG_SIDE * width_m / height_m)), 1)

    scale_x = px_w / width_m
    scale_y = px_h / height_m

    def geo_to_px(x: float, y: float) -> tuple[float, float]:
        col = (x - minx) * scale_x
        row = (maxy - y) * scale_y  # 北(y大)がrow=0（上）になるよう反転
        return (col, row)

    img = Image.new("1", (px_w, px_h), 0)
    draw = ImageDraw.Draw(img)
    for polygon in polygons:
        pts = [geo_to_px(x, y) for x, y in polygon.exterior.coords]
        if len(pts) >= 3:
            draw.polygon(pts, fill=1)

    mask = np.array(img, dtype=bool)
    transform_params = (minx, miny, maxx, maxy, scale_x, scale_y, px_w, px_h)
    return mask, transform_params


def clean_mask(mask: np.ndarray) -> np.ndarray:
    structure = ndimage.generate_binary_structure(2, 2)  # 8近傍
    closed = ndimage.binary_closing(mask, structure=structure, iterations=CLOSING_ITERATIONS)
    filled = ndimage.binary_fill_holes(closed)
    opened = ndimage.binary_opening(filled, structure=structure, iterations=OPENING_ITERATIONS)
    return opened


def mask_to_polygons(mask: np.ndarray) -> list[Polygon]:
    from skimage import measure

    labeled, num = ndimage.label(mask, structure=ndimage.generate_binary_structure(2, 2))
    polygons = []
    for label_id in range(1, num + 1):
        component = labeled == label_id
        if component.sum() < 2:
            continue
        # パディングしてfind_contoursが境界で切れないようにする。
        padded = np.pad(component, 1, mode="constant", constant_values=False)
        contours = measure.find_contours(padded.astype(float), level=0.5)
        if not contours:
            continue
        # 最大の輪郭（外周）を採用する。
        contour = max(contours, key=len)
        contour = contour - 1  # パディング分を戻す
        coords = [(c, r) for r, c in contour]  # (row,col)->(x=col, y=row)
        if len(coords) < 3:
            continue
        poly = Polygon(coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty:
            continue
        simplified = poly.simplify(CONTOUR_SIMPLIFY_TOLERANCE_PX, preserve_topology=True)
        if simplified.is_empty or simplified.geom_type != "Polygon":
            simplified = poly
        polygons.append(simplified)

    polygons.sort(key=lambda p: (round(p.bounds[0], 2), round(p.bounds[1], 2)))
    return polygons


def polygons_to_svg(polygons: list[Polygon], px_w: int, px_h: int) -> str:
    all_x = [x for p in polygons for x in p.exterior.xy[0]]
    all_y = [y for p in polygons for y in p.exterior.xy[1]]
    minx, maxx = min(all_x), max(all_x)
    miny, maxy = min(all_y), max(all_y)
    width = maxx - minx
    height = maxy - miny
    diagonal = (width**2 + height**2) ** 0.5
    pad = max(diagonal * PADDING_FRACTION, 1.0)

    view_minx = minx - pad
    view_miny = miny - pad
    view_width = width + 2 * pad
    view_height = height + 2 * pad

    def fmt_ring(coords) -> str:
        pts = [(x - view_minx, y - view_miny) for x, y in coords]
        d = f"M{pts[0][0]:.{COORD_PRECISION}f},{pts[0][1]:.{COORD_PRECISION}f}"
        for x, y in pts[1:]:
            d += f"L{x:.{COORD_PRECISION}f},{y:.{COORD_PRECISION}f}"
        d += "Z"
        return d

    path_d = " ".join(fmt_ring(p.exterior.coords) for p in polygons)
    view_box = f"0 0 {view_width:.{COORD_PRECISION}f} {view_height:.{COORD_PRECISION}f}"

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{view_box}" role="img" aria-hidden="true">'
        f'<path d="{path_d}" fill="#c5a059" fill-rule="nonzero"/>'
        "</svg>\n"
    )


def generate_one(code: str, slug: str) -> dict:
    raw_polygons = load_prefecture_polygons(code)
    raw_area_m2 = sum(p.area for p in raw_polygons)

    mask, _params = rasterize(raw_polygons, code)
    raw_pixel_count = int(mask.sum())

    cleaned = clean_mask(mask)
    cleaned_pixel_count = int(cleaned.sum())

    final_polygons = mask_to_polygons(cleaned)
    if not final_polygons:
        raise ValueError(f"{code}: 輪郭抽出結果が空です")

    px_h, px_w = mask.shape
    svg = polygons_to_svg(final_polygons, px_w, px_h)

    out_path = OUTPUT_DIR / f"{code}-{slug}.svg"
    out_path.write_text(svg, encoding="utf-8", newline="\n")

    area_ratio = cleaned_pixel_count / raw_pixel_count if raw_pixel_count else 0
    return {
        "code": code,
        "slug": slug,
        "raw_area_km2": raw_area_m2 / 1_000_000,
        "raster_size": f"{px_w}x{px_h}",
        "pixel_area_ratio": area_ratio,
        "island_count": len(final_polygons),
        "path": str(out_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", help="生成する都道府県slugを限定する（省略時は全47件）")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    targets = PREFECTURES
    if args.only:
        targets = [(c, s) for c, s in PREFECTURES if s in args.only]

    results = []
    for code, slug in targets:
        result = generate_one(code, slug)
        results.append(result)
        print(
            f"{result['code']} {result['slug']:12s} raster={result['raster_size']:9s} "
            f"islands={result['island_count']:3d} pixel_ratio={result['pixel_area_ratio']:.4f} "
            f"-> {Path(result['path']).name}"
        )

    if not args.only and len(results) != 47:
        raise AssertionError(f"expected 47 SVGs, generated {len(results)}")

    print(f"Generated {len(results)} silhouette SVG(s) into {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
