"""Build the same question on a zone that does not touch the antimeridian.

The clean twin of 025-antimeridian-zone: the same five ships inside, the same
four in the latitude band elsewhere on the planet, the same three near the zone
but outside the band. One thing differs, and it is the thing under test — the
zone sits at 169E..171E instead of straddling 180.

That makes it an ordinary rectangle, so its bounding box IS the zone and the
bounding-box filter that gets the trap wrong is exactly right here. Both answers
are 5.

Without this twin, a silent-error rate on the family could not be told apart
from a system that cannot count points in a polygon at all — and a system that
has learned to distrust bounding boxes and now tests containment twice would
look identical to one that reads the geometry.
"""


from __future__ import annotations

import json
import sys
from pathlib import Path

#: The zone: 169E..171E, 17.5S..16.5S. Same size, same latitudes, ten degrees
#: west of the line.
SOUTH = -17.5
NORTH = -16.5
WEST = 169.0
EAST = 171.0

#: (name, longitude, latitude, is inside the zone, is inside its latitude band)
SHIPS = [
    # Inside: five, on both sides of the line.
    ("Vatoa", 169.30, -17.00, True, True),
    ("Ono-i-Lau", 169.80, -16.80, True, True),
    ("Tuvana", 170.10, -17.20, True, True),
    ("Ceva-i-Ra", 170.80, -16.90, True, True),
    ("Nukusemanu", 169.95, -17.40, True, True),
    # The same latitude band, elsewhere on the planet. A bounding-box filter
    # takes all four: they are between 17.5S and 16.5S, and the box is the whole
    # world in longitude.
    ("Bandanaira", 100.00, -17.00, False, True),
    ("Santa Helena", 0.00, -16.70, False, True),
    ("Iquique", -80.00, -17.30, False, True),
    ("Cairns Reef", 179.00, -16.60, False, True),
    # Near the antimeridian but outside the latitude band, so the box excludes
    # them too. Without these the wrong answer would be "every ship", which is
    # a shape somebody might notice.
    ("Kadavu South", 169.50, -20.00, False, False),
    ("Wallis", 170.50, -10.00, False, False),
    ("Minerva", 169.00, -30.00, False, False),
]


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)

    # One ring, because nothing needs splitting here. A MultiPolygon of one part
    # rather than a Polygon, so the two files differ in their coordinates and not
    # in their structure: the twin has to isolate the antimeridian, not the
    # geometry type.
    zone = {
        "type": "Feature",
        "properties": {"name": "Survey zone A"},
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
                [[[WEST, SOUTH], [EAST, SOUTH], [EAST, NORTH], [WEST, NORTH],
                  [WEST, SOUTH]]],
            ],
        },
    }
    (destination / "zone.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                # No "bbox" member, for symmetry with the trap: neither file
                # hands over the answer to the question it is asking.
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
