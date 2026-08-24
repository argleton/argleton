"""Build the control: an ordinary valid L-shaped parcel in a metric CRS.

Same operation and same phrasing as the trap; the only difference is that the
ring does not cross itself. The L-shape (rather than another rectangle) keeps
the control from being answerable by pattern-matching the fixture family.
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
E0, N0 = 402_000.0, 5_003_000.0

# Local shape: an L. Area = 100*40 + 60*60 = 7600 m2, on paper.
RING = [(0.0, 0.0), (100.0, 0.0), (100.0, 40.0), (60.0, 40.0), (60.0, 100.0), (0.0, 100.0)]


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    ell = Polygon([(E0 + x, N0 + y) for x, y in RING])
    gpd.GeoDataFrame(
        {"parcel_id": ["A-1"]}, geometry=[ell], crs=CRS
    ).to_file(destination / "parcel.gpkg", layer="parcel", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
