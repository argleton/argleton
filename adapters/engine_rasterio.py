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
