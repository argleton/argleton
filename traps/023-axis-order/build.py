"""Build a corner schedule whose columns are latitude first, as EPSG:4326 says.

The parcel is an axis-aligned square in degrees: 0.0012 deg on each side, its
south-west corner at longitude 23.7300, latitude 37.9800, in Athens. Both facts
matter.

Square IN DEGREES, so swapping the two coordinates does not change the shape of
the footprint at all — the same 0.0012 x 0.0012 window, moved from latitude
37.98 to latitude 23.73. The entire error is which parallel it sits on, which is
why the wrong answer is the right answer scaled by one ratio and nothing else.

Athens because 23.73 and 37.98 are both valid as either coordinate: nothing in
the swapped reading is out of range, out of the hemisphere, or in the sea. The
swapped parcel lands in the Egyptian desert, which no one sees, because the
question asks for an area.
"""

from __future__ import annotations

import sys
from pathlib import Path

#: South-west corner and side, in degrees. Written out rather than computed so
#: the file and the derivation cannot drift apart.
LON0 = 23.7300
LAT0 = 37.9800
SIDE = 0.0012


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)

    # Anticlockwise from the south-west corner, closing the ring — the order a
    # surveyor writes a corner schedule in, and the order a reader will use.
    ring = [
        (LAT0, LON0),
        (LAT0, LON0 + SIDE),
        (LAT0 + SIDE, LON0 + SIDE),
        (LAT0 + SIDE, LON0),
        (LAT0, LON0),
    ]

    # LATITUDE FIRST, and the header says so. That is the order EPSG:4326 itself
    # declares — the authority definition puts the north axis first — and the
    # order every human convention uses, from a GPS readout to a map pin. It is
    # also the order INSPIRE and WFS 1.1 mandate on the wire. The machine
    # convention is the other one.
    lines = ["corner,latitude,longitude"]
    lines += [
        f"{index + 1},{lat:.4f},{lon:.4f}" for index, (lat, lon) in enumerate(ring)
    ]
    (destination / "parcel.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
