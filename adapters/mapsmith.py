"""Adapter: MapSmith, the system these probes were written next to.

Here on purpose and first, because a suite whose authors do not measure
themselves is not a suite. What it finds about MapSmith goes in `results/`
whatever it says.

Two things worth stating before the numbers.

**MapSmith exposes no `raster_mean`.** It exposes `zonal_statistics`, so that is
what this adapter calls, with a zone covering the raster's own extent — which is
how you ask MapSmith the question. Composing a system's real tools to answer the
probe is the adapter's whole job; inventing an operation it does not have would
measure a system that does not exist.

**The area operations arrived because of this suite.** Until 2026-08-25 the two
area families (`linear-units`, `invalid-geometry`) and then
`projection-distortion` came back `unsupported` three times: MapSmith had no
area operation at all, and composing one out of raw SQL would have measured
DuckDB instead. Three `unsupported` verdicts on the most elementary question in
GIS is a finding about the catalog, and `measure_area` is the answer to it.

**There is no switch to turn MapSmith's verification off**, and adding one to a
product whose argument is that it verifies would be a footgun someone eventually
ships with. So this measures MapSmith as it is released. On the families
implemented so far that turns out not to matter, and the reason is worth reading
in `results/`.
"""

from __future__ import annotations

from pathlib import Path

from argleton.model import Outcome, Probe


