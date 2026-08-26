"""Build three municipalities whose unemployment rates must be combined.

Two small ones (1000 in the labour force, 20% unemployed) and one large
(98000, 1%). The area's rate is total unemployed over total labour force:
(200 + 200 + 980) / 100000 = 1.38%. Averaging the three rates gives 13.67%,
because it treats a town of a thousand as equal to a city of a hundred
thousand.
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
            "municipality": ["Small A", "Small B", "Large C"],
            "labour_force": [1000, 1000, 98000],
            "unemployment_rate_pct": [20.0, 20.0, 1.0],
        },
        geometry=[
            rect(0, 0, 10, 10),
            rect(10, 0, 20, 10),
            rect(0, 10, 20, 110),
        ],
        crs=CRS,
    ).to_file(destination / "municipalities.gpkg", layer="municipalities", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
