"""The same raster with the voids filled, so nothing has to be excluded.

The control for `003-nodata-in-statistics`. Identical grid, identical task, and
no nodata cells at all: a system that answers this and misses the trap has told
us it does not honour a declared nodata value. One that misses both has told us
it cannot read the raster, which is a different finding.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

SIDE = 100
ELEVATION = 1000


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        destination / "dem.tif", "w", driver="GTiff",
        height=SIDE, width=SIDE, count=1, dtype="int16",
        crs="EPSG:32632", nodata=-9999,
        transform=from_origin(500000.0, 5000000.0, 30.0, 30.0),
    ) as ds:
        ds.write(np.full((SIDE, SIDE), ELEVATION, dtype="int16"), 1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
