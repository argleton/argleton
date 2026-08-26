"""Clean twin of 018: the same join, no leading zeros.

Twelve codes that survive type inference unchanged, same 100000 total. A
system that reads keys as integers answers this one correctly.
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
        (EAST + x0, NORTH + y0), (EAST + x1, NORTH + y0),
        (EAST + x1, NORTH + y1), (EAST + x0, NORTH + y1),
    ])


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    codes = ["100", "200", "300", "400", "500", "600",
             "700", "800", "900", "110", "120", "130"]
    gpd.GeoDataFrame(
        {"istat_code": codes},
        geometry=[
            rect(i * 10, 0, i * 10 + 10, 10)
            for i in range(len(codes))
        ],
        crs=CRS,
    ).to_file(destination / "municipalities.gpkg", layer="municipalities", driver="GPKG")
    populations = [9500] * 4 + [7750] * 8
    lines = ["istat_code,population"] + [
        f"{c},{p}" for c, p in zip(codes, populations, strict=True)
    ]
    (destination / "population.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
