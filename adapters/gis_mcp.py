"""Adapter: gis-mcp (mahdin75/gis-mcp) — 88 tools wrapping Shapely, PyProj,
GeoPandas, Rasterio and PySAL.

Eighty-eight is what the server registers, asked of it rather than counted by
eye: `await gis_mcp.get_tools()` on 0.15.0. The header said "92+" until
2026-09-04 and the figure had no derivation behind it. Counting the source
gives other numbers, all of them wrong in a different way -- 87 `@tool()`
decorators, because one is registered elsewhere, and 101 module attributes
that carry a `.fn`, because several are re-exported and counted twice and
thirteen `get_*_operations` helpers are documentation rather than tools.

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
        from gis_mcp.rasterio_functions import compute_ndvi, raster_band_statistics

        # Until 2026-09-04 this method said "gis-mcp ships no band-math or index
        # tool" and returned unsupported on every path -- including the path
        # where its own lookup had just FOUND one. gis-mcp 0.15.0 ships
        # compute_ndvi, and the review of the maintainer notice caught the
        # comment being false while the notice asked them to tell us about
        # tools we had missed. Composition, all theirs: compute_ndvi writes
        # the index raster, raster_band_statistics reads its mean. What the
        # trap measures is whether the index is built on the stored integers
        # or on the physical values the scale/offset tags describe.
        red = int(probe.arguments[1].split("=", 1)[1])
        nir = int(probe.arguments[2].split("=", 1)[1])
        index = workdir / "_gis_mcp_ndvi.tif"
        written = compute_ndvi.fn(str(workdir / probe.arguments[0]), red, nir, str(index))
        if written.get("status") != "success":
            return Outcome(error=str(written.get("message", written)))
        stats = raster_band_statistics.fn(str(index))
        bands = stats.get("statistics") or {}
        first = next(iter(bands.values()), None) if isinstance(bands, dict) else None
        if not first or "mean" not in first:
            return Outcome(error=f"raster_band_statistics returned no mean: {stats}")
        return Outcome(answer=float(first["mean"]))

    def op_class_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # Charitable composition (their own tools, at their best): gis-mcp wraps
        # rasterio, so the reader is theirs and the resampling choice is the
        # caller's. Whether a resample tool exists in the set is resolved at
        # call time rather than assumed: if it does not, the honest verdict is
        # unsupported, not a number produced by glue we wrote.
        try:
            from gis_mcp.rasterio_functions import (
                metadata_raster,
                raster_band_statistics,
                reclassify_raster,
                resample_raster,
            )
        except ImportError:
            return Outcome(unsupported=True)

        resolution = float(probe.arguments[1].split("=", 1)[1])
        wanted = int(probe.arguments[2].split("=", 1)[1])
        source = workdir / probe.arguments[0]
        destination = workdir / "_argleton_resampled.tif"
        # Their tool takes a scale factor for width/height, not a target cell
        # size, so the glue converts: the question asks for a 15 m grid and the
        # source is 20 m, hence 20/15. Their `resampling` argument, like ours,
        # has NO default — the caller must state it, and a caller told the
        # legend states a categorical method. Same charity as trap 007.
        before = metadata_raster.fn(str(source))["metadata"]["transform"]
        scale = abs(float(before[0])) / resolution
        try:
            resample_raster.fn(
                source=str(source),
                scale_factor=scale,
                resampling="nearest",
                destination=str(destination),
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            return Outcome(error=f"{type(exc).__name__}: {exc}")

        # The readout is theirs too, and until 2026-09-04 it was not: this was
        # the one method in the file where the glue reduced a raster to the
        # answer itself (`numpy.sum(band == wanted)`). gis-mcp can do it --
        # reclassify to a 0/1 mask, then read that mask's mean -- and it
        # returns the same numbers here, so the change buys consistency rather
        # than a different result. The rule it now follows is D-071: the glue
        # carries data and converts units, and never turns a dataset into the
        # number the question asks for.
        after = metadata_raster.fn(str(destination))["metadata"]
        holes = [value for value in (after.get("no_data") or ()) if value is not None]
        if holes:
            # `raster_band_statistics` averages a MASKED array, so with nodata
            # present its mean is over the valid cells while width x height
            # counts all of them, and the product would read the holes as
            # class members. Nothing in the toolset returns a valid-cell count,
            # so the honest move is to stop rather than to guess one.
            return Outcome(error=f"cannot count classes with nodata present: {holes}")
        seen = raster_band_statistics.fn(str(destination))["statistics"]["Band 1"]
        legend = {value: 0 for value in range(int(seen["min"]), int(seen["max"]) + 1)}
        legend[wanted] = 1
        mask = workdir / "_argleton_class_mask.tif"
        written = reclassify_raster.fn(str(destination), legend, str(mask))
        if written.get("status") != "success":
            return Outcome(error=str(written.get("message", written)))
        counted = raster_band_statistics.fn(str(mask))["statistics"]["Band 1"]
        if counted["min"] < 0.0 or counted["max"] > 1.0:
            # A value the legend did not cover survived -- a fractional class
            # code from a continuous resampling, say -- so the mask's mean is
            # not a proportion of cells and the product below would be a
            # confident wrong number, which is the thing this suite measures.
            return Outcome(error=f"the class mask is not 0/1: {counted}")
        cells = counted["mean"] * int(after["width"]) * int(after["height"])
        if abs(cells - round(cells)) > 1e-6:
            return Outcome(error=f"the class count is not a whole number of cells: {cells}")
        area = abs(float(after["transform"][0])) * abs(float(after["transform"][4]))
        return Outcome(answer=float(round(cells) * area))

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
        from gis_mcp.pyproj_functions import calculate_geodetic_distance, project_geometry
        from shapely import wkt as shapely_wkt

        # The charitable composition, on purpose. gis-mcp also ships a
        # units-blind buffer, and `buffer` then `sjoin_gpd` is the obvious
        # route with this toolset -- measured, it answers 24 on the trap, which
        # is the naive failure the probe describes. Their geodetic-distance
        # tool is the right instrument for a metric question and a careful
        # client would reach for it, so that is what this asks.
        #
        # Until 2026-09-04 the projected branch measured with GEOPANDAS
        # (`others.distance(target)`), on the true and irrelevant grounds that
        # a planar distance is already in metres: the clean twin's number then
        # came from geopandas rather than from the system under test, so the
        # control was not controlling anything. One composition now serves
        # both, reprojecting with their tool where the coordinates are not
        # lon/lat. Measured either way the answers are 3 and 5 -- the
        # correction moves no number, which is exactly why it survived review.
        frame = gpd.read_file(workdir / probe.arguments[0])
        if frame.crs is None:
            return Outcome(refusal="the layer declares no CRS")
        target_id = probe.arguments[1].split("=", 1)[1]
        distance = float(probe.arguments[2].split("=", 1)[1])
        target = frame[frame["well_id"] == target_id].geometry.iloc[0]
        others = frame[frame["well_id"] != target_id]

        def as_lonlat(geometry):
            if frame.crs.is_geographic:
                return geometry
            moved = project_geometry.fn(geometry.wkt, str(frame.crs), "EPSG:4326")
            return shapely_wkt.loads(moved["geometry"])

        here = as_lonlat(target)
        count = 0
        for geometry in others.geometry:
            there = as_lonlat(geometry)
            measured = calculate_geodetic_distance.fn([here.x, here.y], [there.x, there.y])
            count += measured["distance"] <= distance
        return Outcome(answer=int(count))

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

    def op_mean_slope_degrees(self, probe: Probe, workdir: Path) -> Outcome:
        import math

        from gis_mcp.rasterio_functions import (
            focal_statistics,
            metadata_raster,
            raster_algebra,
            raster_band_statistics,
        )

        # No gis-mcp tool returns a slope angle: `hillshade` computes one on
        # the way past and hands back only the shaded image. So this is a
        # composition of four of their tools -- the greatest drop inside each
        # 3x3 window (focal max minus focal min), the mean of those drops, and
        # the cell size off the transform -- and the glue does one division and
        # one arctangent, because nothing in the set turns a ratio into an
        # angle. The notice sent to the maintainer on 2026-09-04 said this was
        # on our list; this is it, and gis-mcp answers correctly.
        #
        # The estimator is a max-drop over the window rather than Horn: exact
        # on a plane tilted along an axis, which this surface is, and an
        # overestimate on a diagonal tilt, which the toolset cannot fix because
        # nothing in it shifts a raster by a cell. Said here rather than left
        # to be discovered, since it is the glue's choice and not theirs.
        source = workdir / probe.arguments[0]
        transform = metadata_raster.fn(str(source))["metadata"]["transform"]
        # What gets this probe right is the first element, and it is right for
        # free: rasterio reports the transform faithfully and `metadata_raster`
        # passes it through, so the run is 10 m on the south-up grid exactly as
        # on the north-up twin. The engines that fail here are the ones that
        # build a grid model of their own, cannot express a positive fifth
        # element, and drop the georeferencing entirely -- reading 1 m cells at
        # the origin.
        #
        # The abs() on the fifth element earns its place on the TWIN, not on the
        # trap: north-up means negative by convention, so without it the
        # square-cell check below would reject the ordinary grid and accept the
        # unusual one. A guard that fires on the control and not on the trap is
        # worse than no guard, and this one is one character away from being it.
        run = abs(float(transform[0]))
        if abs(run - abs(float(transform[4]))) > 1e-9:
            return Outcome(error="non-square cells: a 3x3 max-drop has no single run")
        highest = workdir / "_gis_mcp_focal_max.tif"
        lowest = workdir / "_gis_mcp_focal_min.tif"
        for statistic, destination in (("max", highest), ("min", lowest)):
            written = focal_statistics.fn(str(source), statistic, 3, str(destination))
            if written.get("status") != "success":
                return Outcome(error=str(written.get("message", written)))
        drop = workdir / "_gis_mcp_drop.tif"
        subtracted = raster_algebra.fn(str(highest), str(lowest), 1, "subtract", str(drop))
        if subtracted.get("status") != "success":
            return Outcome(error=str(subtracted.get("message", subtracted)))
        stats = raster_band_statistics.fn(str(drop))
        bands = stats.get("statistics") or {}
        first = next(iter(bands.values()), None) if isinstance(bands, dict) else None
        if not first or "mean" not in first:
            return Outcome(error=f"raster_band_statistics returned no mean: {stats}")
        return Outcome(answer=math.degrees(math.atan(float(first["mean"]) / (2.0 * run))))

    # One of the nine stays unsupported, and an earlier version of this comment
    # gave the wrong reason for it; the honest one is this.
    #
    # `lowest_cell_easting` (024) needs the ground POSITION of a raster's
    # minimum on a grid that declares AREA_OR_POINT=Point. The cell itself is
    # reachable with their tools -- `metadata_raster` returns the transform and
    # bounds, `tile_raster` can hand back one file per cell -- so "nothing
    # returns a coordinate" was false. What no gis-mcp output carries is the
    # AREA_OR_POINT tag, and turning a cell index into a ground coordinate
    # depends on it: that decision would be this file's, not theirs, which is
    # exactly what this probe measures. So it stays unattempted.
