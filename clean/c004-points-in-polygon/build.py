"""Build the control: the same counting task, both layers in the same CRS.

Everything is defined directly in EPSG:32633 metres, so containment is an
interval comparison in the shared plane and nothing is ever transformed. The
trap and this control differ in exactly one thing: whether the two frames
already agree.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte unless the clock is pinned.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-24T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Point, Polygon

CRS = "EPSG:32633"
ZONE_E = (391_000.0, 401_000.0)
ZONE_N = (4_629_000.0, 4_641_000.0)
# Inside: a 3x3 grid with at least 2 km of margin to every edge.
INSIDE_E = (393_000.0, 396_000.0, 399_000.0)
INSIDE_N = (4_632_000.0, 4_635_000.0, 4_638_000.0)
# Outside: everything at easting 430 000 or greater — at least 29 km east.
OUTSIDE_E = (430_000.0, 460_000.0, 490_000.0)
OUTSIDE_N = (
    4_600_000.0, 4_610_000.0, 4_620_000.0, 4_650_000.0, 4_660_000.0,
    4_670_000.0, 4_680_000.0, 4_690_000.0, 4_700_000.0,
)


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)

    rectangle = Polygon([
        (ZONE_E[0], ZONE_N[0]),
        (ZONE_E[1], ZONE_N[0]),
        (ZONE_E[1], ZONE_N[1]),
        (ZONE_E[0], ZONE_N[1]),
    ])
    gpd.GeoDataFrame(
        {"zone_id": ["Z-1"]}, geometry=[rectangle], crs=CRS
    ).to_file(destination / "zone.gpkg", layer="zone", driver="GPKG")

    coords = [(e, n) for e in INSIDE_E for n in INSIDE_N]
    coords += [(e, n) for e in OUTSIDE_E for n in OUTSIDE_N]
    gpd.GeoDataFrame(
        {"well_id": [f"W-{i + 1}" for i in range(len(coords))]},
        geometry=[Point(e, n) for e, n in coords],
        crs=CRS,
    ).to_file(destination / "points.gpkg", layer="points", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
