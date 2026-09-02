"""Build a survey plot whose easement ring is wound the wrong way.

A shapefile has no nesting. Whether a ring is a shell or a hole is decided by
one thing only — the direction it is wound — and GDAL applies that rule as
documented: `OGR_ORGANIZE_POLYGONS` defaults to `ONLY_CCW` for this driver,
under which a clockwise ring is a shell and a counter-clockwise ring is a hole.

So a converter, an editor or a hand-written exporter that emits the inner ring
in the same direction as the outer one produces a file that is legal, opens
without a warning, and means something else: two overlapping shells instead of
one shell with a hole. The plot is 200 x 150 = 30000 m2 and the easement is
40 x 25 = 1000, so the truth is 29000 by subtraction and the misreading gives
31000 by addition — the easement counted once as land instead of once as a gap,
which is a difference of exactly twice its own area.

**The fixture patches the bytes, and it has to.** Writing the polygon through
OGR does not produce this file: the shapefile writer NORMALISES ring direction
on the way out, so a hole handed to it clockwise lands on disk anticlockwise.
Measured on 2026-09-02 by reading the record back out of the `.shp` — the
geometry in memory said clockwise and the bytes said the opposite. The only way
to obtain the file a real converter produces is to write the correct file and
reverse the inner ring's point order in place, which is what happens below and
is why the arithmetic above stays exact: reversing a ring changes no coordinate.
"""

from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

os.environ.setdefault("OGR_CURRENT_DATE", "2026-09-02T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Polygon

CRS = "EPSG:32632"
# Placed where it says it is, like every other fixture here: (0, 0) in this CRS
# is in the Atlantic, and a file that implies something false about where it is
# teaches the reader to distrust the ones that do not.
EAST, NORTH = 500_000.0, 5_030_000.0

PLOT = (0.0, 0.0, 200.0, 150.0)  # 30000 m2
EASEMENT = (60.0, 60.0, 100.0, 85.0)  # 40 x 25 = 1000 m2


def ring(x0: float, y0: float, x1: float, y1: float) -> list[tuple[float, float]]:
    """A closed rectangle, anticlockwise, in the fixture's real-world frame."""
    return [
        (EAST + x0, NORTH + y0),
        (EAST + x1, NORTH + y0),
        (EAST + x1, NORTH + y1),
        (EAST + x0, NORTH + y1),
        (EAST + x0, NORTH + y0),
    ]


def reverse_inner_ring(shapefile: Path) -> None:
    """Reverse the second ring of the single record, in the `.shp` bytes.

    The shapefile record layout for a polygon is fixed and documented: a 8-byte
    record header, the shape type, a 32-byte bounding box, the ring count, the
    point count, the ring start offsets, and then the points as pairs of
    little-endian doubles. Reversing the order of the second ring's points is
    therefore a local edit that changes no coordinate and no length — only the
    direction, which in this format is the whole meaning.
    """
    raw = bytearray(shapefile.read_bytes())
    at = 100 + 8 + 4 + 32  # header, record header, shape type, bounding box
    rings, points = struct.unpack("<ii", raw[at : at + 8])
    at += 8
    starts = list(struct.unpack(f"<{rings}i", raw[at : at + 4 * rings]))
    at += 4 * rings
    if rings != 2:
        raise SystemExit(f"expected two rings in {shapefile.name}, found {rings}")
    inner = [
        struct.unpack("<dd", raw[at + 16 * i : at + 16 * i + 16])
        for i in range(starts[1], points)
    ]
    for offset, (x, y) in enumerate(reversed(inner)):
        struct.pack_into("<dd", raw, at + 16 * (starts[1] + offset), x, y)
    shapefile.write_bytes(bytes(raw))


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    plot = destination / "plot.shp"
    gpd.GeoDataFrame(
        {"plot_id": ["S-1"]},
        geometry=[Polygon(ring(*PLOT), [ring(*EASEMENT)])],
        crs=CRS,
    ).to_file(plot)
    reverse_inner_ring(plot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
