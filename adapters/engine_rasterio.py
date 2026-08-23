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
        operazione = getattr(self, f"op_{probe.operation}", None)
        if operazione is None:
            # Not a failure: the system was never asked. Scoring an unimplemented
            # operation as wrong would measure the adapter, not the engine.
            return Outcome(unsupported=True)
        return operazione(probe, workdir)

    def op_raster_mean(self, probe: Probe, workdir: Path) -> Outcome:
        import numpy as np
        import rasterio

        with rasterio.open(workdir / probe.arguments[0]) as ds:
            banda = ds.read(1, masked=True)
        return Outcome(answer=float(np.ma.mean(banda)))
