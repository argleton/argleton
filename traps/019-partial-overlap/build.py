"""Second probe of double-counting: the whole parcel counted as flooded.

Five fields of 10000 m2 in a row. The flood band is 30 m deep and 300 m wide,
so it covers 3000 m2 of each of the first three: 9000 m2 of farmland at risk.
Select the parcels that intersect and add their areas and you get 30000 —
three whole fields, because the unit of measurement quietly became the parcel
instead of the square metre.
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
        {"field_id": [f"F-{i + 1}" for i in range(5)], "area_m2": [10000.0] * 5},
        geometry=[
            rect(x, 0, x + 100, 100)
            # A 10 m gap after the third field — a road. Without it the fourth
            # parcel touches the flood band's edge, `intersects` returns True on
            # a zero-area contact, and this trap would be measuring
            # boundary-semantics instead of the thing it is about.
            for x in (0, 100, 200, 310, 420)
        ],
        crs=CRS,
    ).to_file(destination / "fields.gpkg", layer="fields", driver="GPKG")
    gpd.GeoDataFrame(
        {"zone": ["flood"]},
        geometry=[rect(0, 0, 300, 30)],
        crs=CRS,
    ).to_file(destination / "flood.gpkg", layer="flood", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
