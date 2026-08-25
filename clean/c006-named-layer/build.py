"""Build the control: a single-layer GeoPackage, same question, no ambiguity.

One layer, honestly named `wells`, 17 points. Whether a system passes a layer
name or not, there is only one layer to get.
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

CRS = "EPSG:32632"
N_WELLS = 17


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {"well_id": [f"W-{i}" for i in range(1, N_WELLS + 1)]},
        geometry=[Point(10.0 + i * 9.0, 50.0 + (i % 4) * 13.0) for i in range(N_WELLS)],
        crs=CRS,
    ).to_file(destination / "wells.gpkg", layer="wells", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
