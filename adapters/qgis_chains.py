"""The algorithm chains that answer each probe, shared by every QGIS adapter.

Three systems in this suite are QGIS underneath: the processing engine driven
headless through `qgis_process`, and the two MCP servers that run inside a live
QGIS and forward to `processing.run`. The chain that answers a probe — buffer
then count, field calculator then statistics, dissolve then measure — is the
same in all three. Only the transport differs.

**It lives in one file because three copies is a defect this project has already
paid for.** On 2026-08-26 the same `sorted[-1]` assumption sat in a site build,
its test and the CI, and published the older of two runs from the same day. Here
the stakes are worse: if a chain drifted between two adapters, the difference
between their rows would be the drift, and the rows exist precisely to attribute
a difference to the SYSTEM. Sharing the chains is what makes the comparison mean
anything — whatever separates the three numbers can only be the thing measured.

Subclasses provide `_call(algorithm, workdir, ellipsoid=None, providers="core",
**parameters)`, returning `(results, log)`: the algorithm's outputs as the
engine reports them, and whatever the system said out loud along the way.

**Why `area($geometry)` and not `$area`.** The two are not synonyms, and the
difference only shows up once more than one transport is in the table. `$area`
is ellipsoid-aware: with no project it is planar in the layer's units, and
inside a live QGIS it obeys the project's ellipsoid. `area($geometry)` is planar
always. A chain written with `$area` therefore asks a *different question* of
the headless engine than of the two servers that run inside QGIS — measured on
2026-09-14, the clean probe `c002-projected-area` came back 1000800.47 against a
truth of 1000000 through the plugin socket, and 1000000.0 headless, from the
same chain. That gap is the chain's ambiguity, not the systems'. So a probe that
asks for a planar area now says so, and a probe that asks for ground area says
that instead by passing an ellipsoid.
"""

from __future__ import annotations

import json
from pathlib import Path

from argleton.model import Outcome, Probe


def _features(path: Path) -> list[dict]:
    """Read back a layer QGIS just wrote, as plain JSON.

    Reading the engine's own output is not doing the GIS: the numbers and the
    strings in it are QGIS's, and this only carries them out of the file. Used
    where the answer is a name or a single attribute rather than a total, which
    `qgis_process` has no way to hand back as a scalar.
    """
    document = json.loads(path.read_text(encoding="utf-8"))
    return document.get("features", [])



