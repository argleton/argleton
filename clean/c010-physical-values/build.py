"""Clean twin of 010: the same question on a scene already in physical units.

Same two bands, same question, no scale and no offset to apply — the values in
the file are the reflectances. Red 0.2 and NIR 0.6 give an NDVI of 0.5, a
different number from the trap's so the two cannot be confused in a log.

A system that answers this and misses the trap can compute NDVI and ignores
declared scaling; a system that misses both cannot compute NDVI at all, which
is a different and lesser finding.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

CRS = "EPSG:32633"
CELL = 10.0
RED, NIR = 0.2, 0.6


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    shape = (4, 4)
    with rasterio.open(
        destination / "scene.tif",
        "w",
        driver="GTiff",
        height=shape[0],
        width=shape[1],
        count=2,
        dtype="float32",
        crs=CRS,
        transform=from_origin(500000, 4600000, CELL, CELL),
    ) as ds:
        ds.write(np.full(shape, RED, dtype="float32"), 1)
        ds.write(np.full(shape, NIR, dtype="float32"), 2)
        ds.set_band_description(1, "red")
        ds.set_band_description(2, "nir")
        ds.update_tags(note="surface reflectance, already in physical units")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
