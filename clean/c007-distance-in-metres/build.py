"""Build the control: the same counting question on a layer already in metres.

Five wells within 460 m of W-1, everything else 2.5 km away or more, all in
EPSG:32633 — the distance 500 and the layer's unit finally agree.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte unless the clock is pinned.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-25T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Point

CRS = "EPSG:32633"
E0, N0 = 500_000.0, 4_640_000.0  # W-1

INSIDE = [
    (E0 + 300.0, N0), (E0, N0 + 400.0), (E0 - 250.0, N0 - 250.0),
    (E0 + 120.0, N0 - 430.0), (E0 - 460.0, N0),
]
OUTSIDE = [(E0 + 2000.0 + 150.0 * i, N0 + 1500.0 + 100.0 * (i % 5)) for i in range(24)]


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    points = [Point(E0, N0)] + [Point(*c) for c in INSIDE] + [Point(*c) for c in OUTSIDE]
    gpd.GeoDataFrame(
        {"well_id": [f"W-{i + 1}" for i in range(len(points))]},
        geometry=points,
        crs=CRS,
    ).to_file(destination / "wells.gpkg", layer="wells", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
