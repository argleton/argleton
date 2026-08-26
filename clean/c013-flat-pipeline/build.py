"""Clean twin of 013: the same pipeline on flat ground.

From (0, 0, 0) to (500, 0, 0): 3D and 2D length agree at 500 m, so a system
that ignores Z answers this one correctly.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte unless the clock is pinned.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-26T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import LineString

CRS = "EPSG:32632"
# The fixture sits where it says it is: EPSG:32632 coordinates near Milan
# rather than at (0, 0), which in that CRS is 500 km west of the central
# meridian and on the equator — a point in the Atlantic where the projection
# distorts area by 27%. A translation changes no area, no length and no count,
# so every truth in this family is unaffected; what changes is that the file
# stops implying something false.
EAST, NORTH = 500_000.0, 5_030_000.0



def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {"pipe_id": ["PL-1"]},
        geometry=[LineString([(EAST + 0, NORTH + 0, 0), (EAST + 500, NORTH + 0, 0)])],
        crs=CRS,
    ).to_file(destination / "pipeline.gpkg", layer="pipeline", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
