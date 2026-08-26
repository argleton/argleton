"""Build an L-shaped parcel whose centroid falls outside it.

The L is a 100 x 20 horizontal bar plus a 20 x 80 vertical one: 3600 m2, and
its centroid is at (32.222, 32.222) — in the notch, on no part of the parcel.
The whole parcel lies in district A; the centroid lands in district B.
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
        (EAST + x0, NORTH + y0),
        (EAST + x1, NORTH + y0),
        (EAST + x1, NORTH + y1),
        (EAST + x0, NORTH + y1),
    ])



def l_shape() -> Polygon:
    """The L: a 100x20 bar plus a 20x80 upright, 3600 m2, centroid in the notch."""
    return Polygon([
        (EAST + 0, NORTH + 0), (EAST + 100, NORTH + 0), (EAST + 100, NORTH + 20),
        (EAST + 20, NORTH + 20), (EAST + 20, NORTH + 100), (EAST + 0, NORTH + 100),
    ])


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {"parcel_id": ["P-1"]},
        geometry=[l_shape()],
        crs=CRS,
    ).to_file(destination / "parcel.gpkg", layer="parcel", driver="GPKG")
    gpd.GeoDataFrame(
        {"district": ["A", "B"]},
        geometry=[
            # A: everything the parcel occupies. B: the notch it does not.
            l_shape(),
            rect(20, 20, 100, 100),
        ],
        crs=CRS,
    ).to_file(destination / "districts.gpkg", layer="districts", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
