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
        # The charitable composition, and until 2026-09-04 this method was not
        # it. It read the file and handed get_area the bare WKT -- which is the
        # three-line function the traps describe, not the careful caller D-035
        # asks this adapter to be. The same file already used the careful path
        # for 007, 008 and 028, so the rule was being applied to some rows and
        # not others; three independent reviewers of the maintainer notice
        # caught it. With gis-mcp's own tools a careful caller gets both traps
        # this method serves right: read_file_gpd reports the CRS, and where
        # its unit is not the metre, project_geometry to the same projection in
        # metres before get_area (002: 92,903.41); is_valid then make_valid
        # before get_area on a ring that is not simple (005: 5,100). What is
        # still true of the interface -- get_area has no place for a unit and
        # no validity flag -- is recorded in the trap READMEs, not measured as
        # a silent error here.
        return Outcome(answer=self._careful_area(workdir / probe.arguments[0]))

    def _careful_area(self, path: Path) -> float:
        """Planar area in square metres, the way a careful gis-mcp caller gets it.

        Every decision is made by one of their tools; the glue only reads the
        file (their reader returns a preview, not the geometry) and carries
        the CRS between calls, because no gis-mcp tool returns a geometry with
        its CRS attached.
        """
        import re

        import geopandas as gpd
        from gis_mcp.pyproj_functions import project_geometry
        from gis_mcp.shapely_functions import get_area, is_valid, make_valid

        frame = gpd.read_file(path)
        wkt = frame.geometry.iloc[0].wkt
        crs = frame.crs
        if crs is not None and not crs.is_geographic:
            unit = crs.axis_info[0].unit_name
            if unit not in ("metre", "meter", "m"):
                # The same projection with +units=m: the unit is the only
                # thing that changes, so a planar area comes back planar.
                proj = crs.to_proj4()
                twin = (
                    re.sub(r"\+units=\S+", "+units=m", proj)
                    if "+units=" in proj
                    else proj + " +units=m"
                )
                wkt = project_geometry.fn(wkt, crs.to_string(), twin)["geometry"]
        if not is_valid.fn(wkt).get("is_valid", True):
            wkt = make_valid.fn(wkt)["geometry"]
        return float(get_area.fn(wkt)["area"])

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

    def op_thiessen_value_mm(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # The charitable composition again, and here the charity is load-bearing:
        # gis-mcp ships BOTH routes. `shapely_functions.voronoi` builds the cells
        # and is the one that walks into the trap; `sjoin_nearest_gpd` is the
        # right instrument for a Thiessen assignment, since the method IS
        # nearest-neighbour, and a careful client would reach for it. The rule
        # recorded in the internal register applies: where they have the right
        # tool, we use it. This is the harder criterion for us, not the softer
        # one -- MapSmith's own adapter takes the polygon route and only passes
        # because its operation verifies the pairing.
        from gis_mcp.geopandas_functions import sjoin_nearest_gpd

        field = probe.arguments[2]
        output = workdir / "_gis_mcp_nearest.gpkg"
        result = sjoin_nearest_gpd.fn(
            left_path=str(workdir / probe.arguments[1]),
            right_path=str(workdir / probe.arguments[0]),
            output_path=str(output),
        )
        if result.get("status") != "success":
            return Outcome(error=str(result.get("message", result)))
        frame = gpd.read_file(output)
        if frame.empty or field not in frame.columns:
            return Outcome(error="the nearest join carried no reading for the site")
        return Outcome(answer=float(frame[field].iloc[0]))

    # ---------------------------------------------------------------- traps
    # added after 2026-08-28. Nine arrived and this adapter had a method for
    # none of them, so all nine came back `unsupported` -- which METHOD.md
    # defines as "the adapter does not implement the operation", a statement
    # about THIS FILE and not about gis-mcp. Read as a coverage gap it would
    # have overstated the case by seven probes: five of the seven below are
    # answered correctly with gis-mcp's own tools. Two are genuine gaps and
    # say so at the bottom.

    def op_parcel_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import csv

        from gis_mcp.pyproj_functions import calculate_geodetic_area

        # `calculate_geodetic_area` is the right instrument for a ground area
        # from lon/lat and gis-mcp has it, so this is the same charitable
        # choice made for 008. Which column is which is decided by the HEADER
        # rather than by position: no gis-mcp tool reads CSV, so that step is
        # glue, and glue written carelessly measures itself instead of the
        # system.
        with (workdir / probe.arguments[0]).open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        names = {name.strip().lower(): name for name in rows[0]}
        if not {"longitude", "latitude"} <= set(names):
            return Outcome(unsupported=True)
        ring = [
            (float(row[names["longitude"]]), float(row[names["latitude"]]))
            for row in rows
        ]
        wkt = "POLYGON ((" + ", ".join(f"{x} {y}" for x, y in ring) + "))"
        return Outcome(answer=float(calculate_geodetic_area.fn(wkt)["area"]))

    def op_ships_in_zone(self, probe: Probe, workdir: Path) -> Outcome:
        import csv
        import json

        import geopandas as gpd
        from gis_mcp.geopandas_functions import point_in_polygon

        # Their tool takes two paths and writes a third, so the glue only
        # turns the CSV into something spatial -- again, no gis-mcp tool reads
        # CSV. Deliberately NO bounding-box prefilter: the trap is what a bbox
        # does to a zone split at the antimeridian, and adding one here would
        # be this adapter failing the probe rather than gis-mcp. The result is
        # a left join, so the count is the rows that matched.
        with (workdir / probe.arguments[1]).open(encoding="utf-8") as handle:
            ships = list(csv.DictReader(handle))
        collection = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": ship["name"]},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(ship["longitude"]),
                            float(ship["latitude"]),
                        ],
                    },
                }
                for ship in ships
            ],
        }
        points = workdir / "_ships_for_gis_mcp.geojson"
        points.write_text(json.dumps(collection), encoding="utf-8")
        joined = workdir / "_ships_in_zone.geojson"
        point_in_polygon.fn(str(points), str(workdir / probe.arguments[0]), str(joined))
        result = gpd.read_file(joined)
        return Outcome(answer=int(result["index_right"].notna().sum()))

    def op_pipe_length_total_m(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from gis_mcp.shapely_functions import get_geometry_type, get_length

        # Which rows are pipe is a decision, and gis-mcp has the tool that
        # informs it: `get_geometry_type`. So the composition asks it per
        # feature and sums `get_length` only over the lines, which is what a
        # careful caller with this toolset would write. The glue reads the
        # container because their reader returns a truncated `preview` rather
        # than the geometries.
        assets = gpd.read_file(workdir / probe.arguments[0])
        total = 0.0
        for geometry in assets.geometry:
            kind = get_geometry_type.fn(geometry.wkt).get("type", "")
            if "LineString" in str(kind):
                total += float(get_length.fn(geometry.wkt)["length"])
        return Outcome(answer=total)

    def op_field_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from gis_mcp.pyproj_functions import calculate_geodetic_area

        # Two tools, and WHICH one is the whole question. On a geographic CRS
        # `get_area` returns square degrees, so the ellipsoidal tool is the
        # right one; on a projected CRS the planar area is already in metres
        # and `calculate_geodetic_area` is the wrong one -- fed projected
        # coordinates it returns `area: NaN` inside `status: "success"`, which
        # is recorded at the top of this file and which the clean twin catches
        # at once. Picking by the CRS gets both right; picking a favourite
        # gets one of them wrong in silence.
        from gis_mcp.shapely_functions import get_area

        field = gpd.read_file(workdir / probe.arguments[0])
        wkt = field.geometry.iloc[0].wkt
        if field.crs is not None and not field.crs.is_geographic:
            return Outcome(answer=float(get_area.fn(wkt)["area"]))
        return Outcome(answer=float(calculate_geodetic_area.fn(wkt)["area"]))

    def op_workable_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from gis_mcp.shapely_functions import difference, get_area

        # Both tools are theirs, and the only decision the glue makes is the
        # argument order -- which IS the trap, so it is taken from the
        # question ("of the concession, outside the reserve") and not from the
        # order the files happen to be listed in. Both layers are projected,
        # so a planar area is already in metres.
        concession = gpd.read_file(workdir / probe.arguments[0]).geometry.iloc[0]
        reserve = gpd.read_file(workdir / probe.arguments[1]).geometry.iloc[0]
        remaining = difference.fn(concession.wkt, reserve.wkt)["geometry"]
        return Outcome(answer=float(get_area.fn(remaining)["area"]))

    def op_raster_ground_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        from gis_mcp.rasterio_functions import metadata_raster

        # `metadata_raster` is the whole answer here: it returns the bounds,
        # and the ground area of a rectangular grid is the extent. Nothing in
        # the toolset can say which of two georeferencings produced those
        # bounds, or that there were two.
        extent = metadata_raster.fn(str(workdir / probe.arguments[0]))["metadata"]
        left, bottom, right, top = extent["bounds"]
        return Outcome(answer=float((right - left) * (top - bottom)))

    def op_net_plot_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # Same careful composition as the other area rows. The ring roles were
        # decided by the shapefile reader before any tool saw the geometry, and
        # GEOS reports the result as invalid ("Nested shells"); is_valid then
        # make_valid, both theirs, give 29,000 where the bare read gives 31,000.
        # Until 2026-09-04 this method took the bare read, which measured the
        # naive composition and called it gis-mcp.
        return Outcome(answer=self._careful_area(workdir / probe.arguments[0]))

    # Two of the nine stay unsupported, and the reason is theirs rather than
    # this file's:
    #
    # `lowest_cell_easting` (024) needs the POSITION of a raster's minimum.
    # gis-mcp reports band statistics but nothing that returns a cell index or
    # a coordinate, and composing an argmin out of numpy here would measure
    # numpy -- the same rule that keeps `ndvi_mean` honest.
    #
    # `mean_slope_degrees` (026) needs slope. They ship `hillshade`, which
    # consumes a slope internally and returns shading, and no tool that
    # returns the angle.
