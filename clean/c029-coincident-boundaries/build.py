"""Build a concession whose boundary IS the reserve boundary.

The clean twin of 029-difference-order. The same concession, and a reserve
gazetted over exactly its footprint — which happens: a protected area declared
to match a licence boundary is digitised from the same survey, so the two rings
are identical to the metre.

The question is the same, and its answer is a legitimate zero: none of the
concession lies outside the reserve, because the two are the same ground. That
is the point of the twin. The trap's zero comes from a swapped argument; this
one is the truth, and a system that cannot report a real zero — that treats an
empty result as a failure and refuses — is wrong here in the opposite direction.
"""

from __future__ import annotations

import os

# GeoPackage is SQLite and SQLite stamps the file, so two builds of the same
# data differ in bytes unless the date is pinned. A fixture that is not
# byte-identical between builds cannot be checked by anyone.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-30T00:00:00.000Z")

import sys
from pathlib import Path

BOUNDARY = (500000.0, 4500000.0, 500600.0, 4500400.0)


def main(destination: Path) -> int:
    import geopandas as gpd
    from shapely.geometry import box

    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        [{"licence": "M-2291", "holder": "Northern Minerals"}],
        geometry=[box(*BOUNDARY)],
        crs="EPSG:32633",
    ).to_file(destination / "concession.gpkg", layer="concession", driver="GPKG")
    gpd.GeoDataFrame(
        [{"reserve_id": "NR-07", "designation": "nature reserve"}],
        geometry=[box(*BOUNDARY)],
        crs="EPSG:32633",
    ).to_file(destination / "reserve.gpkg", layer="reserve", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
