"""Build the same DEM, registered the ordinary way.

The clean twin of 024-pixel-is-point: identical surface, identical spacing,
identical tie point, identical lowest node. One thing differs, and it is the
thing under test — the raster type the file declares.

Here it is `AREA_OR_POINT=Area`, which is the default and what most of the world
ships. A value describes the cell it fills, the tie point is that cell's corner,
and the position of the lowest value is the centre of the lowest cell:

    412000 + 3 * 30 + 15 = 412105

which is precisely the answer that is WRONG on the trap. That is the point of
the pair. A system that hard-codes either convention answers one of the two and
fails the other, and a silent-error rate measured on the trap alone could not
tell that apart from a system that simply cannot read a DEM.

A shallow bowl, 8 by 8 cells at 30 m spacing, with exactly one lowest point at
node (row 2, column 3). The elevation model is

    z = 300 + 0.5 * ((column - 3)^2 + (row - 2)^2)

so the minimum is strict — every neighbour is at least 0.5 m higher — and the
question "where is the bottom of this hollow" has one answer and no argument
about it.

"""

from __future__ import annotations

import sys
from pathlib import Path

#: Tie point, spacing and size. Written out rather than derived so that the file
#: and the derivation in probe.toml cannot drift apart.
EAST0 = 412000.0
NORTH0 = 5108000.0
SPACING = 30.0
SIZE = 8

#: Where the bottom of the hollow is, in grid indices.
LOW_ROW = 2
LOW_COLUMN = 3
LOW_ELEVATION = 300.0


def main(destination: Path) -> int:
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin

    destination.mkdir(parents=True, exist_ok=True)

    rows, columns = np.mgrid[0:SIZE, 0:SIZE]
    surface = LOW_ELEVATION + 0.5 * (
        (columns - LOW_COLUMN) ** 2 + (rows - LOW_ROW) ** 2
    )

    path = destination / "hollow.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=SIZE,
        width=SIZE,
        count=1,
        dtype="float32",
        crs="EPSG:32632",
        transform=from_origin(EAST0, NORTH0, SPACING, SPACING),
    ) as dst:
        dst.write(surface.astype("float32"), 1)
        # Declared rather than left to the default, because the pair is about
        # this line: the trap says Point here, and everything else is the same
        # file. An implicit default would leave a reader wondering whether the
        # difference was intended.
        dst.update_tags(AREA_OR_POINT="Area")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
