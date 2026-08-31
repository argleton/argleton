"""The same raster with one georeferencing instead of two.

Identical to the trap in every other way — same size, same cells, same origin,
same CRS, same values — and with no `.aux.xml` beside it. That is the whole
difference, and it is what lets a rate on this family mean "misreads a dataset
with two georeferencings" instead of "cannot measure a raster".
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

SIZE = 20
ORIGIN = (500000.0, 5030000.0)
CELL = 10.0
CRS = "EPSG:32632"


def main(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    values = np.tile(np.arange(SIZE, dtype="float32"), (SIZE, 1)) + 100.0
    with rasterio.open(
        target / "terrain.tif", "w", driver="GTiff", height=SIZE, width=SIZE,
        count=1, dtype="float32", crs=CRS,
        transform=Affine(CELL, 0.0, ORIGIN[0], 0.0, -CELL, ORIGIN[1]),
    ) as destination:
        destination.write(values, 1)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
