"""Build one GeoPackage holding two layers, neither of them wrong.

``zones`` is written first (4 polygons) and therefore becomes the container's
default layer; ``wells`` (31 points) is written second. Every reader that is
handed the file without a layer name gets zones — the question the caller
asked names wells. Both layers are valid, ordinary and honest; the only trap
is that the container can answer a question nobody asked.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte unless the clock is pinned.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-25T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Point, Polygon

CRS = "EPSG:32632"
N_ZONES = 4
N_WELLS = 31


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    container = destination / "project.gpkg"

    zones = gpd.GeoDataFrame(
        {"zone_id": [f"Z-{i}" for i in range(1, N_ZONES + 1)]},
        geometry=[
            Polygon([
                (i * 100.0, 0.0), (i * 100.0 + 80.0, 0.0),
                (i * 100.0 + 80.0, 80.0), (i * 100.0, 80.0),
            ])
            for i in range(N_ZONES)
        ],
        crs=CRS,
    )
    zones.to_file(container, layer="zones", driver="GPKG")

    wells = gpd.GeoDataFrame(
        {"well_id": [f"W-{i}" for i in range(1, N_WELLS + 1)]},
        geometry=[Point(10.0 + i * 7.0, 200.0 + (i % 5) * 11.0) for i in range(N_WELLS)],
        crs=CRS,
    )
    wells.to_file(container, layer="wells", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
