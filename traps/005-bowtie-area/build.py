"""Build one self-intersecting parcel — a bowtie with unequal lobes.

The ring is A -> B -> C -> D -> A with two edges crossing once. Nothing refuses
to store it: GeoPackage writes it, every reader reads it back byte-identical,
and the polygon renders as two filled triangles that look like an ordinary odd
parcel. The coordinates are ordinary UTM 32N metres.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# GeoPackage stamps the write time into `gpkg_contents.last_change`, so two
# builds of the same data differ byte for byte unless the clock is pinned.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-24T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Polygon

CRS = "EPSG:32632"
E0, N0 = 400_000.0, 5_000_000.0  # ordinary coordinates for the zone

# Local shape: A=(0,0), B=(0,100), C=(120,20), D=(120,80). Edges B->C and D->A
# cross at X=(75,50); the lobes are the triangles (A,B,X) = 3750 m2 and
# (C,D,X) = 1350 m2. Offsets do not change areas.
RING = [(0.0, 0.0), (0.0, 100.0), (120.0, 20.0), (120.0, 80.0)]


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    bowtie = Polygon([(E0 + x, N0 + y) for x, y in RING])
    gpd.GeoDataFrame(
        {"parcel_id": ["A-1"]}, geometry=[bowtie], crs=CRS
    ).to_file(destination / "parcel.gpkg", layer="parcel", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
