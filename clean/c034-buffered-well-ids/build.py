"""Build the projected control for a three-step ID selection."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("OGR_CURRENT_DATE", "2026-10-30T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Point

E0, N0 = 500_000.0, 4_640_000.0
INSIDE = [
    (E0 + 300.0, N0), (E0, N0 + 400.0), (E0 - 250.0, N0 - 250.0),
    (E0 + 120.0, N0 - 430.0), (E0 - 460.0, N0),
]
OUTSIDE = [(E0 + 2000.0 + 150.0 * i, N0 + 1500.0 + 100.0 * (i % 5)) for i in range(24)]


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    points = [Point(E0, N0)] + [Point(*c) for c in INSIDE] + [Point(*c) for c in OUTSIDE]
    gpd.GeoDataFrame(
        {"well_id": [f"W-{i + 1:02d}" for i in range(len(points))]},
        geometry=points,
        crs="EPSG:32633",
    ).to_file(destination / "wells.gpkg", layer="wells", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
