"""Build a DEM whose rows run south to north, which is legal and not rare.

A GeoTIFF's geotransform has six numbers, and the fifth is the north-south pixel
size. It is normally negative — row 0 at the top, rows counting southwards, the
convention every "north-up" image uses. A **positive** fifth number is equally
valid and says the opposite: row 0 is the southernmost row.

Datasets arrive that way all the time. NetCDF, GRIB and HDF products index
latitude in increasing order, because that is how a coordinate axis is written,
so a straight conversion to GeoTIFF produces a grid whose first row is its
southern edge. So do several Surfer and GMT exports. GDAL reads all of them
correctly and hands the caller a transform that says which way the rows run.

The surface here is a plane, and the plane is the point: elevation rises by
exactly 1 m per cell towards the east, on cells of 10 m, so the ground slopes at
exactly

    atan(1/10) = 5.7106 degrees

everywhere. Nothing about that answer depends on which end of the grid is
stored first — the rows run the other way, and a plane tilted eastwards is
tilted eastwards whichever end you start reading from.

It depends entirely on the cell being 10 m, though. An engine that rebuilds its
own grid model and cannot express a positive fifth number has to do something
with the file, and what it does here is discard the georeferencing: a 40 by 40
grid of 1 by 1 cells at the origin. The elevations are untouched, the shape is
untouched, the coordinate system is untouched — only the size of a cell is gone,
and a slope is a rise over a run.
"""

from __future__ import annotations

import sys
from pathlib import Path

#: A 400 m square site in UTM 33N. Written out rather than computed so the file
#: and the derivation in probe.toml cannot drift apart.
WEST = 500000.0
SOUTH = 4500000.0
CELL = 10.0
SIZE = 40

#: The plane: +1 m of elevation per cell eastwards, starting at 100 m.
BASE = 100.0
RISE_PER_CELL = 1.0


def main(destination: Path) -> int:
    import numpy as np
    import rasterio
    from affine import Affine

    destination.mkdir(parents=True, exist_ok=True)

    surface = np.array(
        [[BASE + RISE_PER_CELL * column for column in range(SIZE)] for _ in range(SIZE)],
        dtype="float32",
    )

    # The fifth number is +CELL, not -CELL, and the origin is the SOUTH-west
    # corner rather than the north-west one. Those two go together: a grid whose
    # rows run northwards starts at its southern edge.
    transform = Affine(CELL, 0.0, WEST, 0.0, CELL, SOUTH)

    with rasterio.open(
        destination / "site.tif",
        "w",
        driver="GTiff",
        height=SIZE,
        width=SIZE,
        count=1,
        dtype="float32",
        crs="EPSG:32633",
        transform=transform,
    ) as dst:
        dst.write(surface, 1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
