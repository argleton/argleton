"""Engine adapter: the composition almost everyone writes first.

Read the file, sum `.area`, report it as square metres. It is not a straw man
and it is not a bug in Shapely: it is what a correct-looking three-line function
does, it is what a great deal of published analysis code does, and it is right
whenever the data happens to be in metres — which is most of the time, until it
is not.

It is in the repository because a suite that only measures careful systems
cannot show what the careless answer looks like, and the whole argument is that
the careless answer looks fine.
"""

from __future__ import annotations

from pathlib import Path

from argleton.model import Outcome, Probe


class Adapter:
    name = "shapely-naive"

    def run(self, probe: Probe, workdir: Path) -> Outcome:
        operazione = getattr(self, f"op_{probe.operation}", None)
        if operazione is None:
            return Outcome(unsupported=True)
        return operazione(probe, workdir)

    def op_planar_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd

        return Outcome(answer=float(gpd.read_file(workdir / probe.arguments[0]).area.sum()))
