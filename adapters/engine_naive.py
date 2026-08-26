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

    # ---- tier A: the compositions almost everyone writes first ---------------

    def op_buildable_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # Iterate the rings and add them up. The outer ring is the parcel and
        # the inner one is a courtyard, but a ring is a ring to this loop.
        frame = gpd.read_file(workdir / probe.arguments[0])
        from shapely.geometry import Polygon

        total = 0.0
        for geometry in frame.geometry:
            total += Polygon(geometry.exterior).area
            total += sum(Polygon(ring).area for ring in geometry.interiors)
        return Outcome(answer=float(total))

    def op_total_ground_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # "How much in total" -> sum the areas. Right whenever nothing overlaps.
        return Outcome(answer=float(gpd.read_file(workdir / probe.arguments[0]).area.sum()))

    def op_pipe_length_m(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # .length is 2D and says nothing about it; the Z is right there in the
        # geometry, unused.
        return Outcome(answer=float(gpd.read_file(workdir / probe.arguments[0]).length.sum()))

    def op_district_of_parcel(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # Reduce the polygon to a point, then ask where the point is. The
        # standard way to give a polygon a position.
        parcel = gpd.read_file(workdir / probe.arguments[0])
        districts = gpd.read_file(workdir / probe.arguments[1])
        point = parcel.geometry.iloc[0].centroid
        for _, row in districts.iterrows():
            if row.geometry.contains(point):
                return Outcome(answer=str(row["district"]))
        return Outcome(answer="")

    def op_wells_in_districts(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # An inner spatial join with `within`, which is the default habit.
        wells = gpd.read_file(workdir / probe.arguments[0])
        districts = gpd.read_file(workdir / probe.arguments[1])
        return Outcome(answer=len(gpd.sjoin(wells, districts, predicate="within")))

    def op_latitude_decimal(self, probe: Probe, workdir: Path) -> Outcome:
        import pandas as pd

        station = probe.arguments[1].split("=", 1)[1]
        rows = pd.read_csv(workdir / probe.arguments[0])
        row = rows[rows["station_id"] == station].iloc[0]
        if "latitude" in rows.columns:
            return Outcome(answer=float(row["latitude"]))
        # The three fields pasted together as a decimal.
        return Outcome(answer=float(f"{row.lat_deg}.{row.lat_min}{row.lat_sec}"))

    def op_area_unemployment_rate_pct(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # Average the rate column: what `mean` is for.
        frame = gpd.read_file(workdir / probe.arguments[0])
        return Outcome(answer=float(frame["unemployment_rate_pct"].mean()))

    def op_total_population(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        import pandas as pd

        # read_csv with no dtype: "001" becomes 1 and matches nothing.
        municipalities = gpd.read_file(workdir / probe.arguments[0])
        population = pd.read_csv(workdir / probe.arguments[1])
        joined = municipalities.merge(
            population.astype({"istat_code": str}), on="istat_code", how="inner"
        )
        return Outcome(answer=int(joined["population"].sum()))

    def op_flooded_farmland_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        # Select what intersects, sum what was selected. The selection is right.
        fields = gpd.read_file(workdir / probe.arguments[0])
        band = gpd.read_file(workdir / probe.arguments[1]).union_all()
        return Outcome(answer=float(fields[fields.intersects(band)].area.sum()))

    def op_sheet_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        import pandas as pd

        # Join, then sum. Nothing warns that the join changed the row count.
        parcels = gpd.read_file(workdir / probe.arguments[0])
        owners = pd.read_csv(workdir / probe.arguments[1])
        return Outcome(answer=float(parcels.merge(owners, on="parcel_id")["area_m2"].sum()))

    def op_ndvi_mean(self, probe: Probe, workdir: Path) -> Outcome:
        import numpy as np
        import rasterio

        red_band = int(probe.arguments[1].split("=", 1)[1])
        nir_band = int(probe.arguments[2].split("=", 1)[1])
        with rasterio.open(workdir / probe.arguments[0]) as ds:
            # Read the two bands, put them in the formula. GDAL states that
            # applying scale and offset is the caller's job and RasterIO will
            # not do it; nothing in the returned array says it was skipped.
            red = ds.read(red_band).astype("float64")
            nir = ds.read(nir_band).astype("float64")
        return Outcome(answer=float(np.mean((nir - red) / (nir + red))))

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
