"""Engine adapter: the QGIS processing engine, driven headless through `qgis_process`.

**What this measures, and it is narrower than the name suggests.** This is not a
score for QGIS the application, and it is not a score for any QGIS MCP server.
It is the QGIS *processing* engine asked, through its own command line, for the
thing each probe asks for — with the parameters QGIS offers and nothing added on
top.

That last clause is the whole design, and it is deliberate in both directions:

- **Nothing is added.** No reprojection the question did not ask for, no unit
  conversion, no validity repair, no ellipsoid unless the question is about
  ground distance. `engine_geopandas` is the opposite pole — the same class of
  library composed by a caller who knows — and the gap between the two rows is
  the point of having both.
- **Nothing is sabotaged either.** Where QGIS offers a parameter that answers
  the question (a named layer in a multi-layer container, an ellipsoid for a
  ground area), this adapter passes it. A row produced by withholding an
  argument the API offers would measure the adapter's manners, not the engine.

Why it exists at all, and it is not to add a competitor to the table: the two
QGIS MCP servers (`nkarasiak/qgis-mcp` and QGIS Agent MCP) both funnel every
request into `processing.run`. When a trap falls on one of them, without this
row nobody can say whether the fault is the wrapper's or the engine's
underneath — which is the discipline of saying whose limit each number is.

Measured on 2026-09-13, before a line of this file existed: on 002-feet-as-metres
the engine answers **1000000.0** where the truth is 92903.41, because `$area`
returns square feet and says nothing about it. That is the shape of every number
on this row: plausible, confident, and unqualified.

**Two facts about the harness, both measured rather than assumed.** `qgis_process`
starts in about 65 seconds on a warm cache and in about 3 with `--no-python`,
which disables the Python-written providers (GRASS, SAGA) and leaves the C++ ones
(`native:`, `qgis:`, `gdal:`) that every probe here needs; the buffer output was
byte-identical either way. And QGIS writes its own diagnostics to stdout *before*
the JSON document — including the transformation warnings a wrapper throws away —
so this adapter keeps them and reports them as the system's own disclosure.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from argleton.model import Outcome, Probe

# Log lines QGIS prints on stdout that are noise rather than disclosure. Kept as
# a deny-list rather than an allow-list on purpose: an unknown line from the
# engine is far more likely to be something the caller should have seen than
# something worth hiding, and this row exists to show what wrappers discard.
_NOISE = (
    "QStandardPaths:",
    "Warning: loading of",
    "Application state:",
)


def _executable() -> str:
    """Find `qgis_process`, and fail with an instruction rather than a traceback."""
    override = os.environ.get("ARGLETON_QGIS_PROCESS")
    if override:
        return override
    found = shutil.which("qgis_process") or shutil.which("qgis_process.bat")
    if found:
        return found
    # Windows installs it under the versioned program directory, and the LTR
    # build spells the file differently from the release one. Sorted so that a
    # machine with two QGIS versions picks the same one twice in a row rather
    # than whatever the filesystem happened to hand back.
    for base in (Path("C:/Program Files"), Path("C:/Program Files (x86)")):
        candidates = sorted(base.glob("QGIS */bin/qgis_process-qgis*.bat"))
        if candidates:
            return str(candidates[-1])
    raise RuntimeError(
        "qgis_process not found. Install QGIS, or point ARGLETON_QGIS_PROCESS at "
        "the qgis_process executable."
    )


def _parse(stdout: str) -> tuple[dict, list[str]]:
    """Split QGIS's stdout into (JSON document, the log lines that preceded it).

    The JSON is pretty-printed and always the tail of the stream, so the document
    starts at the first line that is exactly `{`. Searching for the first `{`
    anywhere would find one inside a log line — the PROJ pipelines QGIS quotes in
    its transformation warnings contain braces.
    """
    lines = stdout.splitlines()
    for index, line in enumerate(lines):
        if line.rstrip() == "{":
            document = json.loads("\n".join(lines[index:]))
            log = [entry.strip() for entry in lines[:index] if entry.strip()]
            return document, log
    raise RuntimeError(f"qgis_process produced no JSON document. Output: {stdout[-800:]!r}")


class Adapter:
    name = "qgis_process"

    # --- plumbing -------------------------------------------------------

    def __init__(self) -> None:
        self._executable: str | None = None

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
        **parameters: object,
    ) -> tuple[dict, list[str]]:
        """Run one algorithm and return its results plus what QGIS said out loud."""
        if self._executable is None:
            self._executable = _executable()
        # Parameters go in on STDIN as JSON, not as `--KEY=VALUE` arguments, and
        # it is not a style preference. On Windows `qgis_process` is a .bat, so
        # the command line is re-parsed by cmd.exe — which reads the `|` in
        # `path|layername=wells` as a pipe and tries to run `layername` as a
        # program. Measured on 2026-09-14: the whole call died with «"layername"
        # is not recognized as an internal or external command», which reads on
        # a results table exactly like a system that cannot open a named layer.
        # The JSON channel is documented by the CLI, takes the ellipsoid and the
        # project path as keys, and implies --json for the output.
        payload: dict[str, object] = {"inputs": parameters}
        if ellipsoid is not None:
            payload["ellipsoid"] = ellipsoid
        process = subprocess.run(
            [self._executable, "--no-python", "--skip-loading-plugins", "run", algorithm, "-"],
            input=json.dumps(payload),
            cwd=str(workdir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            check=False,
        )
        if process.returncode != 0:
            detail = (process.stdout or process.stderr or "")[-800:]
            raise RuntimeError(f"{algorithm} failed (rc={process.returncode}): {detail.strip()}")
        document, log = _parse(process.stdout)
        return document.get("results", {}), [line for line in log if not line.startswith(_NOISE)]

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
        total, _, stat_log = self._sum_of(calculated, "m", workdir)
        return total, calc_log + stat_log

    # --- vector: area ---------------------------------------------------

    def op_planar_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # `$area` with no ellipsoid set is planar, in the layer's own units,
        # and QGIS neither converts them nor names them. Asking for square
        # metres is the caller's business; this row records what the engine
        # hands back when asked the way the question was asked.
        total, log = self._measure(probe.arguments[0], "$area", workdir)
        return Outcome(answer=total, warnings=log)

    def op_field_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        total, log = self._measure(probe.arguments[0], "$area", workdir)
        return Outcome(answer=total, warnings=log)

    def op_buildable_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        # A polygon's rings are the engine's business: `$area` subtracts the
        # interior ones, and whether a ring IS interior is decided by the format.
        total, log = self._measure(probe.arguments[0], "$area", workdir)
        return Outcome(answer=total, warnings=log)

    def op_net_plot_area_m2(self, probe: Probe, workdir: Path) -> Outcome:
        total, log = self._measure(probe.arguments[0], "$area", workdir)
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
        total, log = self._measure("_dissolved.gpkg", "$area", workdir)
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
        total, log = self._measure("_workable.gpkg", "$area", workdir)
        return Outcome(answer=total, warnings=difference_log + log)

    # --- vector: length, counts ------------------------------------------

    def op_pipe_length_total_m(self, probe: Probe, workdir: Path) -> Outcome:
        total, log = self._measure(probe.arguments[0], "$length", workdir)
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
