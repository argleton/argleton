"""The same survey plot, with the easement ring wound the way the format expects.

Identical geometry, identical coordinates, identical arithmetic: 200 x 150 minus
40 x 25 is 29000 m2. The only difference from the trap is the direction the
inner ring is written in, which is the whole of what a shapefile uses to say
"this ring is a hole".

Nothing is patched here, and that is the point of the twin: writing the polygon
through OGR produces the correct winding by itself, because the shapefile writer
normalises it. A file with the wrong winding cannot be produced by accident from
this library — it comes from a converter, an exporter or a hand-rolled writer,
which is exactly where it comes from in the field.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("OGR_CURRENT_DATE", "2026-09-02T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Polygon

CRS = "EPSG:32632"
EAST, NORTH = 500_000.0, 5_030_000.0

PLOT = (0.0, 0.0, 200.0, 150.0)  # 30000 m2
EASEMENT = (60.0, 60.0, 100.0, 85.0)  # 40 x 25 = 1000 m2


def ring(x0: float, y0: float, x1: float, y1: float) -> list[tuple[float, float]]:
    return [
        (EAST + x0, NORTH + y0),
        (EAST + x1, NORTH + y0),
        (EAST + x1, NORTH + y1),
        (EAST + x0, NORTH + y1),
        (EAST + x0, NORTH + y0),
    ]


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {"plot_id": ["S-1"]},
        geometry=[Polygon(ring(*PLOT), [ring(*EASEMENT)])],
        crs=CRS,
    ).to_file(destination / "plot.shp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
