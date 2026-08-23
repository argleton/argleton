"""Build a parcel in a CRS whose linear unit is the US survey foot.

Nothing here is unusual. EPSG:2229 is NAD83 / California zone 5, it is what a
large part of California's public parcel data is published in, and its unit is
the US survey foot. The numbers in the file are feet, and they do not say so
anywhere a naive reader would look.
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

SIDE_FEET = 1000.0
ORIGIN_X, ORIGIN_Y = 6_500_000.0, 1_800_000.0  # ordinary coordinates for the zone


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    square = Polygon([
        (ORIGIN_X, ORIGIN_Y),
        (ORIGIN_X + SIDE_FEET, ORIGIN_Y),
        (ORIGIN_X + SIDE_FEET, ORIGIN_Y + SIDE_FEET),
        (ORIGIN_X, ORIGIN_Y + SIDE_FEET),
    ])
    gpd.GeoDataFrame(
        {"parcel_id": ["A-1"]}, geometry=[square], crs="EPSG:2229"
    ).to_file(destination / "parcel.gpkg", layer="parcel", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
