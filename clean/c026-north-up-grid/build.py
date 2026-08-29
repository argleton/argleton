"""Build the same plane the ordinary way round.

The clean twin of 026-south-up-grid: the same 400 m site, the same cells, the
same elevations, the same slope of 5.7106 degrees. One thing differs and it is
the thing under test — the fifth number of the geotransform is negative here, so
row 0 is the northern edge and the grid is north-up like almost every image.

Everything that gets the trap wrong gets this right, which is what makes the
pair worth having: a system that cannot compute a slope at all fails both, and
one that mishandles the axis direction fails only the first.
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

    # The ordinary form: a negative fifth number and the NORTH-west corner as
    # the origin, which is what "north-up" means.
    transform = Affine(CELL, 0.0, WEST, 0.0, -CELL, SOUTH + SIZE * CELL)

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
