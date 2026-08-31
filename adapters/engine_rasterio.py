"""Engine adapter: rasterio/GDAL, called directly.

The engine level is the floor of this suite. It costs nothing, it is
deterministic, it runs in CI on every commit, and anyone can rerun it and
contest the numbers in a minute. The agent level is where the interesting
configuration lives, but a benchmark whose cheapest tier costs money is a
benchmark nobody independently checks.
"""

from __future__ import annotations

from pathlib import Path

from argleton.model import Outcome, Probe


class Adapter:
    name = "rasterio"

    def run(self, probe: Probe, workdir: Path) -> Outcome:
        operation = getattr(self, f"op_{probe.operation}", None)
        if operation is None:
            # Not a failure: the system was never asked. Scoring an unimplemented
            # operation as wrong would measure the adapter, not the engine.
            return Outcome(unsupported=True)
        return operation(probe, workdir)


    def op_raster_ground_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import rasterio

        path = workdir / probe.arguments[0]
        # The task says to use the georeferencing stored in the GeoTIFF, and
        # honouring that means knowing whether anything else is claiming to
        # georeference the same file. A `.aux.xml` beside it does, and by GDAL's
        # documented precedence it wins unless asked otherwise.
        sidecar = path.with_suffix(path.suffix + ".aux.xml")
        opened_with = "internal georeferencing"
        with rasterio.Env(GDAL_GEOREF_SOURCES="INTERNAL"), rasterio.open(path) as ds:
            cell_area = abs(ds.transform.a * ds.transform.e)
            area = float(cell_area * ds.width * ds.height)
        said = [f"read with {opened_with}"]
        if sidecar.exists():
            # Said out loud: the number is one of two the file can produce, and
            # an answer that does not name the source is not reproducible.
            said.append(
                f"{sidecar.name} also georeferences this raster and would give a "
                "different answer; GDAL prefers it by default"
            )
        return Outcome(answer=area, warnings=said)

    def op_lowest_cell_easting(self, probe: Probe, workdir: Path) -> Outcome:
        import numpy as np
        import rasterio

        # `ds.xy` returns the centre of the cell under the pixel-is-AREA
        # reading, always, and there is no argument on it that mentions
        # registration. The correction is not obscure and it is not a
        # workaround: the file says which convention it uses and rasterio hands
        # that over on the same open dataset.
        #
        # Under pixel-is-POINT the value is a sample AT the node, so the tie
        # point IS the position of pixel (0, 0) and every cell centre `xy`
        # computes is half a cell too far east and south.
        with rasterio.open(workdir / probe.arguments[0]) as ds:
            values = ds.read(1, masked=True)
            row, column = np.unravel_index(np.argmin(values), values.shape)
            easting, _ = ds.xy(int(row), int(column))
            if ds.tags().get("AREA_OR_POINT") == "Point":
                easting -= ds.transform.a / 2.0
        return Outcome(answer=float(easting))


    def op_mean_slope_degrees(self, probe: Probe, workdir: Path) -> Outcome:
        import numpy as np
        import rasterio

        with rasterio.open(workdir / probe.arguments[0]) as ds:
            elevation = ds.read(1).astype("float64")
            width, height = ds.res
        # `res` is the size of a cell and is positive whichever way the rows
        # run: the direction lives in the sign of the transform, not here. So
        # this is right on both halves of the pair without knowing there is a
        # pair — which is the finding, not a virtue of the code.
        along_rows, along_columns = np.gradient(elevation, height, width)
        slope = np.degrees(np.arctan(np.hypot(along_columns, along_rows)))
        return Outcome(answer=float(slope.mean()))

    def op_ndvi_mean(self, probe: Probe, workdir: Path) -> Outcome:
        import numpy as np
        import rasterio

        red_band = int(probe.arguments[1].split("=", 1)[1])
        nir_band = int(probe.arguments[2].split("=", 1)[1])
        with rasterio.open(workdir / probe.arguments[0]) as ds:
            # rasterio exposes what the file declares; applying it is still the
            # caller's job, and this is the caller doing it. A scale of 1 and an
            # offset of 0 is the no-op the clean twin needs.
            scales, offsets = ds.scales, ds.offsets
            red = ds.read(red_band).astype("float64") * scales[red_band - 1] + offsets[
                red_band - 1
            ]
            nir = ds.read(nir_band).astype("float64") * scales[nir_band - 1] + offsets[
                nir_band - 1
            ]
        return Outcome(answer=float(np.mean((nir - red) / (nir + red))))

    def op_class_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import rasterio
        from rasterio.enums import Resampling

        resolution = float(probe.arguments[1].split("=", 1)[1])
        wanted = int(probe.arguments[2].split("=", 1)[1])
        with rasterio.open(workdir / probe.arguments[0]) as ds:
            if ds.crs is None:
                return Outcome(
                    refusal="the raster declares no CRS, so a resolution in metres "
                    "cannot be interpreted"
                )
            left, bottom, right, top = ds.bounds
            width = round((right - left) / resolution)
            height = round((top - bottom) / resolution)
            # The question states a legend, so these are class codes: nearest
            # neighbour keeps the codes that exist. Same information the naive
            # composition had and did not use — the difference measured here is
            # the reading of the question, not the capability of the library.
            band = ds.read(
                1, out_shape=(1, height, width), resampling=Resampling.nearest
            )
        cells = int((band == wanted).sum())
        return Outcome(answer=float(cells * resolution * resolution))

    def op_raster_mean(self, probe: Probe, workdir: Path) -> Outcome:
        import numpy as np
        import rasterio

        with rasterio.open(workdir / probe.arguments[0]) as ds:
            band = ds.read(1, masked=True)
        return Outcome(answer=float(np.ma.mean(band)))
