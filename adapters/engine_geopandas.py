"""Engine adapter: GeoPandas / Shapely / pyproj, composed by a caller who knows.

The vector counterpart of `engine_rasterio`, and the pair to `engine_naive`.
Worth being exact about what it measures, because the name on the results table
is easy to over-read: **this is not a score for GeoPandas.** Shapely computes
planar area in whatever units the coordinates happen to be in and is unit-unaware
by design; `to_crs` hands its pair to pyproj and takes whatever comes back. What
this adapter measures is what a *competent caller* gets out of these libraries —
the unit read from the CRS rather than assumed, a geographic CRS refused for a
planar area, an invalid ring repaired and the repair disclosed, a metric distance
taken in a projected frame, a transformation checked for being a ballpark one.

`engine_naive` is the same libraries without any of that. The gap between the two
rows is the whole point, and neither row is a statement about the libraries: it
is a statement about the composition. The published label says
"(careful composition)" for the same reason — on 2026-08-26 the row read
"GeoPandas 1.1 + Shapely 2 | 0.00" and told a reader the library handles a case
it does not.
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

    def op_ground_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from pyproj import Geod

        frame = gpd.read_file(workdir / probe.arguments[0])
        if frame.crs is None:
            return Outcome(
                refusal="the layer declares no CRS, so its coordinates cannot be "
                "placed on the ground"
            )
        # Ground area is a property of the ellipsoid, not of any map plane:
        # take the geodesic area of the footprint. Measuring in a projected
        # CRS instead would answer with that projection's distortion — which
        # is exactly the failure this family measures.
        geoms = frame.to_crs("EPSG:4326").geometry
        warns = []
        if not geoms.is_valid.all():
            from shapely.validation import make_valid

            geoms = geoms.apply(make_valid)
            warns.append(
                "invalid geometry (self-intersection): repaired with make_valid before measuring"
            )
        geod = Geod(ellps="WGS84")
        total = sum(abs(geod.geometry_area_perimeter(g)[0]) for g in geoms)
        return Outcome(answer=float(total), warnings=warns)


    def op_ships_in_zone(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        import pandas as pd

        # Containment against the geometry itself, with no bounding box in the
        # way. Careful here is not cleverness about the antimeridian: it is
        # declining the optimisation, because the box of a geometry split at the
        # line is the whole planet and the filter is the failure.
        zone = gpd.read_file(workdir / probe.arguments[0])
        rows = pd.read_csv(workdir / probe.arguments[1])
        ships = gpd.GeoDataFrame(
            rows,
            geometry=gpd.points_from_xy(rows["longitude"], rows["latitude"]),
            crs="EPSG:4326",
        )
        return Outcome(answer=int(ships.within(zone.union_all()).sum()))

    def op_feature_count(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # The question names a layer, so the read does too. On a multi-layer
        # container this is the whole difference between 31 and 4.
        layer = probe.arguments[1].split("=", 1)[1]
        return Outcome(
            answer=len(gpd.read_file(workdir / probe.arguments[0], layer=layer))
        )

    def op_count_within_distance(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        frame = gpd.read_file(workdir / probe.arguments[0])
        target_id = probe.arguments[1].split("=", 1)[1]
        distance = float(probe.arguments[2].split("=", 1)[1])
        if frame.crs is None:
            return Outcome(refusal="the layer declares no CRS, so a metric distance is undefined")
        if frame.crs.is_geographic:
            # The question is metric and the layer is in degrees: project to
            # the local UTM zone before measuring anything in meters.
            frame = frame.to_crs(frame.estimate_utm_crs())
        target = frame[frame["well_id"] == target_id].geometry.iloc[0]
        others = frame[frame["well_id"] != target_id]
        return Outcome(answer=int((others.distance(target) <= distance).sum()))

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

    def op_wgs84_latitude(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from pyproj import CRS, Transformer
        from pyproj.transformer import TransformerGroup

        frame = gpd.read_file(workdir / probe.arguments[0])
        if frame.crs is None:
            return Outcome(refusal="the layer declares no CRS, so it cannot be transformed")
        point = frame.geometry.iloc[0]
        # `to_crs` is one line and it is wrong here, so this does what the other
        # nine operations in this file do: use the library properly rather than
        # first. Pick the transformation, then look at what was picked. PROJ
        # reports a ballpark with an accuracy of -1, and a ballpark means the
        # datums were treated as equivalent -- no shift, no warning, the latitude
        # returned unchanged.
        #
        # Fourteen lines, no manifest, no provenance format. That is what makes
        # trap 021 fair: it is beaten by a computation any engine can do, not by
        # a record only one product keeps.
        chosen = Transformer.from_crs(frame.crs, CRS("EPSG:4326"), always_xy=True)
        chosen.transform(point.x, point.y)
        used = chosen.get_last_used_operation()
        if used.accuracy is None or used.accuracy < 0:
            group = TransformerGroup(frame.crs, CRS("EPSG:4326"), always_xy=True)
            real = [t for t in group.transformers
                    if t.accuracy is not None and t.accuracy >= 0]
            if not real:
                return Outcome(
                    refusal="every available transformation to EPSG:4326 is a ballpark one, "
                    "so no datum shift can be applied and the answer would be the input"
                )
            out = real[0].transform(point.x, point.y)
            return Outcome(
                answer=float(out[1]),
                warnings=[
                    "the default transformation for this CRS is a ballpark one (accuracy -1, "
                    "no datum shift): used a published operation with stated accuracy "
                    f"{real[0].accuracy} m instead"
                ],
            )
        out = chosen.transform(point.x, point.y)
        return Outcome(answer=float(out[1]))

    def op_thiessen_value_mm(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # The Thiessen method IS nearest-neighbour assignment, so this asks that
        # question directly instead of building polygons and then asking which
        # one the site is in. Two lines, no ordering to get wrong, and correct
        # for the reason the method is defined -- which is what makes trap 022
        # fair: it is beaten by understanding the operation, not by a feature.
        gauges = gpd.read_file(workdir / probe.arguments[0])
        site = gpd.read_file(workdir / probe.arguments[1])
        field = probe.arguments[2]
        if gauges.crs is None or site.crs is None:
            return Outcome(refusal="a layer declares no CRS, so distances are not distances")
        if gauges.crs != site.crs:
            site = site.to_crs(gauges.crs)
        if gauges.crs.is_geographic:
            return Outcome(
                refusal="the layers are in a geographic CRS, where a nearest-neighbour "
                "distance would be measured in degrees"
            )
        target = site.geometry.iloc[0]
        distances = gauges.geometry.distance(target)
        nearest = distances.idxmin()
        # A tie would make the question ambiguous rather than hard, so say so
        # instead of picking one.
        second = distances.drop(index=nearest).min()
        if abs(second - distances[nearest]) < 1e-9:
            return Outcome(
                refusal="two gauges are equidistant from the site, so the Thiessen "
                "assignment is not unique"
            )
        return Outcome(answer=float(gauges.loc[nearest, field]))

    def op_parcel_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import csv

        from pyproj import Geod
        from shapely.geometry import Polygon

        # The header is the contract. A corner schedule can be written either
        # way round — EPSG:4326 declares latitude first and every geometry
        # library expects longitude first, and both conventions are current —
        # so the column NAMES decide, not their positions.
        with (workdir / probe.arguments[0]).open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        names = {name.strip().lower() for name in rows[0]}
        for lon_name, lat_name in (("longitude", "latitude"), ("lon", "lat"), ("x", "y")):
            if {lon_name, lat_name} <= names:
                break
        else:
            return Outcome(
                error="the corner schedule does not name its coordinate columns, "
                "so which one is longitude cannot be established"
            )
        ring = [(float(row[lon_name]), float(row[lat_name])) for row in rows]
        # Geodesic on the ellipsoid the CRS names: no map plane, so no
        # projection distortion enters the answer.
        return Outcome(answer=abs(Geod(ellps="WGS84").geometry_area_perimeter(
            Polygon(ring)
        )[0]))