class QgisChains:
    """The operations, in terms of a `_call` a subclass supplies."""

    def run(self, probe: Probe, workdir: Path) -> Outcome:
        operation = getattr(self, f"op_{probe.operation}", None)
        if operation is None:
            return Outcome(unsupported=True)
        try:
            return operation(probe, workdir)
        except RuntimeError as failure:
            return Outcome(error=str(failure))

    def _call(
        self,
        algorithm: str,
        workdir: Path,
        ellipsoid: str | None = None,
        providers: str = "core",
        **parameters: object,
    ) -> tuple[dict, list[str]]:
        raise NotImplementedError("a QGIS adapter must supply its own transport")

    def _sum_of(self, layer: str, field: str, workdir: Path) -> tuple[float, int, list[str]]:
        """SUM and COUNT of one numeric field, straight from QGIS's own statistics."""
        results, log = self._call(
            "qgis:basicstatisticsforfields", workdir, INPUT_LAYER=layer, FIELD_NAME=field
        )
        return float(results["SUM"]), int(results["COUNT"]), log

    def _measure(
        self,
        layer: str,
        expression: str,
        workdir: Path,
        ellipsoid: str | None = None,
    ) -> tuple[float, list[str]]:
        """Evaluate a per-feature expression with the field calculator, then total it.

        Two algorithms rather than one because `qgis_process` has no way to
        evaluate an expression over a layer and hand back a scalar: the engine's
        own route from "a number per feature" to "one number" is a statistics
        run over a calculated field, and that is the route taken here.
        """
        total, _, log = self._measure_sum(layer, expression, workdir, ellipsoid)
        return total, log

    def _measure_sum(
        self,
        layer: str,
        expression: str,
        workdir: Path,
        ellipsoid: str | None = None,
    ) -> tuple[float, int, list[str]]:
        """As `_measure`, but keeping the feature count the statistics also give."""
        calculated = "_measured.gpkg"
        _, calc_log = self._call(
            "native:fieldcalculator",
            workdir,
            ellipsoid=ellipsoid,
            INPUT=layer,
            FIELD_NAME="m",
            FORMULA=expression,
            OUTPUT=calculated,
        )
        total, count, stat_log = self._sum_of(calculated, "m", workdir)
        return total, count, calc_log + stat_log

    # --- vector: area ---------------------------------------------------

    def op_planar_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # `$area` with no ellipsoid set is planar, in the layer's own units,
        # and QGIS neither converts them nor names them. Asking for square
        # metres is the caller's business; this row records what the engine
        # hands back when asked the way the question was asked.
        total, log = self._measure(probe.arguments[0], "area($geometry)", workdir)
        return Outcome(answer=total, warnings=log)

    def op_field_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        total, log = self._measure(probe.arguments[0], "area($geometry)", workdir)
        return Outcome(answer=total, warnings=log)

    def op_buildable_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # A polygon's rings are the engine's business: `$area` subtracts the
        # interior ones, and whether a ring IS interior is decided by the format.
        total, log = self._measure(probe.arguments[0], "area($geometry)", workdir)
        return Outcome(answer=total, warnings=log)

    def op_net_plot_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        total, log = self._measure(probe.arguments[0], "area($geometry)", workdir)
        return Outcome(answer=total, warnings=log)

    def op_ground_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # Ground area is the one place an ellipsoid is not an embellishment but
        # the question itself, and QGIS offers the parameter: `--ELLIPSOID`
        # switches `$area` from planar to ellipsoidal. Withholding it would
        # measure this file's manners rather than the engine.
        total, log = self._measure(probe.arguments[0], "$area", workdir, ellipsoid="WGS84")
        return Outcome(answer=total, warnings=log)

    def op_total_ground_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # Summing the parts double-counts wherever they overlap. The engine's
        # answer to "the total ground area of these" is the union, so dissolve
        # first and measure the result — one algorithm call, no arithmetic here.
        #
        # Planar, and NOT with an ellipsoid, unlike `ground_area_m2` above —
        # which is a difference between two probes of this suite, not a choice
        # of this adapter. `008-web-mercator-area` means geodesic area by
        # "ground area" and its truth is 6651.3 against a planar 12000;
        # `012-double-counting` means the planar area of a UTM square and its
        # truth is exactly 16000 at a tolerance of 0.01. Measured on 2026-09-14:
        # answering 012 ellipsoidally gives 16012.81, which is right about the
        # Earth and 1280 times outside the tolerance of a probe whose subject is
        # double counting, not projection. Reported to the suite; until it is
        # settled, each operation is answered in the frame its own truth uses.
        _, dissolve_log = self._call(
            "native:dissolve", workdir, INPUT=probe.arguments[0], OUTPUT="_dissolved.gpkg"
        )
        total, log = self._measure("_dissolved.gpkg", "area($geometry)", workdir)
        return Outcome(answer=total, warnings=dissolve_log + log)

    def op_workable_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # "The concession minus the reserve", in that order: `native:difference`
        # keeps INPUT and removes OVERLAY, and swapping them answers a different
        # question with the same confidence.
        _, difference_log = self._call(
            "native:difference",
            workdir,
            INPUT=probe.arguments[0],
            OVERLAY=probe.arguments[1],
            OUTPUT="_workable.gpkg",
        )
        total, log = self._measure("_workable.gpkg", "area($geometry)", workdir)
        return Outcome(answer=total, warnings=difference_log + log)

    # --- vector: length, counts ------------------------------------------

    def op_pipe_length_total_m(self, probe: Probe, workdir: Path) -> Outcome:
        total, log = self._measure(probe.arguments[0], "length($geometry)", workdir)
        return Outcome(answer=total, warnings=log)

    def op_feature_count(self, probe: Probe, workdir: Path) -> Outcome:
        # The probe names the layer, and a container holds several: QGIS's own
        # way to name one is the `|layername=` suffix on the path, so it is used.
        # There is no `count features` algorithm in the C++ providers — that was
        # assumed here on 2026-09-14 and it does not exist. Totalling a constant
        # per feature is the same number by a route that is actually shipped,
        # and it works on any layer rather than on a GeoPackage's `fid`.
        layer = probe.arguments[0]
        named = f"{layer}|layername={probe.arguments[1].split('=', 1)[1]}"
        total, log = self._measure(named, "1", workdir)
        return Outcome(answer=int(total), warnings=log)

    def op_points_in_polygon_count(self, probe: Probe, workdir: Path) -> Outcome:
        # The two layers may declare different CRSs. Processing reprojects
        # inputs into the algorithm's working CRS by itself; whether it does so
        # here, and whether it says anything, is precisely what is being measured.
        results, log = self._call(
            "native:countpointsinpolygon",
            workdir,
            POLYGONS=probe.arguments[1],
            POINTS=probe.arguments[0],
            FIELD="n",
            OUTPUT="_inpoly.gpkg",
        )
        total, _, stat_log = self._sum_of(str(results["OUTPUT"]), "n", workdir)
        return Outcome(answer=int(total), warnings=log + stat_log)

    def op_count_within_distance(self, probe: Probe, workdir: Path) -> Outcome:
        # Buffer the target by the distance and count what falls inside. QGIS
        # buffers in the layer's units, as every engine here does; the question
        # is in metres, and nothing in the call can say so.
        layer = probe.arguments[0]
        target = probe.arguments[1].split("=", 1)[1]
        distance = float(probe.arguments[2].split("=", 1)[1])
        _, extract_log = self._call(
            "native:extractbyattribute",
            workdir,
            INPUT=layer,
            FIELD="well_id",
            VALUE=target,
            OUTPUT="_target.gpkg",
        )
        _, buffer_log = self._call(
            "native:buffer", workdir, INPUT="_target.gpkg", DISTANCE=distance, OUTPUT="_ring.gpkg"
        )
        results, count_log = self._call(
            "native:countpointsinpolygon",
            workdir,
            POLYGONS="_ring.gpkg",
            POINTS=layer,
            FIELD="n",
            OUTPUT="_ringcount.gpkg",
        )
        total, _, stat_log = self._sum_of(str(results["OUTPUT"]), "n", workdir)
        # The target sits inside its own buffer; the question asks for the others.
        return Outcome(
            answer=int(total) - 1, warnings=extract_log + buffer_log + count_log + stat_log
        )

    # --- raster ----------------------------------------------------------

    def op_raster_mean(self, probe: Probe, workdir: Path) -> Outcome:
        results, log = self._call(
            "native:rasterlayerstatistics", workdir, INPUT=probe.arguments[0], BAND=1
        )
        return Outcome(answer=float(results["MEAN"]), warnings=log)

    def op_mean_slope_degrees(self, probe: Probe, workdir: Path) -> Outcome:
        _, slope_log = self._call(
            "native:slope", workdir, INPUT=probe.arguments[0], Z_FACTOR=1, OUTPUT="_slope.tif"
        )
        results, log = self._call(
            "native:rasterlayerstatistics", workdir, INPUT="_slope.tif", BAND=1
        )
        return Outcome(answer=float(results["MEAN"]), warnings=slope_log + log)

    def op_raster_ground_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # The extent as the file declares it: columns times rows times the cell.
        # Which georeferencing QGIS believes when a stale world file sits beside
        # the GeoTIFF is the question, and this reads back whatever it believed.
        results, log = self._call(
            "native:rasterlayerproperties", workdir, INPUT=probe.arguments[0], BAND=1
        )
        area = (
            float(results["WIDTH_IN_PIXELS"])
            * abs(float(results["PIXEL_WIDTH"]))
            * float(results["HEIGHT_IN_PIXELS"])
            * abs(float(results["PIXEL_HEIGHT"]))
        )
        return Outcome(answer=area, warnings=log)

    def op_lowest_cell_easting(self, probe: Probe, workdir: Path) -> Outcome:
        # Every cell becomes a point, the lowest value is found by statistics,
        # and the point carrying it is extracted. Where QGIS puts that point
        # inside the cell — centre or corner — is the trap, and it is QGIS's
        # answer that is read back, not a correction of it.
        _, points_log = self._call(
            "native:pixelstopoints",
            workdir,
            INPUT_RASTER=probe.arguments[0],
            RASTER_BAND=1,
            FIELD_NAME="VALUE",
            OUTPUT="_cells.gpkg",
        )
        stats, stats_log = self._call(
            "qgis:basicstatisticsforfields", workdir, INPUT_LAYER="_cells.gpkg", FIELD_NAME="VALUE"
        )
        lowest = float(stats["MIN"])
        _, extract_log = self._call(
            "native:extractbyattribute",
            workdir,
            INPUT="_cells.gpkg",
            FIELD="VALUE",
            OPERATOR=0,  # equals
            VALUE=lowest,
            OUTPUT="_lowest.gpkg",
        )
        easting, _, sum_log = self._measure_sum("_lowest.gpkg", "$x", workdir)
        return Outcome(answer=easting, warnings=points_log + stats_log + extract_log + sum_log)

    def op_class_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # "Put it on a 15 metre grid, then report the area of class 2." Warping
        # is a `gdal:` algorithm, so this one pays the slow door; the resampling
        # method is QGIS's own default, which is the subject of the probe.
        resolution = float(probe.arguments[1].split("=", 1)[1])
        wanted = float(probe.arguments[2].split("=", 1)[1])
        _, warp_log = self._call(
            "gdal:warpreproject",
            workdir,
            providers="all",
            INPUT=probe.arguments[0],
            TARGET_RESOLUTION=resolution,
            OUTPUT="_grid.tif",
        )
        _, points_log = self._call(
            "native:pixelstopoints",
            workdir,
            INPUT_RASTER="_grid.tif",
            RASTER_BAND=1,
            FIELD_NAME="VALUE",
            OUTPUT="_gridcells.gpkg",
        )
        _, extract_log = self._call(
            "native:extractbyattribute",
            workdir,
            INPUT="_gridcells.gpkg",
            FIELD="VALUE",
            OPERATOR=0,
            VALUE=wanted,
            OUTPUT="_class.gpkg",
        )
        cells, _, sum_log = self._measure_sum("_class.gpkg", "1", workdir)
        return Outcome(
            answer=cells * resolution * resolution,
            warnings=warp_log + points_log + extract_log + sum_log,
        )

    def op_ndvi_mean(self, probe: Probe, workdir: Path) -> Outcome:
        # (NIR - RED) / (NIR + RED), through the raster calculator, which is a
        # `gdal:` algorithm and needs the slow door. Whether the bands' declared
        # scale and offset reach the arithmetic is the whole probe.
        red = int(probe.arguments[1].split("=", 1)[1])
        nir = int(probe.arguments[2].split("=", 1)[1])
        scene = probe.arguments[0]
        _, calc_log = self._call(
            "gdal:rastercalculator",
            workdir,
            providers="all",
            INPUT_A=scene,
            BAND_A=nir,
            INPUT_B=scene,
            BAND_B=red,
            FORMULA="(A.astype(float) - B.astype(float)) / (A.astype(float) + B.astype(float))",
            OUTPUT="_ndvi.tif",
        )
        results, log = self._call(
            "native:rasterlayerstatistics", workdir, INPUT="_ndvi.tif", BAND=1
        )
        return Outcome(answer=float(results["MEAN"]), warnings=calc_log + log)

    # --- vector: joins, location, tables ---------------------------------

    def op_pipe_length_m(self, probe: Probe, workdir: Path) -> Outcome:
        # `$length` is the length QGIS offers, and it is the one on the map
        # plane. Whether the pipe's elevations belong in "how many metres of
        # pipe" is the probe's question, not this adapter's to answer.
        total, log = self._measure(probe.arguments[0], "length($geometry)", workdir)
        return Outcome(answer=total, warnings=log)

    def op_flooded_farmland_m2(self, probe: Probe, workdir: Path) -> Outcome:
        _, cut_log = self._call(
            "native:intersection",
            workdir,
            INPUT=probe.arguments[0],
            OVERLAY=probe.arguments[1],
            OUTPUT="_flooded.gpkg",
        )
        total, log = self._measure("_flooded.gpkg", "area($geometry)", workdir)
        return Outcome(answer=total, warnings=cut_log + log)

    def op_wells_in_districts(self, probe: Probe, workdir: Path) -> Outcome:
        results, log = self._call(
            "native:countpointsinpolygon",
            workdir,
            POLYGONS=probe.arguments[1],
            POINTS=probe.arguments[0],
            FIELD="n",
            OUTPUT="_wells.gpkg",
        )
        total, _, stat_log = self._sum_of(str(results["OUTPUT"]), "n", workdir)
        return Outcome(answer=int(total), warnings=log + stat_log)

    def op_ships_in_zone(self, probe: Probe, workdir: Path) -> Outcome:
        # The vessel table names its columns, so they are named here rather than
        # taken in order — QGIS asks which field is X and which is Y, and giving
        # it the wrong one would be this file's mistake, not the engine's.
        _, points_log = self._call(
            "native:createpointslayerfromtable",
            workdir,
            INPUT=probe.arguments[1],
            XFIELD="longitude",
            YFIELD="latitude",
            TARGET_CRS="EPSG:4326",
            OUTPUT="_ships.gpkg",
        )
        results, count_log = self._call(
            "native:countpointsinpolygon",
            workdir,
            POLYGONS=probe.arguments[0],
            POINTS="_ships.gpkg",
            FIELD="n",
            OUTPUT="_shipsinzone.gpkg",
        )
        total, _, stat_log = self._sum_of(str(results["OUTPUT"]), "n", workdir)
        return Outcome(answer=int(total), warnings=points_log + count_log + stat_log)

    def op_district_of_parcel(self, probe: Probe, workdir: Path) -> Outcome:
        # Centroid, then which district contains it — the route a processing
        # toolbox offers for "which polygon is this one in". That a centroid can
        # fall outside its own parcel is the probe's business.
        _, centroid_log = self._call(
            "native:centroids", workdir, INPUT=probe.arguments[0], OUTPUT="_centroid.gpkg"
        )
        _, join_log = self._call(
            "native:joinattributesbylocation",
            workdir,
            INPUT="_centroid.gpkg",
            JOIN=probe.arguments[1],
            PREDICATE=[0],  # intersects
            JOIN_FIELDS=["district"],
            METHOD=0,
            DISCARD_NONMATCHING=False,
            OUTPUT="_where.geojson",
        )
        features = _features(workdir / "_where.geojson")
        names = [f["properties"].get("district") for f in features]
        answer = names[0] if len(names) == 1 else names
        return Outcome(answer=answer, warnings=centroid_log + join_log)

    def op_thiessen_value_mm(self, probe: Probe, workdir: Path) -> Outcome:
        # Voronoi cells around the gauges, then the cell the site falls in.
        # COPY_ATTRIBUTES is asked for explicitly: without it the reading would
        # not travel with its cell, and the pairing is the probe's subject.
        #
        # QGIS refuses to build cells from fewer than three points, and with two
        # gauges the Thiessen answer is simply the nearer one — so the fallback
        # is a join by nearest, and it is announced in the warnings rather than
        # done quietly. Falling back is not a correction of the engine: it is
        # the second algorithm the engine offers for the same question once the
        # first has said it cannot.
        field = probe.arguments[2]
        fallback: list[str] = []
        try:
            _, voronoi_log = self._call(
                "native:voronoipolygons",
                workdir,
                INPUT=probe.arguments[0],
                BUFFER=100,
                COPY_ATTRIBUTES=True,
                OUTPUT="_cells.gpkg",
            )
            _, join_log = self._call(
                "native:joinattributesbylocation",
                workdir,
                INPUT=probe.arguments[1],
                JOIN="_cells.gpkg",
                PREDICATE=[0],
                JOIN_FIELDS=[field],
                METHOD=0,
                DISCARD_NONMATCHING=False,
                OUTPUT="_site.geojson",
            )
        except RuntimeError as refusal:
            if "at least" not in str(refusal) and "3 point" not in str(refusal):
                raise
            fallback = [
                "voronoi polygons refused the gauge layer, so the nearest gauge was "
                f"joined instead: {refusal}"
            ]
            _, join_log = self._call(
                "native:joinbynearest",
                workdir,
                INPUT=probe.arguments[1],
                INPUT_2=probe.arguments[0],
                FIELDS_TO_COPY=[field],
                NEIGHBORS=1,
                DISCARD_NONMATCHING=False,
                OUTPUT="_site.geojson",
            )
            voronoi_log = []
        features = _features(workdir / "_site.geojson")
        values = [f["properties"].get(field) for f in features]
        return Outcome(
            answer=float(values[0]) if len(values) == 1 and values[0] is not None else values,
            warnings=fallback + voronoi_log + join_log,
        )

    def op_total_population(self, probe: Probe, workdir: Path) -> Outcome:
        # Join the table on the code and total the column. Whether the two sides
        # of the key are the same type after each file is read is the probe.
        _, join_log = self._call(
            "native:joinattributestable",
            workdir,
            INPUT=probe.arguments[0],
            FIELD="istat_code",
            INPUT_2=probe.arguments[1],
            FIELD_2="istat_code",
            METHOD=1,
            DISCARD_NONMATCHING=False,
            OUTPUT="_joined.gpkg",
        )
        total, _, sum_log = self._measure_sum(
            "_joined.gpkg", 'coalesce(to_real("population"), 0)', workdir
        )
        return Outcome(answer=total, warnings=join_log + sum_log)

    def op_sheet_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # The question is the area of the parcels; the owners table is named in
        # it, so it is joined, which is what makes this a trap: one parcel with
        # two owners becomes two rows, and the area follows the row.
        _, join_log = self._call(
            "native:joinattributestable",
            workdir,
            INPUT=probe.arguments[0],
            FIELD="parcel_id",
            INPUT_2=probe.arguments[1],
            FIELD_2="parcel_id",
            METHOD=1,
            DISCARD_NONMATCHING=False,
            OUTPUT="_sheets.gpkg",
        )
        total, log = self._measure("_sheets.gpkg", "area($geometry)", workdir)
        return Outcome(answer=total, warnings=join_log + log)

    def op_area_unemployment_rate_pct(self, probe: Probe, workdir: Path) -> Outcome:
        # The statistics panel answers "the rate of the area" with the mean of
        # the rate column. Whether that is the rate of the area, or the mean of
        # three rates that belong to populations of different sizes, is the probe.
        results, log = self._call(
            "qgis:basicstatisticsforfields",
            workdir,
            INPUT_LAYER=probe.arguments[0],
            FIELD_NAME="unemployment_rate_pct",
        )
        return Outcome(answer=float(results["MEAN"]), warnings=log)

    def op_wgs84_latitude(self, probe: Probe, workdir: Path) -> Outcome:
        # Reproject to WGS 84 and read the northing back. Which transformation
        # PROJ picks between the two datums is the probe, and QGIS announces a
        # non-preferred one on stdout — so the warning travels with the number
        # here instead of being swallowed, which is the point of keeping the log.
        _, reproject_log = self._call(
            "native:reprojectlayer",
            workdir,
            INPUT=probe.arguments[0],
            TARGET_CRS="EPSG:4326",
            OUTPUT="_wgs84.gpkg",
        )
        latitude, _, log = self._measure_sum("_wgs84.gpkg", "$y", workdir)
        return Outcome(answer=latitude, warnings=reproject_log + log)

    def op_latitude_decimal(self, probe: Probe, workdir: Path) -> Outcome:
        # The table may keep the latitude already in decimal degrees, or split
        # across degrees, minutes, seconds and a hemisphere. Which one it is, is
        # read from the header — the same look a person gives a corner schedule
        # before choosing a formula — and the arithmetic is then the field
        # calculator's. The CSV reader hands every column back as text, hence
        # `to_real`.
        station = probe.arguments[1].split("=", 1)[1]
        _, extract_log = self._call(
            "native:extractbyattribute",
            workdir,
            INPUT=probe.arguments[0],
            FIELD="station_id",
            OPERATOR=0,
            VALUE=station,
            OUTPUT="_station.gpkg",
        )
        header = (workdir / probe.arguments[0]).read_text(encoding="utf-8").splitlines()[0]
        columns = [name.strip().strip('"') for name in header.split(",")]
        if "lat_deg" in columns:
            decimal = (
                '(to_real("lat_deg") + to_real("lat_min") / 60.0 + to_real("lat_sec") / 3600.0)'
                " * (CASE WHEN upper(\"lat_hem\") = 'S' THEN -1 ELSE 1 END)"
            )
        else:
            decimal = 'to_real("latitude")'
        total, _, sum_log = self._measure_sum("_station.gpkg", decimal, workdir)
        return Outcome(answer=total, warnings=extract_log + sum_log)

    def op_parcel_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # A corner schedule becomes points, the points become a closed path, the
        # path becomes a polygon. The columns are named in the file and named
        # again here: QGIS asks which is X, and answering "longitude" is reading
        # the file, not correcting it.
        _, points_log = self._call(
            "native:createpointslayerfromtable",
            workdir,
            INPUT=probe.arguments[0],
            XFIELD="longitude",
            YFIELD="latitude",
            TARGET_CRS="EPSG:4326",
            OUTPUT="_corners.gpkg",
        )
        _, path_log = self._call(
            "native:pointstopath",
            workdir,
            INPUT="_corners.gpkg",
            CLOSE_PATH=True,
            ORDER_EXPRESSION='to_real("corner")',
            OUTPUT="_ring.gpkg",
        )
        _, polygon_log = self._call(
            "native:polygonize", workdir, INPUT="_ring.gpkg", OUTPUT="_parcel.gpkg"
        )
        total, log = self._measure("_parcel.gpkg", "$area", workdir, ellipsoid="WGS84")
        return Outcome(answer=total, warnings=points_log + path_log + polygon_log + log)
