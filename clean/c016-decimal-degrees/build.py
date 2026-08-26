"""Clean twin of 016: the same stations, already in decimal degrees.

41.89 is in the file as 41.89. Nothing to convert, nothing to get wrong.
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
    rows = [("ST-1", 41.89, 12.492222), ("ST-2", 45.46, 9.19), ("ST-3", 40.85, 14.27)]
    lines = ["station_id,latitude,longitude"]
    lines += [f"{i},{lat},{lon}" for i, lat, lon in rows]
    (destination / "stations.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
