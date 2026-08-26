"""Clean twin of 015: the same partition, no well on the boundary.

The four seam wells move one metre west. Strict containment and boundary
inclusion agree at 12, so a system that uses `within` answers this one
correctly.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte unless the clock is pinned.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-26T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Point, Polygon

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



def at(x: float, y: float) -> Point:
    """A point in local metres, placed at the fixture's real-world origin."""
    return Point(EAST + x, NORTH + y)


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    wells = [
        (10, 10), (20, 30), (30, 60), (40, 80),
        (60, 10), (70, 30), (80, 60), (90, 80),
        (49, 20), (49, 40), (49, 60), (49, 80),
    ]
    gpd.GeoDataFrame(
        {"well_id": [f"W-{i + 1}" for i in range(len(wells))]},
        geometry=[at(x, y) for x, y in wells],
        crs=CRS,
    ).to_file(destination / "wells.gpkg", layer="wells", driver="GPKG")
    gpd.GeoDataFrame(
        {"district": ["west", "east"]},
        geometry=[
            rect(0, 0, 50, 100),
            rect(50, 0, 100, 100),
        ],
        crs=CRS,
    ).to_file(destination / "districts.gpkg", layer="districts", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
