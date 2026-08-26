"""Build a station list whose coordinates are degrees, minutes and seconds.

41 deg 53 min 24 s north is 41 + 53/60 + 24/3600 = 41.89 exactly: 3204/3600
divides out, which is why these numbers were chosen. Read the fields as though
they were already decimal and you get 41.5324 — off by 0.36 degrees, about
40 km, and still a latitude in central Italy.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("OGR_CURRENT_DATE", "2026-08-26T00:00:00.000Z")

pass  # this fixture is a CSV: no geometry library needed

CRS = "EPSG:32632"


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    rows = [
        ("ST-1", 41, 53, 24, "N", 12, 29, 32, "E"),
        ("ST-2", 45, 27, 36, "N", 9, 11, 24, "E"),
        ("ST-3", 40, 51, 0, "N", 14, 16, 12, "E"),
    ]
    lines = ["station_id,lat_deg,lat_min,lat_sec,lat_hem,lon_deg,lon_min,lon_sec,lon_hem"]
    lines += [",".join(str(v) for v in r) for r in rows]
    (destination / "stations.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
