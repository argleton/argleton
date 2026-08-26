"""Build a two-band scene whose values are stored, not measured.

Band 1 is red, band 2 is near-infrared, both uint16 digital numbers with a
scale and an offset declared in the GeoTIFF's own metadata — the arrangement
every optical satellite archive uses, and the one Sentinel-2 changed under the
world's feet in January 2022 when it added a non-zero offset.

physical = raw * scale + offset  (the GDAL definition, and the one written in
the file). Red 3000 and NIR 5000 with scale 0.0001 and offset -0.1 are
reflectances of 0.2 and 0.4.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

CRS = "EPSG:32633"
CELL = 10.0
SCALE, OFFSET = 0.0001, -0.1
RED_DN, NIR_DN = 3000, 5000


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
        dtype="uint16",
        crs=CRS,
        transform=from_origin(500000, 4600000, CELL, CELL),
    ) as ds:
        ds.write(np.full(shape, RED_DN, dtype="uint16"), 1)
        ds.write(np.full(shape, NIR_DN, dtype="uint16"), 2)
        ds.scales = (SCALE, SCALE)
        ds.offsets = (OFFSET, OFFSET)
        ds.set_band_description(1, "red")
        ds.set_band_description(2, "nir")
        ds.update_tags(
            note="digital numbers; physical = raw * scale + offset",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
