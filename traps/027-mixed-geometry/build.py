"""Build a network layer that also contains the plant it runs to.

`network.gpkg` is a water utility's asset layer: five pipe runs and one
treatment-plant footprint, in one layer, which is what a GeoPackage allows and
what a shapefile does not. That single difference is why so much data arrives
this way — a conversion out of shapefiles into a GeoPackage merges what the
older format had forced apart, and nothing complains.

The five pipes are straight and axis-aligned, so their lengths are exact:

    600 + 400 + 250 + 250 + 500 = 2000 m

The plant is a 300 by 200 m rectangle. It has no length. Ask a layer for the
length of its geometries and a polygon answers with its perimeter — 1000 m —
because that is what the length of a closed ring is, and it is the right answer
to a question nobody asked.

The numbers are chosen so the wrong total is round. 2000 m of pipe becomes
3000 m: half as much again, no decimal to look odd, and every individual pipe
still the length it says it is.
"""

from __future__ import annotations

import os

# GeoPackage is SQLite and SQLite stamps the file, so two builds of the same
# data differ in bytes unless the date is pinned. A fixture that is not
# byte-identical between builds cannot be checked by anyone.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-30T00:00:00.000Z")

import sys
from pathlib import Path

#: UTM 33N, a works site. Pipes first, then the plant, in the order a merge
#: would have produced.
PIPES = [
    ("P-01", [(500000, 4500000), (500600, 4500000)]),          # 600
    ("P-02", [(500600, 4500000), (500600, 4500400)]),          # 400
    ("P-03", [(500600, 4500400), (500850, 4500400)]),          # 250
    ("P-04", [(500000, 4500000), (500000, 4500250)]),          # 250
    ("P-05", [(500000, 4500250), (500500, 4500250)]),          # 500
]

#: 300 x 200, so a perimeter of exactly 1000.
PLANT = [
    (500850, 4500400),
    (501150, 4500400),
    (501150, 4500600),
    (500850, 4500600),
    (500850, 4500400),
]


def main(destination: Path) -> int:
    import geopandas as gpd
    from shapely.geometry import LineString, Polygon

    destination.mkdir(parents=True, exist_ok=True)

    rows = [
        {"asset_id": name, "asset_type": "pipe", "geometry": LineString(points)}
        for name, points in PIPES
    ]
    rows.append(
        {"asset_id": "WTP-1", "asset_type": "treatment_plant", "geometry": Polygon(PLANT)}
    )

    # One layer, two geometry types. GeoPackage stores the layer's declared
    # geometry type as GEOMETRY when they differ, which is legal, and every
    # reader accepts it without a word.
    gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:32633").to_file(
        destination / "network.gpkg", layer="assets", driver="GPKG"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
