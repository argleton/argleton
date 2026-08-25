"""Build a parcel stored in EPSG:3857, where every coordinate is in metres.

The parcel is an exact 120 x 100 rectangle in the map plane, sitting at the
latitude of Rome. Web Mercator's metres are real metres of MAP: at 41.86 north
one metre of map is cos(41.86) metres of ground, so the 12,000 m2 the plane
shows covers 6,656 m2 of land. The file is honest, the CRS is declared, and
its unit really is the metre. What the unit does not say is metres of what.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte unless the clock is pinned.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-25T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import box

CRS = "EPSG:3857"
X0, WIDTH = 1_380_000.0, 120.0  # ~12.40E
Y0, HEIGHT = 5_140_000.0, 100.0  # ~41.86N


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {"parcel_id": ["P-1"]},
        geometry=[box(X0, Y0, X0 + WIDTH, Y0 + HEIGHT)],
        crs=CRS,
    ).to_file(destination / "parcel.gpkg", layer="parcel", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
