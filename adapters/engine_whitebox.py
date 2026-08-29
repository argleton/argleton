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
        operation = getattr(self, f"op_{probe.operation}", None)
        if operation is None:
            return Outcome(unsupported=True)
        return operation(probe, workdir)


    def op_lowest_cell_easting(self, probe: Probe, workdir: Path) -> Outcome:
        import whitebox_workflows as wbw

        # Whitebox has no "where is the minimum" tool, so this is the composition
        # its API invites: read the raster, walk it, and convert the index with
        # the grid description the library itself reports.
        wbe = wbw.WbEnvironment()
        wbe.verbose = False
        raster = wbe.read_raster(str(workdir / probe.arguments[0]))
        meta = raster.metadata()
        lowest, position = None, (0, 0)
        for row in range(meta.rows):
            for column in range(meta.columns):
                value = raster[row, column]
                if value == meta.nodata:
                    continue
                if lowest is None or value < lowest:
                    lowest, position = value, (row, column)
        # `west` as the library reports it, plus half a cell for the centre.
        easting = meta.west + (position[1] + 0.5) * meta.resolution_x
        return Outcome(answer=float(easting))

    def op_raster_mean(self, probe: Probe, workdir: Path) -> Outcome:
        import whitebox_workflows as wbw

        env = wbw.WbEnvironment()
        env.verbose = False
        raster = env.read_raster(str(workdir / probe.arguments[0]))
        # The library's own mean, not one this adapter computes cell by cell.
        # An adapter that reimplements the operation measures the adapter; the
        # question is what the engine answers when someone asks it normally.
        return Outcome(answer=float(raster.calculate_mean()))
