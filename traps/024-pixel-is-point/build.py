"""Build a DEM that declares its values are at grid nodes, not in grid cells.

A shallow bowl, 8 by 8 nodes at 30 m spacing, with exactly one lowest point at
node (row 2, column 3). The elevation model is

    z = 300 + 0.5 * ((column - 3)^2 + (row - 2)^2)

so the minimum is strict — every neighbour is at least 0.5 m higher — and the
question "where is the bottom of this hollow" has one answer and no argument
about it.

The one thing that matters is the tag. `AREA_OR_POINT=Point` says the value of
a pixel is a sample AT the tie point of that pixel, not an average over the cell
around it. Under that reading the tie point (412000, 5108000) is the position of
the value in pixel (0, 0) itself, so the value in pixel (2, 3) sits at

    412000 + 3 * 30 = 412090,  5108000 - 2 * 30 = 5107940

and not half a cell south-east of there. Fifteen metres, in a file that says so.

30 m spacing and `Point` together are not a contrivance: they are what the USGS
elevation products have used for decades, which is where most people meet this.
"""

from __future__ import annotations

import sys
from pathlib import Path

#: Tie point, spacing and size. Written out rather than derived so that the file
#: and the derivation in probe.toml cannot drift apart.
EAST0 = 412000.0
NORTH0 = 5108000.0
SPACING = 30.0
SIZE = 8

#: Where the bottom of the hollow is, in grid indices.
LOW_ROW = 2
LOW_COLUMN = 3
LOW_ELEVATION = 300.0


def main(destination: Path) -> int:
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin

    destination.mkdir(parents=True, exist_ok=True)

    rows, columns = np.mgrid[0:SIZE, 0:SIZE]
    surface = LOW_ELEVATION + 0.5 * (
        (columns - LOW_COLUMN) ** 2 + (rows - LOW_ROW) ** 2
    )

    path = destination / "hollow.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=SIZE,
        width=SIZE,
        count=1,
        dtype="float32",
        crs="EPSG:32632",
        transform=from_origin(EAST0, NORTH0, SPACING, SPACING),
    ) as dst:
        dst.write(surface.astype("float32"), 1)
        # The whole trap, in one line of metadata. GeoTIFF calls it
        # RasterPixelIsPoint; GDAL surfaces it as this tag and leaves the
        # geotransform alone, which is documented and is exactly why the caller
        # has to do something about it.
        dst.update_tags(AREA_OR_POINT="Point")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
