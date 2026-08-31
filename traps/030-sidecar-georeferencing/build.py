"""Build a GeoTIFF whose own georeferencing disagrees with the sidecar beside it.

Two files. `terrain.tif` says it starts at (500000, 5030000) with 10 m pixels;
`terrain.tif.aux.xml` says (600000, 5040000) with 20 m pixels. Both are ordinary
artefacts: a `.aux.xml` is what GDAL writes when someone assigns georeferencing
to a raster that had none or corrects one that was wrong, and it is the reason
the sidecar takes precedence by default — an override that a user chose has to
beat the file it overrides, or overriding would not work.

So the file is not malformed, the sidecar is not malformed, and GDAL's
precedence is documented and deliberate. What is missing is anywhere in the
answer that says which of the two was used.

Nothing here is committed: the fixture is generated, and a test enforces that
two builds are byte-identical.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

#: 20 x 20 cells. Small enough to check by hand, big enough that a whole-raster
#: area is a number somebody would report rather than eyeball.
SIZE = 20

#: What the GeoTIFF itself declares. Ten-metre cells at a plausible UTM origin.
INTERNAL_ORIGIN = (500000.0, 5030000.0)
INTERNAL_CELL = 10.0

#: What the sidecar declares instead: a different origin a hundred kilometres
#: away and cells twice as wide. Twice the cell is four times the area, which is
#: the number the task asks for.
SIDECAR_ORIGIN = (600000.0, 5040000.0)
SIDECAR_CELL = 20.0

CRS = "EPSG:32632"

#: The sidecar, written by hand rather than by GDAL so the fixture cannot drift
#: with a library version. This is exactly the shape GDAL's PAM writes: a WKT
#: for the coordinate system and a six-element GeoTransform in the documented
#: order (origin x, pixel width, row rotation, origin y, column rotation, pixel
#: height — negative because rows run north to south).
AUX_XML = """<PAMDataset>
  <SRS dataAxisToSRSAxisMapping="1,2">PROJCS["WGS 84 / UTM zone 32N",\
GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,\
AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],\
PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],\
UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],\
AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],\
PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",9],\
PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],\
PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],\
AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","32632"]]</SRS>
  <GeoTransform> {ox},  {cell},  0.0,  {oy},  0.0, -{cell}</GeoTransform>
</PAMDataset>
"""


def main(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)

    # A gentle ramp. The values are not what the task asks about, but a raster
    # of constant zeros would look like a placeholder and invite doubt for the
    # wrong reason.
    values = np.tile(np.arange(SIZE, dtype="float32"), (SIZE, 1)) + 100.0

    raster = target / "terrain.tif"
    with rasterio.open(
        raster, "w", driver="GTiff", height=SIZE, width=SIZE, count=1,
        dtype="float32", crs=CRS,
        transform=Affine(
            INTERNAL_CELL, 0.0, INTERNAL_ORIGIN[0],
            0.0, -INTERNAL_CELL, INTERNAL_ORIGIN[1],
        ),
    ) as destination:
        destination.write(values, 1)

    (target / "terrain.tif.aux.xml").write_text(
        AUX_XML.format(
            ox=SIDECAR_ORIGIN[0], oy=SIDECAR_ORIGIN[1], cell=SIDECAR_CELL
        ),
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
