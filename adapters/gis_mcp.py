"""Adapter: gis-mcp (mahdin75/gis-mcp) — 92+ tools wrapping Shapely, PyProj,
GeoPandas, Rasterio and PySAL.

Measured because it is the natural counterpoint to MapSmith's shape — many thin
tools, no provenance — and because a suite that only measures its own author is
not a suite. The adapter calls the package's own tool functions (FastMCP wraps
them in ``FunctionTool``, the implementation is ``.fn``) with the arguments an
MCP client would pass.

One composition is worth flagging before the numbers: gis-mcp's only area tool,
``get_area``, takes a bare WKT string — an interface with no place for a CRS or
a unit. The adapter does the file-to-WKT step itself and says so here; the
measured behaviour (a unit-blind area) is the tool's contract, not the glue
around it.
"""

from __future__ import annotations

from pathlib import Path

from argleton.model import Outcome, Probe


class Adapter:
    name = "gis-mcp"

    def run(self, probe: Probe, workdir: Path) -> Outcome:
        operation = getattr(self, f"op_{probe.operation}", None)
        if operation is None:
            return Outcome(unsupported=True)
        return operation(probe, workdir)

    def op_raster_mean(self, probe: Probe, workdir: Path) -> Outcome:
        from gis_mcp.rasterio_functions import raster_band_statistics

        result = raster_band_statistics.fn(str(workdir / probe.arguments[0]))
        return Outcome(answer=float(result["statistics"]["Band 1"]["mean"]))

    def op_planar_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from gis_mcp.shapely_functions import get_area

        # The reading happens outside the server, and whatever the layer knew
        # about its unit does not fit through a WKT string.
        geometry = gpd.read_file(workdir / probe.arguments[0]).geometry.iloc[0]
        result = get_area.fn(geometry.wkt)
        return Outcome(answer=float(result["area"]))

    def op_ground_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from gis_mcp.pyproj_functions import calculate_geodetic_area, project_geometry

        # The charitable composition, like the geodetic distance in 007:
        # gis-mcp has the right tools for this question — project_geometry to
        # get the footprint into lon/lat, then calculate_geodetic_area. The
        # glue reads the file and carries the CRS between the two calls,
        # because no gis-mcp tool returns a geometry together with its CRS.
        # (Worth recording: calculate_geodetic_area fed projected coordinates
        # directly returns area=NaN wrapped in status='success'.)
        frame = gpd.read_file(workdir / probe.arguments[0])
        wkt = frame.geometry.iloc[0].wkt
        if frame.crs is not None and str(frame.crs).upper() not in ("EPSG:4326", "OGC:CRS84"):
            wkt = project_geometry.fn(wkt, str(frame.crs), "EPSG:4326")["geometry"]
        result = calculate_geodetic_area.fn(wkt)
        return Outcome(answer=float(result["area"]))

    def op_feature_count(self, probe: Probe, workdir: Path) -> Outcome:
        from gis_mcp.geopandas_functions import read_file_gpd

        # gis-mcp's reader takes a path and nothing else — no tool in the set
        # can name the layer the question names — so the composition is the
        # bare read, and num_rows is whatever layer the container defaults to.
        result = read_file_gpd.fn(str(workdir / probe.arguments[0]))
        return Outcome(answer=int(result["num_rows"]))

    def op_count_within_distance(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # The charitable composition, on purpose: gis-mcp also ships a
        # units-blind buffer, but its geodetic-distance tool is the right
        # instrument for a metric question on geographic coordinates, and a
        # careful client would reach for it. On projected data the plain
        # planar distance is already in the right unit.
        frame = gpd.read_file(workdir / probe.arguments[0])
        target_id = probe.arguments[1].split("=", 1)[1]
        distance = float(probe.arguments[2].split("=", 1)[1])
        target = frame[frame["well_id"] == target_id].geometry.iloc[0]
        others = frame[frame["well_id"] != target_id]
        if frame.crs is not None and frame.crs.is_geographic:
            from gis_mcp.pyproj_functions import calculate_geodetic_distance

            count = 0
            for geometry in others.geometry:
                measured = calculate_geodetic_distance.fn(
                    [target.x, target.y], [geometry.x, geometry.y]
                )
                count += measured["distance"] <= distance
            return Outcome(answer=int(count))
        return Outcome(answer=int((others.distance(target) <= distance).sum()))

    def op_points_in_polygon_count(self, probe: Probe, workdir: Path) -> Outcome:
        from gis_mcp.geopandas_functions import sjoin_gpd

        # Not `point_in_polygon`: that tool returns every point with the join
        # outcome as columns (36 features for the 9-inside control), which is a
        # defensible contract but not a count. The first adapter draft read its
        # `num_features` as the answer and wrongly scored the CLEAN control as a
        # silent error — the trap-002 lesson again, caught the same way: when a
        # system fails the control, suspect the adapter first. An inner
        # within-join answers the question asked.
        result = sjoin_gpd.fn(
            str(workdir / probe.arguments[0]),
            str(workdir / probe.arguments[1]),
            how="inner",
            predicate="within",
        )
        return Outcome(answer=int(result["num_features"]))
