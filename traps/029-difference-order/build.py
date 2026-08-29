"""Build a mining concession with a nature reserve inside it.

Two rectangles in UTM 33N, and the reserve is wholly contained in the
concession:

    concession   500000..500600 E, 4500000..4500400 N   600 x 400 = 240000 m2
    reserve      500100..500500 E, 4500100..4500300 N   400 x 200 =  80000 m2

The question is how much of the concession lies OUTSIDE the reserve — the part
that can be worked. On paper that is 240000 - 80000 = 160000 m2, and it is a
subtraction of two rectangles with whole-metre corners, so it is exact.

The trap is the order of the two arguments. `difference` is not symmetric, and
the wrong way round is not an error: the reserve minus the concession is a
perfectly valid question whose answer here is nothing at all, because the
reserve is entirely inside. So a swapped call returns an EMPTY result, and an
empty result reads as an answer — nought hectares outside the reserve, the whole
licence is protected. That is a finding a board would act on.

Containment is what makes it silent. If the two overlapped only partially, both
orders would return something and the numbers would differ visibly. Here one
order returns 160000 and the other returns nothing, and nothing is not an error
message.
"""

from __future__ import annotations

import os

# GeoPackage is SQLite and SQLite stamps the file, so two builds of the same
# data differ in bytes unless the date is pinned. A fixture that is not
# byte-identical between builds cannot be checked by anyone.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-30T00:00:00.000Z")

import sys
from pathlib import Path

CONCESSION = (500000.0, 4500000.0, 500600.0, 4500400.0)
RESERVE = (500100.0, 4500100.0, 500500.0, 4500300.0)


def main(destination: Path) -> int:
    import geopandas as gpd
    from shapely.geometry import box

    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        [{"licence": "M-2291", "holder": "Northern Minerals"}],
        geometry=[box(*CONCESSION)],
        crs="EPSG:32633",
    ).to_file(destination / "concession.gpkg", layer="concession", driver="GPKG")
    gpd.GeoDataFrame(
        [{"reserve_id": "NR-07", "designation": "nature reserve"}],
        geometry=[box(*RESERVE)],
        crs="EPSG:32633",
    ).to_file(destination / "reserve.gpkg", layer="reserve", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
