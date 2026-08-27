"""Build five rain gauges whose Thiessen cells will be paired by position.

Nothing is wrong with this file. Five gauges in UTM 33N, round coordinates, one
annual-rainfall reading each, and a site to assign a value to. The defect is not
in the data and not in any library: it is in the composition almost everyone
writes to answer the question, which pairs the cells a Voronoi routine returns
with the rows they came from BY POSITION, when nothing guarantees that pairing.

The gauge positions are not decorative. With this arrangement the default order
of shapely's Voronoi output puts ONE of the five cells on its own point, so the
site's cell arrives carrying a value measured 985 m away. A different
arrangement would have hidden the defect by luck -- five of the six candidate
layouts tried on 27/08/2026 did exactly that -- which is why the layout is
pinned here and the shapely version is recorded in the probe.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte unless the clock is pinned.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-27T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Point

CRS = "EPSG:32633"  # UTM 33N: metres, so a distance is a distance

# (gauge id, easting, northing, annual rainfall in mm). Every reading is an
# ordinary annual total for a Mediterranean catchment, so no value in the file
# and no value that can come out of it invites a second look.
GAUGES = [
    ("G-1", 0.0, 0.0, 412.0),
    ("G-2", 400.0, 300.0, 268.0),
    ("G-3", 800.0, 600.0, 731.0),
    ("G-4", 1200.0, 900.0, 554.0),
    ("G-5", 200.0, 900.0, 197.0),
]

# The site to assign a value to. 223.61 m from G-2 and 412.31 m from the next
# nearest, so the Thiessen assignment is not close to a tie.
SITE = ("S-1", 300.0, 500.0)


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
        {"site_id": [SITE[0]]},
        geometry=[Point(SITE[1], SITE[2])],
        crs=CRS,
    ).to_file(destination / "site.gpkg", layer="site", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
