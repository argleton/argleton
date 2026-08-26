"""The same station, the same datum, the Greenwich variant.

Byte for byte the same physical point as trap 021: Monte Mario, 45.5 north,
8.952333333 east of Greenwich — which is -3.5 east of Rome. The only difference
is that the file declares EPSG:4265 (Monte Mario, Greenwich meridian) instead of
EPSG:4806 (Monte Mario, Rome meridian).

That is the whole isolation. Same datum, same shift to apply, same correct
answer. If a system gets this one right and the trap wrong, the cause is not
"datum transformations are hard": it is which variant it was handed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-26T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Point

CRS = "EPSG:4265"
# -3.5 from Rome is 8.952333333... from Greenwich. The two fixtures describe
# one place.
LON_FROM_GREENWICH, LAT = 8.952333333333333, 45.5


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {"station_id": ["ST-1"]},
        geometry=[Point(LON_FROM_GREENWICH, LAT)],
        crs=CRS,
    ).to_file(destination / "station.gpkg", layer="stations", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
