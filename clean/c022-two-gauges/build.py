"""Build the clean twin: the same question, with the pairing unable to matter.

Two gauges 5 km apart and a site 224 m from one of them. The Thiessen answer is
the same whichever cell ends up on whichever row, because with two points the
site is inside the nearer one's cell under any pairing that a correct
implementation and an incorrect one can produce alike.

That is the point of the twin. It exercises the same operation, on the same
kind of data, with the same question -- so a system that answers this one and
misses the trap has met the defect, while a system that misses both could not do
the task at all. And a system that refuses everything to keep its silent-error
rate down is caught here, where there is nothing to refuse.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-27T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Point

CRS = "EPSG:32633"
GAUGES = [("G-1", 0.0, 0.0, 305.0), ("G-2", 5000.0, 0.0, 688.0)]
SITE = ("S-1", 200.0, 100.0)


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {
            "gauge_id": [row[0] for row in GAUGES],
            "rainfall_mm": [row[3] for row in GAUGES],
        },
        geometry=[Point(row[1], row[2]) for row in GAUGES],
        crs=CRS,
    ).to_file(destination / "gauges.gpkg", layer="gauges", driver="GPKG")
    gpd.GeoDataFrame(
        {"site_id": [SITE[0]]}, geometry=[Point(SITE[1], SITE[2])], crs=CRS
    ).to_file(destination / "site.gpkg", layer="site", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
