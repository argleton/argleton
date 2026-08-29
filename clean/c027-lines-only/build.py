"""Build the same network with the plant in a layer of its own.

The clean twin of 027-mixed-geometry: the same five pipe runs, the same 2000 m,
the same treatment plant at the same coordinates. One thing differs and it is
the thing under test — this `assets` layer holds only the pipe runs, so every
geometry in it is a LineString.

That is the arrangement thirty years of shapefiles enforced, one geometry type
per file, and it is why summing the length of every geometry in a layer became
a habit that usually works. The plant is delivered separately here, as
structures were for as long as the format required it.

One layer in each half of the pair, deliberately. A second layer would drag in
the ambiguous-container question — a real one, and a different family — and the
twin has to isolate the geometry types and nothing else.
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

def main(destination: Path) -> int:
    import geopandas as gpd
    from shapely.geometry import LineString

    destination.mkdir(parents=True, exist_ok=True)

    rows = [
        {"asset_id": name, "asset_type": "pipe", "geometry": LineString(points)}
        for name, points in PIPES
    ]
    # One layer holding pipes and nothing else, so its declared geometry type
    # is LineString rather than GEOMETRY.
    gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:32633").to_file(
        destination / "network.gpkg", layer="assets", driver="GPKG"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
