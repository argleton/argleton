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
        operation = getattr(self, f"op_{probe.operation}", None)
        if operation is None:
            return Outcome(unsupported=True)
        return operation(probe, workdir)

    def op_planar_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        return Outcome(answer=float(gpd.read_file(workdir / probe.arguments[0]).area.sum()))

    def op_ground_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # "How big is the parcel" gets the same three lines as any other area
        # question: read, sum .area, report. The shoelace runs in whatever
        # plane the file is in, and nobody asked the plane whether its metres
        # are metres of ground.
        return Outcome(answer=float(gpd.read_file(workdir / probe.arguments[0]).area.sum()))

    def op_class_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import rasterio
        from rasterio.enums import Resampling

        resolution = float(probe.arguments[1].split("=", 1)[1])
        wanted = int(probe.arguments[2].split("=", 1)[1])
        with rasterio.open(workdir / probe.arguments[0]) as ds:
            left, bottom, right, top = ds.bounds
            width = round((right - left) / resolution)
            height = round((top - bottom) / resolution)
            # `bilinear` is what a pipeline configured once for elevation applies
            # to everything, and what the resampling docs recommend for "continuous
            # data" — which nothing in a GeoTIFF says this is not.
            band = ds.read(
                1, out_shape=(1, height, width), resampling=Resampling.bilinear
            )
        cells = int((band == wanted).sum())
        return Outcome(answer=float(cells * resolution * resolution))

    def op_raster_mean(self, probe: Probe, workdir: Path) -> Outcome:
        import rasterio

        with rasterio.open(workdir / probe.arguments[0]) as ds:
            # `read(1)` and `read(1, masked=True)` differ by one keyword, and
            # the raw array is the one you get by default.
            return Outcome(answer=float(ds.read(1).mean()))

    def op_feature_count(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # No layer argument: "the file" gets read, and a multi-layer container
        # hands back its default layer. pyogrio warns on stderr; the returned
        # frame carries no trace, and this composition never looks.
        return Outcome(answer=len(gpd.read_file(workdir / probe.arguments[0])))

    def op_count_within_distance(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        frame = gpd.read_file(workdir / probe.arguments[0])
        target_id = probe.arguments[1].split("=", 1)[1]
        distance = float(probe.arguments[2].split("=", 1)[1])
        target = frame[frame["well_id"] == target_id].geometry.iloc[0]
        others = frame[frame["well_id"] != target_id]
        # buffer() works in the layer's own units, whatever they are. The
        # question said meters; nobody told the buffer.
        return Outcome(answer=int(others.within(target.buffer(distance)).sum()))

    def op_points_in_polygon_count(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        points = gpd.read_file(workdir / probe.arguments[0])
        zone = gpd.read_file(workdir / probe.arguments[1]).geometry.iloc[0]
        # `within` against a bare geometry: there is no second CRS in sight,
        # so not even geopandas' own mismatch warning can fire.
        return Outcome(answer=int(points.within(zone).sum()))
