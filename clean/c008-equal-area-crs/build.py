"""Build the clean twin of 008: the same question where the plane tells the truth.

The parcel is an exact 100 x 100 rectangle in EPSG:3035 (Lambert Azimuthal
Equal-Area over Europe), at the same latitude as the trap. LAEA preserves area
by construction, so here — and only here — the planar shoelace IS the ground
area, and the composition that falls into 008 answers this one correctly.
Without this twin, a failure on 008 could not be told apart from "the system
cannot measure an area at all".
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

CRS = "EPSG:3035"
X0, Y0, SIDE = 4_532_000.0, 2_050_000.0, 100.0  # ~12.52E 41.52N


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {"parcel_id": ["P-1"]},
        geometry=[box(X0, Y0, X0 + SIDE, Y0 + SIDE)],
        crs=CRS,
    ).to_file(destination / "parcel.gpkg", layer="parcel", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
