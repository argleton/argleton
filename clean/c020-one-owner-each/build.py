"""Clean twin of 020: ten parcels, ten owners, one each.

The join returns ten rows and the sum is 50000, so a system that sums after
joining answers this one correctly.
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
    parcels = [f"P-{i + 1}" for i in range(10)]
    gpd.GeoDataFrame(
        {"parcel_id": parcels, "area_m2": [5000.0] * 10},
        geometry=[
            rect(i * 100, 0, i * 100 + 50, 100)
            for i in range(10)
        ],
        crs=CRS,
    ).to_file(destination / "parcels.gpkg", layer="parcels", driver="GPKG")
    lines = ["parcel_id,owner"] + [f"{p},Owner{i + 1}" for i, p in enumerate(parcels)]
    (destination / "owners.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
