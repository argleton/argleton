"""Build a station stored on Monte Mario with the Rome prime meridian.

The point is written in EPSG:4806 at longitude -3.5 and latitude 45.5 — round
numbers, and unmistakably Rome-meridian values: -3.5 degrees east of Monte Mario
is 8.95233333 degrees east of Greenwich, in Piedmont.

Nothing about this file is unusual. Italian cadastral and historic mapping data
is stored on Monte Mario, and both EPSG variants of it are in daily use: 4265
with the Greenwich meridian and 4806 with the Rome one. The trap is not in the
data. It is in which transformation a library picks for THIS variant.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte unless the clock is pinned.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-26T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Point

# Monte Mario (Rome). Longitudes are measured from the Rome meridian, which is
# 12.45233333... east of Greenwich: this is the whole reason the variant exists
# and the reason a value of -3.5 is not a mistake.
CRS = "EPSG:4806"
LON_FROM_ROME, LAT = -3.5, 45.5


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {"station_id": ["ST-1"]},
        geometry=[Point(LON_FROM_ROME, LAT)],
        crs=CRS,
    ).to_file(destination / "station.gpkg", layer="stations", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
