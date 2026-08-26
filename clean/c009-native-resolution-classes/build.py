"""Clean twin of 009: the same question where the urban class is really there.

Same legend, same CRS, already on the 15 m grid the question asks for, and
four cells genuinely coded urban. A system that can read a class map and add
up the area of one class answers 900; the trap's answer is zero. Without this
twin, a zero on the trap could not be told apart from "cannot do the task".
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

CRS = "EPSG:32633"
CELL = 15.0
# Four genuinely urban cells (2), the rest forest and water.
CLASSES = np.array(
    [
        [1, 1, 2, 3],
        [1, 1, 2, 3],
        [1, 1, 2, 3],
        [1, 1, 2, 3],
    ],
    dtype="uint8",
)


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
