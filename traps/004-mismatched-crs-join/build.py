"""Build two individually impeccable layers that never meet.

The zone is a rectangle in EPSG:4326. The points are stored in EPSG:32633 —
the UTM zone this longitude band belongs to, an entirely ordinary choice for
field data. Twelve of the forty points lie inside the rectangle, by
construction in the shared lon/lat domain; whether a consumer finds them
depends on exactly one thing: bringing the two frames together before testing
containment.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte unless the clock is pinned.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-24T00:00:00.000Z")

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import Point, Polygon

ZONE_LON = (12.30, 12.42)
ZONE_LAT = (41.80, 41.95)
# Inside: a 3x4 grid with at least 0.03 degrees of margin to every edge.
INSIDE_LON = (12.33, 12.36, 12.39)
INSIDE_LAT = (41.83, 41.86, 41.89, 41.92)
# Outside: everything at longitude 13.2 or greater — at least 0.78 degrees
# east of the zone, outside on the longitude interval alone.
OUTSIDE_LON = (13.2, 13.7, 14.2, 14.9)
OUTSIDE_LAT = (40.4, 40.9, 41.4, 42.4, 42.9, 43.4, 43.9)

ZONE_CRS = "EPSG:4326"
POINTS_CRS = "EPSG:32633"  # UTM zone 33N, which covers 12-18 degrees east


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)

    rectangle = Polygon([
        (ZONE_LON[0], ZONE_LAT[0]),
        (ZONE_LON[1], ZONE_LAT[0]),
        (ZONE_LON[1], ZONE_LAT[1]),
        (ZONE_LON[0], ZONE_LAT[1]),
    ])
    gpd.GeoDataFrame(
        {"zone_id": ["Z-1"]}, geometry=[rectangle], crs=ZONE_CRS
    ).to_file(destination / "zone.gpkg", layer="zone", driver="GPKG")

    lonlat = [(x, y) for x in INSIDE_LON for y in INSIDE_LAT]
    lonlat += [(x, y) for x in OUTSIDE_LON for y in OUTSIDE_LAT]
    forward = Transformer.from_crs(ZONE_CRS, POINTS_CRS, always_xy=True)
    points = [Point(*forward.transform(x, y)) for x, y in lonlat]
    gpd.GeoDataFrame(
        {"well_id": [f"W-{i + 1}" for i in range(len(points))]},
        geometry=points,
        crs=POINTS_CRS,
    ).to_file(destination / "points.gpkg", layer="points", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
