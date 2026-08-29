"""Build the same field delivered in metres.

The clean twin of 028-degrees-as-metres: the same four corners, the same parcel,
the same 8.99 hectares. One thing differs and it is the thing under test — the
file is in UTM 33N... in EPSG:32632, a projected system whose unit is the metre,
so the coordinates are already a length and there is nothing to convert.

Written as a GeoPackage rather than GeoJSON, because GeoJSON is defined on WGS 84
and a projected GeoJSON would be the wrong kind of unusual: the pair has to
differ in the CRS of the data, not in whether the file bends its own format.
"""

from __future__ import annotations

import os

# GeoPackage is SQLite and SQLite stamps the file, so two builds of the same
# data differ in bytes unless the date is pinned. A fixture that is not
# byte-identical between builds cannot be checked by anyone.
os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-30T00:00:00.000Z")

import sys
from pathlib import Path

LON0 = 9.0000
LAT0 = 45.0000
DLON = 0.0038
DLAT = 0.0027


def main(destination: Path) -> int:
    import geopandas as gpd
    from shapely.geometry import Polygon

    destination.mkdir(parents=True, exist_ok=True)

    ring = [
        (LON0, LAT0),
        (LON0 + DLON, LAT0),
        (LON0 + DLON, LAT0 + DLAT),
        (LON0, LAT0 + DLAT),
        (LON0, LAT0),
    ]
    # The same corners, converted once here so the two files describe one parcel
    # rather than two similar ones.
    gpd.GeoDataFrame(
        [{"parcel_id": "F-114", "crop": "maize"}],
        geometry=[Polygon(ring)],
        crs="EPSG:4326",
    ).to_crs("EPSG:32632").to_file(
        destination / "field.gpkg", layer="parcels", driver="GPKG"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