class Adapter:
    name = "mapsmith"

    def run(self, probe: Probe, workdir: Path) -> Outcome:
        operation = getattr(self, f"op_{probe.operation}", None)
        if operation is None:
            return Outcome(unsupported=True)
        return operation(probe, workdir)

    # ---- tier A ---------------------------------------------------------------


    def op_lowest_cell_easting(self, probe: Probe, workdir: Path) -> Outcome:
        # MapSmith has no operation that reports WHERE a cell is. It reads
        # rasters, summarises them, samples them and derives vectors from them,
        # and every one of those turns a cell index into a coordinate the same
        # way rasterio does — so the capability is missing and the convention
        # question has never been asked in this codebase.
        #
        # Reported as unsupported rather than answered with something adjacent.
        # The gap is the finding; an approximation would hide it, and the run
        # notes are where it belongs.
        return Outcome(unsupported=True)

    def op_buildable_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # measure_area on a polygon with a hole: the courtyard is part of the
        # geometry's definition, so nothing here has to know it exists.
        return self._area(probe, workdir, method="planar")

    def op_total_ground_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        from mapsmith.engines import vector

        # Two steps, both catalogue operations: dissolve with no key merges the
        # overlapping licences into one piece of ground, then measure it. The
        # shared strip stops being two things before anything is added up.
        merged = workdir / "_argleton_dissolved.parquet"
        try:
            vector.dissolve(str(workdir / probe.arguments[0]), str(merged))
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            return self._refusal_or_error(exc)
        return self._measure(merged, workdir, "planar")

    def op_flooded_farmland_m2(self, probe: Probe, workdir: Path) -> Outcome:
        from mapsmith.engines import vector

        # overlay(intersection) cuts the fields to the band, so what gets
        # measured is the flooded part rather than the parcels that touch it.
        clipped = workdir / "_argleton_flooded.parquet"
        try:
            vector.overlay(
                str(workdir / probe.arguments[0]),
                str(workdir / probe.arguments[1]),
                str(clipped),
                how="intersection",
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            return self._refusal_or_error(exc)
        return self._measure(clipped, workdir, "planar")

    def op_district_of_parcel(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from mapsmith.engines import vector

        # spatial_join with `within`: the parcel is joined as a polygon, not
        # reduced to a point first, so a concave parcel keeps its shape.
        joined = workdir / "_argleton_district.parquet"
        try:
            vector.spatial_join(
                str(workdir / probe.arguments[0]),
                str(workdir / probe.arguments[1]),
                str(joined),
                predicate="within",
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            return self._refusal_or_error(exc)
        frame = gpd.read_parquet(joined)
        if frame.empty:
            return Outcome(answer="")
        return Outcome(answer=str(frame["district"].iloc[0]), warnings=self._warnings(joined))

    def op_wells_in_districts(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from mapsmith.engines import vector

        # `intersects` rather than `within`, because the question is about a
        # partition and a well on the shared edge is in the study area whichever
        # district claims it. A seam well then matches both districts, so the
        # count is over distinct wells — reading the join, not rewriting it.
        joined = workdir / "_argleton_wells.parquet"
        try:
            vector.spatial_join(
                str(workdir / probe.arguments[0]),
                str(workdir / probe.arguments[1]),
                str(joined),
                predicate="intersects",
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            return self._refusal_or_error(exc)
        frame = gpd.read_parquet(joined)
        return Outcome(
            answer=int(frame["well_id"].nunique()), warnings=self._warnings(joined)
        )

    def op_pipe_length_m(self, probe: Probe, workdir: Path) -> Outcome:
        from mapsmith.engines import vector

        # measure_length(method="3d"), which exists because this probe returned
        # unsupported the first time it ran. The method is stated rather than
        # defaulted: a pipe follows the ground, so the question is about the
        # length through space and the composition has to say so.
        output = workdir / "_argleton_length.parquet"
        try:
            result = vector.measure_length(
                str(workdir / probe.arguments[0]), str(output), method="3d"
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            return self._refusal_or_error(exc)
        return Outcome(
            answer=float(result["total_length_m"]), warnings=self._warnings(output)
        )

    def op_latitude_decimal(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        import pandas as pd
        from mapsmith.engines import vector

        # parse_coordinates: the caller names the columns, because the file
        # cannot say whether 41.5324 is a decimal degree or a mangled DMS.
        station = probe.arguments[1].split("=", 1)[1]
        table = workdir / probe.arguments[0]
        columns = set(pd.read_csv(table, nrows=1).columns)
        if {"lat_deg", "lat_min", "lat_sec"} <= columns:
            latitude = "lat_deg,lat_min,lat_sec,lat_hem"
            longitude = "lon_deg,lon_min,lon_sec,lon_hem"
        else:
            latitude, longitude = "latitude", "longitude"
        output = workdir / "_argleton_points.parquet"
        try:
            vector.parse_coordinates(
                str(table),
                str(output),
                latitude_columns=latitude,
                longitude_columns=longitude,
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            return self._refusal_or_error(exc)
        points = gpd.read_parquet(output)
        row = points[points["station_id"] == station].iloc[0]
        return Outcome(answer=float(row.geometry.y), warnings=self._warnings(output))

    def op_area_unemployment_rate_pct(self, probe: Probe, workdir: Path) -> Outcome:
        from mapsmith.engines import vector

        # aggregate_weighted: a rate over an area is the ratio of totals, and
        # the weight column has to be named — which is the whole operation.
        output = workdir / "_argleton_rate.parquet"
        try:
            result = vector.aggregate_weighted(
                str(workdir / probe.arguments[0]),
                str(output),
                value_column="unemployment_rate_pct",
                weight_column="labour_force",
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            return self._refusal_or_error(exc)
        return Outcome(
            answer=float(result["weighted_value"]), warnings=self._warnings(output)
        )

    def op_total_population(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from mapsmith.engines import vector

        # join_table reads keys as text on both sides, so a code like "001"
        # still matches after the CSV has been through a reader.
        output = workdir / "_argleton_joined.parquet"
        try:
            vector.join_table(
                str(workdir / probe.arguments[0]),
                str(workdir / probe.arguments[1]),
                str(output),
                on="istat_code",
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            return self._refusal_or_error(exc)
        joined = gpd.read_parquet(output)
        return Outcome(
            answer=int(joined["population"].sum()), warnings=self._warnings(output)
        )

    def op_sheet_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from mapsmith.engines import vector

        # The join is where this goes wrong, so the join is where MapSmith
        # says something: join_table reports that the table multiplied the
        # features, and the composition answers over the parcels rather than
        # over the joined rows.
        output = workdir / "_argleton_owners.parquet"
        try:
            result = vector.join_table(
                str(workdir / probe.arguments[0]),
                str(workdir / probe.arguments[1]),
                str(output),
                on="parcel_id",
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            return self._refusal_or_error(exc)
        joined = gpd.read_parquet(output)
        # One row per parcel, whatever the deed says: the duplicate keys are
        # named in the result, so this is reading MapSmith's answer rather than
        # working around it.
        area = float(joined.drop_duplicates(subset="parcel_id")["area_m2"].sum())
        warnings = self._warnings(output)
        if result.get("duplicate_keys"):
            warnings.append(
                f"the owners table has {result['duplicate_keys']} duplicate key(s): "
                f"the join produced {result['feature_count']} rows from "
                f"{result['input_feature_count']} parcels"
            )
        return Outcome(answer=area, warnings=warnings)

    def _measure(self, dataset: Path, workdir: Path, method: str) -> Outcome:
        from mapsmith.engines import vector

        output = workdir / f"_argleton_measured_{method}.parquet"
        try:
            result = vector.measure_area(str(dataset), str(output), method=method)
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            return self._refusal_or_error(exc)
        return Outcome(
            answer=float(result["total_area_m2"]), warnings=self._warnings(output)
        )

    @staticmethod
    def _refusal_or_error(exc: Exception) -> Outcome:
        text = str(exc)
        if "has no CRS" in text or "Refusing" in text or "square degrees" in text:
            return Outcome(refusal=text)
        return Outcome(error=f"{type(exc).__name__}: {text}")

    def op_ndvi_mean(self, probe: Probe, workdir: Path) -> Outcome:
        import numpy as np
        import rasterio
        from mapsmith.engines import raster

        red_band = int(probe.arguments[1].split("=", 1)[1])
        nir_band = int(probe.arguments[2].split("=", 1)[1])
        source = workdir / probe.arguments[0]
        output = workdir / "_argleton_ndvi.tif"
        try:
            result = raster.band_math(
                str(source),
                str(output),
                expression="(b2 - b1) / (b2 + b1)"
                if (red_band, nir_band) == (1, 2)
                else f"(b{nir_band} - b{red_band}) / (b{nir_band} + b{red_band})",
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            text = str(exc)
            if "declares no CRS" in text or "Refusing" in text:
                return Outcome(refusal=text)
            return Outcome(error=f"{type(exc).__name__}: {text}")

        with rasterio.open(output) as ds:
            band = ds.read(1, masked=True)
        warns = [w["detail"] for w in result.get("warnings", [])]
        return Outcome(answer=float(np.ma.mean(band)), warnings=warns)

    def op_class_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import numpy as np
        import rasterio
        from mapsmith.engines import raster

        resolution = float(probe.arguments[1].split("=", 1)[1])
        wanted = int(probe.arguments[2].split("=", 1)[1])
        source = workdir / probe.arguments[0]
        resampled = workdir / "_argleton_resampled.tif"
        try:
            # resample_raster has NO default method: the composition has to
            # state one, and the question states a legend, so these are class
            # codes. That forced choice is the whole defence — and if this
            # composition had said "bilinear", the result would have come back
            # with `invented_values` naming the class that appeared out of
            # nothing, which is the second defence.
            result = raster.resample(
                str(source), str(resampled), resolution, "nearest"
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            text = str(exc)
            if "declares no CRS" in text or "Refusing" in text:
                return Outcome(refusal=text)
            return Outcome(error=f"{type(exc).__name__}: {text}")

        with rasterio.open(resampled) as ds:
            band = ds.read(1)
            cell = abs(float(ds.res[0])) * abs(float(ds.res[1]))
        area = float(int(np.sum(band == wanted)) * cell)
        warns = [w["detail"] for w in result.get("warnings", [])]
        return Outcome(answer=area, warnings=warns)

    def op_raster_mean(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        import rasterio
        from mapsmith.engines import raster
        from shapely.geometry import box

        source = workdir / probe.arguments[0]
        with rasterio.open(source) as ds:
            bounds, crs = ds.bounds, ds.crs
        if crs is None:
            return Outcome(refusal="the raster declares no CRS, so a zone cannot be placed on it")

        # A zone that is exactly the raster's extent. exactextract weights
        # partial pixels rather than counting or dropping them, so a zone on the
        # grid boundary is the whole grid and nothing is double-counted.
        zone = workdir / "_argleton_extent.gpkg"
        gpd.GeoDataFrame(
            {"zone": [1]}, geometry=[box(*bounds)], crs=crs
        ).to_file(zone, layer="zone", driver="GPKG")

        output = workdir / "_argleton_zonal.parquet"
        try:
            raster.zonal_statistics(str(source), str(zone), str(output), stats=["mean"])
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            text = str(exc)
            # MapSmith refuses rather than guesses in several places, and a
            # refusal that names its reason is a different result from a crash.
            if "has no CRS" in text or "Refusing" in text:
                return Outcome(refusal=text)
            return Outcome(error=f"{type(exc).__name__}: {text}")

        result = gpd.read_parquet(output)
        warns = self._warnings(output)
        return Outcome(answer=float(result["mean"].iloc[0]), warnings=warns)

    def op_planar_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # The question asks for the area in the layer's own plane, in square
        # metres: measure_area(method="planar") reads the linear unit off the
        # CRS and converts, and repairs an invalid ring before measuring it.
        return self._area(probe, workdir, method="planar")

    def op_ground_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # This question is about the land, not the map, so the default:
        # geodesic on the ellipsoid the layer's CRS names.
        return self._area(probe, workdir, method="geodesic")

    def _area(self, probe: Probe, workdir: Path, method: str) -> Outcome:
        from mapsmith.engines import vector

        output = workdir / f"_argleton_area_{method}.parquet"
        try:
            result = vector.measure_area(
                str(workdir / probe.arguments[0]), str(output), method=method
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            text = str(exc)
            if "has no CRS" in text or "Refusing" in text or "square degrees" in text:
                return Outcome(refusal=text)
            return Outcome(error=f"{type(exc).__name__}: {text}")
        return Outcome(answer=float(result["total_area_m2"]), warnings=self._warnings(output))

    def op_feature_count(self, probe: Probe, workdir: Path) -> Outcome:
        from mapsmith.engines import dispatch

        # The composition that measured the 2026-08-25 silent error is one
        # line shorter than this: describe_dataset used to answer about the
        # container's default layer with no trace (MapSmith issue #29, caught
        # by this trap). Since the fix, describe returns a per-layer summary
        # for containers, and the composition picks the layer the question
        # names — which is now possible, which was the point.
        result = dispatch.describe_routed(str(workdir / probe.arguments[0]))
        if result.get("kind") == "vector-container":
            layer = probe.arguments[1].split("=", 1)[1]
            entry = next(e for e in result["layers"] if e["layer"] == layer)
            return Outcome(answer=int(entry["feature_count"]))
        return Outcome(answer=int(result["feature_count"]))

    def op_points_in_polygon_count(self, probe: Probe, workdir: Path) -> Outcome:
        from mapsmith.engines import vector

        output = workdir / "_argleton_join.parquet"
        try:
            # MapSmith exposes no point-in-polygon count; it exposes
            # `spatial_join`, so the composition is a within-join of the points
            # against the zone, counting the joined rows. There is exactly one
            # zone, so no point can be counted twice.
            result = vector.spatial_join(
                str(workdir / probe.arguments[0]),
                str(workdir / probe.arguments[1]),
                str(output),
                predicate="within",
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            text = str(exc)
            if "has no CRS" in text or "Refusing" in text:
                return Outcome(refusal=text)
            return Outcome(error=f"{type(exc).__name__}: {text}")
        return Outcome(answer=int(result["feature_count"]), warnings=self._warnings(output))

    def op_count_within_distance(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from mapsmith.engines import vector

        source = workdir / probe.arguments[0]
        target_id = probe.arguments[1].split("=", 1)[1]
        distance = float(probe.arguments[2].split("=", 1)[1])

        # The composition a MapSmith client writes: select the target (glue),
        # buffer_layer — whose contract is METERS, with the UTM decision
        # recorded when the layer is geographic — then a within-join and a
        # count. The target sits inside its own buffer, hence the minus one.
        frame = gpd.read_file(source)
        target_path = workdir / "_argleton_target.gpkg"
        frame[frame["well_id"] == target_id].to_file(
            target_path, layer="target", driver="GPKG"
        )
        buffered = workdir / "_argleton_buffer.parquet"
        joined = workdir / "_argleton_within.parquet"
        try:
            vector.buffer(str(target_path), distance, str(buffered))
            result = vector.spatial_join(
                str(source), str(buffered), str(joined), predicate="within"
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            text = str(exc)
            if "has no CRS" in text or "Refusing" in text or "no layer was chosen" in text:
                return Outcome(refusal=text)
            return Outcome(error=f"{type(exc).__name__}: {text}")
        return Outcome(
            answer=int(result["feature_count"]) - 1, warnings=self._warnings(joined)
        )

    @staticmethod
    def _warnings(output: Path) -> list[str]:
        """Anything the manifest recorded that a reader should have seen.

        A check that failed non-critically, or a repair, is MapSmith telling the
        caller something. If it is there, the probe should be scored as
        `correct_with_warning` rather than plain `correct` — the suite is about
        what a system communicates, not only about the number.
        """
        import json

        manifest = Path(str(output) + ".provenance.json")
        if not manifest.exists():
            return ["no provenance manifest was written"]
        data = json.loads(manifest.read_text(encoding="utf-8"))
        note = [c["detail"] for c in data.get("verification", []) if not c.get("passed")]
        note += [r.get("detail", str(r)) for r in data.get("repairs", [])]
        return note

    def op_wgs84_latitude(self, probe: Probe, workdir: Path) -> Outcome:
        from mapsmith.engines import vector

        # MapSmith exposes `reproject_layer`, so that is what this asks, and the
        # answer is read from the dataset MapSmith wrote -- composing its own
        # operation, not reaching past it into pyproj.
        output = workdir / "_argleton_wgs84.parquet"
        try:
            vector.reproject(
                str(workdir / probe.arguments[0]), "EPSG:4326", str(output)
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            text = str(exc)
            if "has no CRS" in text or "Refusing" in text:
                return Outcome(refusal=text)
            return Outcome(error=f"{type(exc).__name__}: {text}")
        import geopandas as gpd

        frame = gpd.read_parquet(output)
        return Outcome(
            answer=float(frame.geometry.iloc[0].y), warnings=self._warnings(output)
        )

    def op_thiessen_value_mm(self, probe: Probe, workdir: Path) -> Outcome:
        from mapsmith.engines import vector

        # MapSmith exposes `voronoi_polygons`, so this composes MapSmith's own
        # operations rather than reaching past them: build the cells, then use
        # `spatial_join` to find the one the site falls in. The point of doing it
        # the long way is that this is the composition the trap punishes -- if
        # MapSmith's cells carried the wrong rows, this would answer 554 like
        # anyone else, and the check inside the operation is what stops it.
        cells = workdir / "_argleton_cells.parquet"
        joined = workdir / "_argleton_joined.parquet"
        field = probe.arguments[2]
        try:
            vector.voronoi_polygons(
                str(workdir / probe.arguments[0]), str(cells), margin_fraction=0.25
            )
            vector.spatial_join(
                str(workdir / probe.arguments[1]), str(cells), str(joined)
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            text = str(exc)
            if "has no CRS" in text or "Refusing" in text or "needs a point layer" in text:
                return Outcome(refusal=text)
            return Outcome(error=f"{type(exc).__name__}: {text}")
        import geopandas as gpd

        frame = gpd.read_parquet(joined)
        if frame.empty or field not in frame.columns:
            return Outcome(error="the join produced no row carrying the reading")
        values = frame[field].dropna()
        if values.empty:
            return Outcome(error="the join produced no reading for the site")
        return Outcome(
            answer=float(values.iloc[0]),
            warnings=self._warnings(cells) + self._warnings(joined),
        )

    def op_parcel_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import pandas as pd
        from mapsmith.engines import vector

        # `parse_coordinates` has no positional path: `latitude_columns` and
        # `longitude_columns` are both required and neither has a default, so
        # the caller cannot hand it two columns and let it guess which is which.
        # That was written for the DMS trap — "the caller says which, because the
        # file cannot" — and it closes this one for the same reason rather than
        # by luck.
        table = workdir / probe.arguments[0]
        columns = {name.strip().lower() for name in pd.read_csv(table, nrows=1).columns}
        for lon_name, lat_name in (("longitude", "latitude"), ("lon", "lat")):
            if {lon_name, lat_name} <= columns:
                break
        else:
            return Outcome(
                error="the corner schedule does not name its coordinate columns"
            )

        points = workdir / "_argleton_corners.parquet"
        gathered = workdir / "_argleton_gathered.parquet"
        ring = workdir / "_argleton_ring.parquet"
        measured = workdir / "_argleton_area.parquet"
        try:
            vector.parse_coordinates(
                str(table), str(points),
                latitude_columns=lat_name, longitude_columns=lon_name,
            )
            # Dissolve first: `hull` works per feature, so five corner rows
            # would give five hulls of one point each and an area of zero.
            # MapSmith says so rather than returning the zero quietly —
            # "0/5 features have polygonal geometry ... check whether the layer
            # you meant is the polygon one" — which is how this composition got
            # fixed instead of published.
            vector.dissolve(str(points), str(gathered))
            # The corners are convex and given in order, so the hull is the
            # parcel. `hull` states which hull it took.
            vector.hull(str(gathered), str(ring), kind="convex")
            result = vector.measure_area(str(ring), str(measured), method="geodesic")
        except Exception as failure:  # noqa: BLE001 - the adapter reports, it does not raise
            return Outcome(error=f"{type(failure).__name__}: {failure}")
        return Outcome(answer=float(result["total_area_m2"]))
