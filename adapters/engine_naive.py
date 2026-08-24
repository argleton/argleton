"""The compositions almost everyone writes first.

Read the file, take the statistic, report it. Not straw men and not bugs in the
libraries: Shapely computes planar area in the coordinates' own units by design
because nothing else can know the unit, and rasterio returns the raw array
unless you ask for the masked one. Each of these is three correct-looking lines,
each is what a great deal of published analysis code does, and each is right
whenever the data happens to be shaped the way it usually is.

They are in the repository because a suite that only measures careful systems
cannot show what the careless answer looks like, and the whole argument is that
the careless answer looks fine.
"""

from __future__ import annotations

from pathlib import Path

from argleton.model import Outcome, Probe


class Adapter:
    name = "naive-composition"

    def run(self, probe: Probe, workdir: Path) -> Outcome:
        operazione = getattr(self, f"op_{probe.operation}", None)
        if operazione is None:
            return Outcome(unsupported=True)
        return operazione(probe, workdir)

    def op_planar_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        return Outcome(answer=float(gpd.read_file(workdir / probe.arguments[0]).area.sum()))

    def op_raster_mean(self, probe: Probe, workdir: Path) -> Outcome:
        import rasterio

        with rasterio.open(workdir / probe.arguments[0]) as ds:
            # `read(1)` and `read(1, masked=True)` differ by one keyword, and
            # the raw array is the one you get by default.
            return Outcome(answer=float(ds.read(1).mean()))

    def op_points_in_polygon_count(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        points = gpd.read_file(workdir / probe.arguments[0])
        zone = gpd.read_file(workdir / probe.arguments[1]).geometry.iloc[0]
        # `within` against a bare geometry: there is no second CRS in sight,
        # so not even geopandas' own mismatch warning can fire.
        return Outcome(answer=int(points.within(zone).sum()))
