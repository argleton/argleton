"""The same square, in a CRS whose unit is the metre.

The control for `002-feet-as-metres`: identical geometry and identical task, and
the only difference is a linear unit the file states plainly. A system that
answers this and misses the trap has told us it does not read the unit. One that
misses both has told us nothing about units at all.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte. Every published number is
# anchored to a `spec_commit`, which means nothing if that commit can produce
# different fixtures — so the clock is pinned. GDAL reads this at write time,
# hence before the import that uses it.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-23T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Polygon

SIDE_METRES = 1000.0
ORIGIN_X, ORIGIN_Y = 500000.0, 5000000.0  # UTM 32N


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    square = Polygon([
        (ORIGIN_X, ORIGIN_Y),
        (ORIGIN_X + SIDE_METRES, ORIGIN_Y),
        (ORIGIN_X + SIDE_METRES, ORIGIN_Y + SIDE_METRES),
        (ORIGIN_X, ORIGIN_Y + SIDE_METRES),
    ])
    gpd.GeoDataFrame(
        {"parcel_id": ["A-1"]}, geometry=[square], crs="EPSG:32632"
    ).to_file(destination / "parcel.gpkg", layer="parcel", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
