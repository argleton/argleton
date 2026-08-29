"""Build a field delivered in degrees, as most open data is.

`field.geojson` is one rectangular parcel in WGS 84 (EPSG:4326), in the Po
valley at 45 degrees north: 0.0038 degrees of longitude by 0.0027 of latitude.
On the ground that is 299 m by 300 m and 8.99 hectares.

Nothing about the file is unusual. GeoJSON is defined on WGS 84 and RFC 7946
says so; almost every open dataset, every web API and every hand-drawn polygon
arrives exactly like this.

What the file does not carry is a length. Shapely computes area in the
coordinates' own units by design, because nothing else can know what they are,
so asking this parcel for its area returns a number in square DEGREES. It has to
be converted, and the conversion everyone reaches for is one factor:

    area_in_degrees * 111320 ** 2

111320 m is one degree at the equator. It is right for latitude almost
everywhere and right for longitude only on the equator, because a degree of
longitude shrinks with the cosine of the latitude. At 45 degrees it has shrunk
to 0.7071 of its equatorial length, so the answer comes back 1.4142 times too
large — and 45 degrees is chosen for that: the ratio is the square root of two,
exactly, which is the size of error that is much too small to look absurd.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

#: South-west corner and extent, in degrees. Written out rather than computed so
#: the file and the derivation in probe.toml cannot drift apart.
LON0 = 9.0000
LAT0 = 45.0000
DLON = 0.0038
DLAT = 0.0027


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)

    ring = [
        [LON0, LAT0],
        [LON0 + DLON, LAT0],
        [LON0 + DLON, LAT0 + DLAT],
        [LON0, LAT0 + DLAT],
        [LON0, LAT0],
    ]
    (destination / "field.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"parcel_id": "F-114", "crop": "maize"},
                        "geometry": {"type": "Polygon", "coordinates": [ring]},
                    }
                ],
            },
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
