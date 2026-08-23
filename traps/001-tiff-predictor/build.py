"""Build a valid GeoTIFF whose bytes are horizontally differenced.

The file is ordinary. TIFF's horizontal predictor (tag 317 = 2) stores each
pixel as the difference from its left neighbour before compressing, because
differences of a smooth surface compress far better than the values themselves.
Undoing it on read is the reader's job, and it is not optional.

The elevations are chosen so that both the right answer and the wrong one can be
worked out on paper — see README.md. That is the point of a fixture that is
built rather than vendored: nothing here has to be taken on trust.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

HEIGHT = WIDTH = 32
WEST, NORTH, PIXEL = 500000.0, 5000000.0, 30.0  # UTM 32N, 30 m — SRTM-shaped
BASE, EAST_STEP, SOUTH_STEP = 1000, 4, 2


def elevations() -> np.ndarray:
    """A plateau tilting east and south. int16, like SRTM and most public DEMs.

    Integers matter: TIFF predictor 2 is defined for integer samples, so this is
    an ordinary file and not a malformed one. A reader that gets it wrong is not
    being fed something exotic.
    """
    row, column = np.mgrid[0:HEIGHT, 0:WIDTH]
    return (BASE + EAST_STEP * column + SOUTH_STEP * row).astype("int16")


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    grid = elevations()
    profile = dict(
        driver="GTiff", height=HEIGHT, width=WIDTH, count=1, dtype="int16",
        crs="EPSG:32632", nodata=-32768,
        transform=from_origin(WEST, NORTH, PIXEL, PIXEL),
    )
    # The trap: same pixels, stored differenced. A conforming reader returns
    # identical arrays from both files, and `dem_plain.tif` is here so that
    # anyone can check that in one line.
    with rasterio.open(destination / "dem_plain.tif", "w", **profile) as ds:
        ds.write(grid, 1)
    with rasterio.open(destination / "dem.tif", "w", **profile,
                       compress="deflate", predictor=2) as ds:
        ds.write(grid, 1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
