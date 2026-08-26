"""Build a parcel with a courtyard: one outer ring, one inner ring.

The outer ring is 100 x 100 = 10000 m2 exactly and the courtyard 40 x 40 =
1600 m2 exactly, so the buildable area is 8400 m2 by subtraction and by
nothing else. Read the inner ring as a second outer ring and the same two
numbers add to 11600 instead.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte unless the clock is pinned.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-26T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Polygon

CRS = "EPSG:32632"
# The fixture sits where it says it is: EPSG:32632 coordinates near Milan
# rather than at (0, 0), which in that CRS is 500 km west of the central
# meridian and on the equator — a point in the Atlantic where the projection
# distorts area by 27%. A translation changes no area, no length and no count,
# so every truth in this family is unaffected; what changes is that the file
# stops implying something false.
EAST, NORTH = 500_000.0, 5_030_000.0




def rect(x0: float, y0: float, x1: float, y1: float) -> Polygon:
    """A rectangle in local metres, placed at the fixture's real-world origin."""
    return Polygon([
        (EAST + x0, NORTH + y0), (EAST + x1, NORTH + y0),
        (EAST + x1, NORTH + y1), (EAST + x0, NORTH + y1),
    ])


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {"parcel_id": ["P-1"]},
        geometry=[
            Polygon(rect(0, 0, 100, 100).exterior, [rect(30, 30, 70, 70).exterior])
        ],
        crs=CRS,
    ).to_file(destination / "parcel.gpkg", layer="parcel", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
