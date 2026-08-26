"""Clean twin of 017: three municipalities of the same size.

Labour forces 1000, 1000, 1000 with rates 20%, 20%, 5%. Weighted and
unweighted agree at 15%, so a system that averages rates answers this one
correctly — which is exactly what makes the habit survive.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

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


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {
            "municipality": ["A", "B", "C"],
            "labour_force": [1000, 1000, 1000],
            "unemployment_rate_pct": [20.0, 20.0, 5.0],
        },
        geometry=[
            rect(0, 0, 10, 10),
            rect(10, 0, 20, 10),
            rect(0, 10, 20, 20),
        ],
        crs=CRS,
    ).to_file(destination / "municipalities.gpkg", layer="municipalities", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
