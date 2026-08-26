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

    def op_ndvi_mean(self, probe: Probe, workdir: Path) -> Outcome:
        # gis-mcp ships no band-math or index tool: composing one here out of
        # numpy would measure numpy. Resolved at call time rather than assumed,
        # so the day they add one this adapter picks it up.
        try:
            from gis_mcp import rasterio_functions
        except ImportError:
            return Outcome(unsupported=True)
        for name in ("calculate_ndvi", "band_math", "raster_algebra", "raster_calculator"):
            if hasattr(rasterio_functions, name):
                break
        else:
            return Outcome(unsupported=True)
        return Outcome(unsupported=True)

    def op_class_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # Charitable composition (their own tools, at their best): gis-mcp wraps
        # rasterio, so the reader is theirs and the resampling choice is the
        # caller's. Whether a resample tool exists in the set is resolved at
        # call time rather than assumed: if it does not, the honest verdict is
        # unsupported, not a number produced by glue we wrote.
        try:
            from gis_mcp.rasterio_functions import resample_raster
        except ImportError:
            return Outcome(unsupported=True)

        import rasterio

        resolution = float(probe.arguments[1].split("=", 1)[1])
        wanted = int(probe.arguments[2].split("=", 1)[1])
        source = workdir / probe.arguments[0]
        destination = workdir / "_argleton_resampled.tif"
        # Their tool takes a scale factor for width/height, not a target cell
        # size, so the glue converts: the question asks for a 15 m grid and the
        # source is 20 m, hence 20/15. Their `resampling` argument, like ours,
        # has NO default — the caller must state it, and a caller told the
        # legend states a categorical method. Same charity as trap 007.
        with rasterio.open(source) as ds:
            scale = abs(float(ds.res[0])) / resolution
        try:
            resample_raster.fn(
                source=str(source),
                scale_factor=scale,
                resampling="nearest",
                destination=str(destination),
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            return Outcome(error=f"{type(exc).__name__}: {exc}")

        import numpy as np
        import rasterio

        with rasterio.open(destination) as ds:
            band = ds.read(1)
            cell = abs(float(ds.res[0])) * abs(float(ds.res[1]))
        return Outcome(answer=float(int(np.sum(band == wanted)) * cell))

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

    def op_wgs84_latitude(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from gis_mcp.pyproj_functions import project_geometry
        from shapely import wkt as shapely_wkt

        # gis-mcp has the right tool for this question: `project_geometry`. This
        # is the charitable composition D-035 asks for -- their dedicated tool,
        # called the way their documentation shows.
        frame = gpd.read_file(workdir / probe.arguments[0])
        if frame.crs is None:
            return Outcome(refusal="the layer declares no CRS")
        result = project_geometry.fn(
            frame.geometry.iloc[0].wkt, str(frame.crs), "EPSG:4326"
        )
        if not isinstance(result, dict) or "geometry" not in result:
            return Outcome(error=f"project_geometry returned {result!r}")
        return Outcome(answer=float(shapely_wkt.loads(result["geometry"]).y))
