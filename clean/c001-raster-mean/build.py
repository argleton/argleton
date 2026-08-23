"""The same elevations, stored without the predictor.

The control. If a system cannot answer this, it cannot answer trap 001 either,
and its silent-error rate on that trap says nothing about silent errors — only
that the task was out of reach. Every trap family should have a clean twin for
the same reason a medical test needs a negative control.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

HEIGHT = WIDTH = 32
BASE, EAST_STEP, SOUTH_STEP = 1000, 4, 2


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    row, column = np.mgrid[0:HEIGHT, 0:WIDTH]
    grid = (BASE + EAST_STEP * column + SOUTH_STEP * row).astype("int16")
    with rasterio.open(
        destination / "dem.tif", "w", driver="GTiff", height=HEIGHT, width=WIDTH,
        count=1, dtype="int16", crs="EPSG:32632", nodata=-32768,
        transform=from_origin(500000.0, 5000000.0, 30.0, 30.0),
    ) as ds:
        ds.write(grid, 1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
