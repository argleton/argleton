"""The same parcel, the same square, the columns in the machine's order.

Identical footprint to 023-axis-order — the same 0.0012 degree square with its
south-west corner at longitude 23.7300, latitude 37.9800 — so the right answer
is the same number. The only thing that changed is which column comes first,
which is the one thing the trap is about.

A reader that takes the two columns in the order it finds them is correct here
and wrong there. A reader that reads the header is correct in both.
"""

from __future__ import annotations

import sys
from pathlib import Path

LON0 = 23.7300
LAT0 = 37.9800
SIDE = 0.0012


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)

    ring = [
        (LON0, LAT0),
        (LON0 + SIDE, LAT0),
        (LON0 + SIDE, LAT0 + SIDE),
        (LON0, LAT0 + SIDE),
        (LON0, LAT0),
    ]
    # Longitude first: the order shapefiles, GeoJSON and every geometry library
    # use, and the order OGC calls CRS84. Just as declared as the other one, and
    # just as common — which is the whole difficulty.
    lines = ["corner,longitude,latitude"]
    lines += [
        f"{index + 1},{lon:.4f},{lat:.4f}" for index, (lon, lat) in enumerate(ring)
    ]
    (destination / "parcel.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
