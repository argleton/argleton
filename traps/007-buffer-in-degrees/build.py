"""Build a wells layer in EPSG:4326 where "within 500 metres" is the question.

W-1 sits at (12.40, 41.90). Three wells lie within 400 metres of it; the other
21 lie kilometres away. The layer is honest — valid points, declared CRS — and
the number 500 is honest too. What is implicit is the unit it gets applied in.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte unless the clock is pinned.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-25T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Point

CRS = "EPSG:4326"
LON, LAT = 12.40, 41.90  # W-1

# ~300 m north, ~398 m east, ~359 m south-west of W-1 (local metric at 41.9N).
INSIDE = [(LON, LAT + 0.0027), (LON + 0.0048, LAT), (LON - 0.0036, LAT - 0.0018)]
# Everything else at least ~4 km away (>= 0.05 degrees in both axes).
OUTSIDE = [(LON + 0.05 + 0.01 * i, LAT + 0.05 + 0.007 * (i % 7)) for i in range(21)]


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    points = [Point(LON, LAT)] + [Point(*c) for c in INSIDE] + [Point(*c) for c in OUTSIDE]
    gpd.GeoDataFrame(
        {"well_id": [f"W-{i + 1}" for i in range(len(points))]},
        geometry=points,
        crs=CRS,
    ).to_file(destination / "wells.gpkg", layer="wells", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
