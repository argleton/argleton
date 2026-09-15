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

**What this row is a row of, stated narrowly, because one measurement made the
narrowness matter.** `qgis_process` runs with no project, and a project carries
an ellipsoid. Asked the same algorithms with the same parameters inside a *live*
QGIS — whose default project sets `EPSG:7030` — the same trap came back as
**92899.397** instead of 1000000.0, because `$area` is ellipsoidal there and
planar here: a factor of 10.8 between two systems that are the same QGIS
(measured 2026-09-14 through the QGIS Agent MCP bridge, with the project's
ellipsoid read back from `project.properties` rather than inferred).

That measurement is why the shared chain now asks for `area($geometry)`, which is
planar wherever it runs, instead of `$area`, which is whatever the open project
says. **In the published run the three QGIS rows therefore agree on this trap**,
all at 1000000.0, and the divergence above is not visible in the table — it was
never a property of the systems, it was a question we were asking two different
ways. Four probes still carry a warning that the ellipsoid the question wants
cannot be passed through a live QGIS at all. So: **this row is QGIS processing
driven without a project**, which is what a headless caller gets, and it is still
not interchangeable with QGIS inside its desktop — the difference now shows up as
a disclosed warning rather than as a number nobody could explain.

**Three facts about the harness, all measured rather than assumed.** Startup has
two speeds and they are not free of consequence: `--no-python
--skip-loading-plugins` answers in about 1.5 seconds against about 23 with
everything loaded, and the buffer output was identical either way — but the
`gdal:` family is *part of the Processing plugin*, so warping a raster and the
raster calculator are unreachable through the fast door. Two operations here open
the slow one and the rest do not, which is why the flag is per call. And QGIS
writes its own diagnostics to stdout *before* the JSON document — including the
transformation warnings a wrapper throws away — so this adapter keeps them and
reports them as the system's own disclosure.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from adapters.qgis_chains import QgisChains

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


class Adapter(QgisChains):
    name = "qgis_process"

    # --- plumbing -------------------------------------------------------

    def __init__(self) -> None:
        self._executable: str | None = None

    def _call(
        self,
        algorithm: str,
        workdir: Path,
        ellipsoid: str | None = None,
        providers: str = "core",
        **parameters: object,
    ) -> tuple[dict, list[str]]:
        """Run one algorithm and return its results plus what QGIS said out loud.

        `providers="all"` is the slow door and is only opened where an algorithm
        needs it. Measured on 2026-09-14: the C++ providers alone answer in about
        1.5 seconds, and loading the Python ones takes about 23 — but the whole
        `gdal:` family lives in the Processing *plugin*, so warping a raster or
        running a raster calculator is unreachable through the fast door. The
        flag is per call rather than per run so that one raster operation does
        not make sixty vector ones fifteen times slower.
        """
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
        speed = [] if providers == "all" else ["--no-python", "--skip-loading-plugins"]
        process = subprocess.run(
            [self._executable, *speed, "run", algorithm, "-"],
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

