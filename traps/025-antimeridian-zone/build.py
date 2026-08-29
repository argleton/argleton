"""Build a survey zone that straddles the 180th meridian, and ships to count in it.

The zone is 2 degrees of longitude wide and 1 degree of latitude tall, centred on
the antimeridian in Fijian waters: longitude 179E to 179W, latitude 17.5S to
16.5S. There is nothing unusual about it on the ground. It is 213 km across.

**It is written the way the standard says to write it.** RFC 7946 section 3.1.9
states that a geometry crossing the antimeridian SHOULD be split into two parts
at it, so `zone.geojson` is a MultiPolygon of exactly two rectangles —
[179, 180] and [-180, -179] — and there is no ambiguity anywhere in the file
about which 2 degrees are meant. Every coordinate is inside the [-180, 180] range
the same document requires.

The trap is what that shape does to a bounding box. The two parts touch the range
limits from opposite ends, so the MultiPolygon's bounds are

    (-180.0, -17.5, 180.0, -16.5)

which is a band right around the planet. Any composition that filters by the
bounds of the area of interest before testing containment — `gdf.cx[minx:maxx,
miny:maxy]`, a tile query, a `WHERE` clause on min/max columns — accepts every
ship at that latitude, anywhere on Earth.

So the ships are placed to make that visible as a count rather than as a map:
five inside the zone, four in the same latitude band but scattered across the
Pacific, the Indian Ocean and the Atlantic, and three near the antimeridian but
outside the latitude band. A bounding-box filter answers nine. Nine is a
perfectly ordinary number of ships.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

#: The zone: 179E..179W, 17.5S..16.5S. Written out rather than computed so the
#: file and the derivation in probe.toml cannot drift apart.
SOUTH = -17.5
NORTH = -16.5
WEST = 179.0
EAST = -179.0

#: (name, longitude, latitude, is inside the zone, is inside its latitude band)
SHIPS = [
    # Inside: five, on both sides of the line.
    ("Vatoa", 179.30, -17.00, True, True),
    ("Ono-i-Lau", 179.80, -16.80, True, True),
    ("Tuvana", -179.90, -17.20, True, True),
    ("Ceva-i-Ra", -179.20, -16.90, True, True),
    ("Nukusemanu", 179.95, -17.40, True, True),
    # The same latitude band, elsewhere on the planet. A bounding-box filter
    # takes all four: they are between 17.5S and 16.5S, and the box is the whole
    # world in longitude.
    ("Bandanaira", 100.00, -17.00, False, True),
    ("Santa Helena", 0.00, -16.70, False, True),
    ("Iquique", -80.00, -17.30, False, True),
    ("Cairns Reef", 150.00, -16.60, False, True),
    # Near the antimeridian but outside the latitude band, so the box excludes
    # them too. Without these the wrong answer would be "every ship", which is
    # a shape somebody might notice.
    ("Kadavu South", 179.50, -20.00, False, False),
    ("Wallis", -179.50, -10.00, False, False),
    ("Minerva", 179.00, -30.00, False, False),
]


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)

    # Split at the antimeridian, as RFC 7946 3.1.9 prescribes: two rings, each
    # entirely within one hemisphere, each with coordinates in [-180, 180].
    zone = {
        "type": "Feature",
        "properties": {"name": "Survey zone A"},
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
                [[[WEST, SOUTH], [180.0, SOUTH], [180.0, NORTH], [WEST, NORTH],
                  [WEST, SOUTH]]],
                [[[-180.0, SOUTH], [EAST, SOUTH], [EAST, NORTH], [-180.0, NORTH],
                  [-180.0, SOUTH]]],
            ],
        },
    }
    (destination / "zone.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                # No "bbox" member: the file must not hand over the answer to
                # the question it is asking, and RFC 7946 5.2 would have it read
                # (179.0, -17.5, -179.0, -16.5) with west greater than east.
                "features": [zone],
            },
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = ["name,longitude,latitude"]
    lines += [f"{name},{lon:.2f},{lat:.2f}" for name, lon, lat, _, _ in SHIPS]
    (destination / "ships.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
