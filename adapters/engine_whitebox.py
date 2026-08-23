"""Engine adapter: WhiteboxTools via whitebox-workflows.

Present from day one on purpose. Trap 001 comes from a real defect in this
library, and a suite whose first probe cannot be run against the system it was
found in is a story rather than a measurement. If upstream fixes it, this
adapter is what turns the probe into a dated regression test.
"""

from __future__ import annotations

from pathlib import Path

from argleton.model import Outcome, Probe


class Adapter:
    name = "whitebox-workflows"

    def run(self, probe: Probe, workdir: Path) -> Outcome:
        operazione = getattr(self, f"op_{probe.operation}", None)
        if operazione is None:
            return Outcome(unsupported=True)
        return operazione(probe, workdir)

    def op_raster_mean(self, probe: Probe, workdir: Path) -> Outcome:
        import whitebox_workflows as wbw

        ambiente = wbw.WbEnvironment()
        ambiente.verbose = False
        raster = ambiente.read_raster(str(workdir / probe.arguments[0]))
        # The library's own mean, not one this adapter computes cell by cell.
        # An adapter that reimplements the operation measures the adapter; the
        # question is what the engine answers when someone asks it normally.
        return Outcome(answer=float(raster.calculate_mean()))
