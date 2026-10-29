from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("OGR_CURRENT_DATE", "2026-10-29T00:00:00.000Z")

import geopandas as gpd
from shapely.geometry import Point

CRS = "+proj=longlat +ellps=intl +towgs84=0,0,0 +no_defs +type=crs"


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        {"station_id": ["ST-1"]},
        geometry=[Point(8.952333333333333, 45.5)],
        crs=CRS,
    ).to_file(destination / "station.gpkg", layer="stations", driver="GPKG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
