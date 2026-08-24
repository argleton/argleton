"""Engine adapter: GeoPandas / Shapely / pyproj, called directly.

The vector counterpart of `engine_rasterio`. Worth being explicit about what
this measures: Shapely computes planar area in whatever units the coordinates
happen to be in, and is unit-unaware by design. So this adapter is not testing
Shapely — it is testing the ordinary composition a caller writes, which is where
the unit is either read from the CRS or assumed.
"""

from __future__ import annotations

from pathlib import Path

from argleton.model import Outcome, Probe


class Adapter:
    name = "geopandas"

    def run(self, probe: Probe, workdir: Path) -> Outcome:
        operation = getattr(self, f"op_{probe.operation}", None)
        if operation is None:
            return Outcome(unsupported=True)
        return operation(probe, workdir)

    def op_planar_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        frame = gpd.read_file(workdir / probe.arguments[0])
        if frame.crs is None:
            return Outcome(refusal="the layer declares no CRS, so its linear unit is unknown")
        if not frame.crs.is_projected:
            return Outcome(
                refusal="the layer is in a geographic CRS, so a planar area would be "
                "in square degrees, not square metres"
            )
        # Read the unit; do not reproject. Reprojecting to compute an area is a
        # second source of error on top of the one being measured: UTM is
        # conformal, not equal-area, and this parcel comes out 50 m2 lighter
        # there. The conversion factor is exact and answers the question asked.
        factor = frame.crs.axis_info[0].unit_conversion_factor
        geoms = frame.geometry
        warns = []
        if not geoms.is_valid.all():
            # On a self-intersecting ring, .area returns the signed-shoelace
            # artifact with no exception and no warning — a number that matches
            # no definition of the region. Repair first, and say so: measuring
            # after a silent repair would be trading one silence for another.
            from shapely.validation import make_valid

            geoms = geoms.apply(make_valid)
            warns.append(
                "invalid geometry (self-intersection): repaired with make_valid before measuring"
            )
        return Outcome(answer=float(geoms.area.sum() * factor**2), warnings=warns)

    def op_points_in_polygon_count(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        points = gpd.read_file(workdir / probe.arguments[0])
        zones = gpd.read_file(workdir / probe.arguments[1])
        if points.crs is None or zones.crs is None:
            return Outcome(refusal="a layer declares no CRS, so the two frames cannot be aligned")
        if points.crs != zones.crs:
            # Bring both into one frame before testing containment. Containment
            # is invariant under a correct transform, so which frame wins does
            # not matter; that it is a single frame is the whole job.
            points = points.to_crs(zones.crs)
        return Outcome(answer=int(points.within(zones.geometry.iloc[0]).sum()))
