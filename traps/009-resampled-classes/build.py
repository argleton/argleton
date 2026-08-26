"""Build a land-cover raster that must be resampled to answer the question.

Two classes in a 3x3 grid of 20 m cells: the two west columns are forest (1),
the east column is water (3). The legend also defines 2 = urban, and no cell
in this file carries it.

The question asks for the urban area on a 15 m grid — the resolution of a
different dataset it has to line up with. 60 m of extent divides into four
15 m cells, and the new cell centres fall between the old ones, which is the
ordinary case whenever two grids have to meet.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

CRS = "EPSG:32633"
CELL = 20.0
CLASSES = np.array([[1, 1, 3], [1, 1, 3], [1, 1, 3]], dtype="uint8")


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        destination / "landcover.tif",
        "w",
        driver="GTiff",
        height=CLASSES.shape[0],
        width=CLASSES.shape[1],
        count=1,
        dtype="uint8",
        crs=CRS,
        transform=from_origin(500000, 4600000, CELL, CELL),
    ) as ds:
        ds.write(CLASSES, 1)
        ds.update_tags(legend="1=forest, 2=urban, 3=water")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
