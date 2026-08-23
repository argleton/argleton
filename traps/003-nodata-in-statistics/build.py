"""A DEM that declares its nodata value, and has fifty cells of it.

Nothing is hidden. The GeoTIFF carries `nodata = -9999` in its header, where
every raster library looks for it, and the void cells hold exactly that value.
The file is not malformed and it is not unusual: voids are what a DEM has where
the sensor saw cloud, water or steep shadow, and -9999 is the convention that
fills them.

The elevations are constant on purpose. A fixture whose valid cells all hold the
same number makes both the right answer and the wrong one checkable on paper,
which is worth more here than looking like terrain.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

SIDE = 100
ELEVATION = 1000
NODATA = -9999
VOID_CELLS = 50
STRIDE = 197  # coprime with SIDE*SIDE, so the voids scatter and never repeat


def elevations() -> np.ndarray:
    grid = np.full((SIDE, SIDE), ELEVATION, dtype="int16")
    flat = grid.reshape(-1)
    for k in range(VOID_CELLS):
        flat[(k * STRIDE) % (SIDE * SIDE)] = NODATA
    return grid


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        destination / "dem.tif", "w", driver="GTiff",
        height=SIDE, width=SIDE, count=1, dtype="int16",
        crs="EPSG:32632", nodata=NODATA,
        transform=from_origin(500000.0, 5000000.0, 30.0, 30.0),
    ) as ds:
        ds.write(elevations(), 1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
