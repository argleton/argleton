"""Build a geographic wellfield for a three-step ID selection."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("OGR_CURRENT_DATE", "2026-10-30T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Point

LON, LAT = 12.40, 41.90
INSIDE = [(LON, LAT + 0.0027), (LON + 0.0048, LAT), (LON - 0.0036, LAT - 0.0018)]
OUTSIDE = [(LON + 0.05 + 0.01 * i, LAT + 0.05 + 0.007 * (i % 7)) for i in range(21)]


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    points = [Point(LON, LAT)] + [Point(*c) for c in INSIDE] + [Point(*c) for c in OUTSIDE]
    gpd.GeoDataFrame(
        {"well_id": [f"W-{i + 1:02d}" for i in range(len(points))]},
        geometry=points,
        crs="EPSG:4326",
    ).to_file(destination / "wells.gpkg", layer="wells", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
