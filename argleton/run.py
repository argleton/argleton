"""The runner: build the fixtures, ask a system, write a result nobody has to trust.

Fixtures are built, never vendored. The repo stays in kilobytes, anyone can
regenerate them and check they are what we say they are, and rerunning the whole
suite costs nothing — which is half of why a third party can contest our numbers
in an afternoon instead of taking them on faith.
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from .model import Outcome, Probe, discover
from .score import Verdict, judge, summarise

ROOT = Path(__file__).resolve().parent.parent


def build_fixtures(probe: Probe, workdir: Path) -> None:
    """Run the probe's `build.py` into a fresh directory.

    A subprocess rather than an import: fixture builders are the part of this
    repo most likely to come from someone else, and a builder that leaks state
    into the runner would make two probes depend on the order they ran in —
    the kind of defect this suite is supposed to be above.
    """
    builder = probe.directory / "build.py"
    if not builder.exists():
        return
    esito = subprocess.run(
        [sys.executable, str(builder), str(workdir)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300, check=False,
    )
    if esito.returncode != 0:
        raise RuntimeError(f"{probe.id}: build.py failed\n{esito.stdout}\n{esito.stderr}")


def load_adapter(nome: str):
    """`engine:rasterio` → adapters.engine_rasterio; `x.y:Z` → an importable object."""
    if nome.startswith("engine:"):
        modulo = importlib.import_module(f"adapters.engine_{nome.split(':', 1)[1]}")
        return modulo.Adapter()
    modulo, _, attributo = nome.partition(":")
    caricato = importlib.import_module(modulo)
    return getattr(caricato, attributo or "Adapter")()


def run_probe(adapter, probe: Probe, keep: Path | None = None) -> tuple[Outcome, Verdict]:
    with tempfile.TemporaryDirectory(prefix=f"argleton-{probe.id}-") as temporanea:
        workdir = Path(keep / probe.id) if keep else Path(temporanea)
        workdir.mkdir(parents=True, exist_ok=True)
        try:
            build_fixtures(probe, workdir)
            outcome = adapter.run(probe, workdir)
        except Exception as exc:  # noqa: BLE001 — an adapter that raises has errored, not crashed us
            outcome = Outcome(error=f"{type(exc).__name__}: {exc}")
    return outcome, judge(probe, outcome)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="argleton", description=__doc__.splitlines()[0])
    parser.add_argument("--adapter", required=True,
                        help="engine:rasterio, engine:whitebox, or module:Class")
    parser.add_argument("--system", help="name of the system under test, for the result file")
    parser.add_argument("--only", nargs="*", default=None, help="probe ids to run")
    parser.add_argument("--population", choices=("trap", "clean"), default=None)
    parser.add_argument("--out", type=Path, help="write the result JSON here")
    parser.add_argument("--keep", type=Path, help="keep the built fixtures in this directory")
    parser.add_argument("--root", type=Path, default=ROOT)
    argomenti = parser.parse_args(argv)
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            # Probe text is UTF-8 and consoles are not, on the platform where
            # this was written. A mangled tolerance sign in a published run is
            # a small thing that makes a careful reader distrust the rest.
            flusso.reconfigure(encoding="utf-8", errors="replace")

    sys.path.insert(0, str(argomenti.root))
    probes = discover(argomenti.root)
    if argomenti.population:
        probes = [p for p in probes if p.population == argomenti.population]
    if argomenti.only:
        probes = [p for p in probes if p.id in set(argomenti.only)]
    if not probes:
        print("no probes matched", file=sys.stderr)
        return 2

    adapter = load_adapter(argomenti.adapter)
    verdetti, dettagli = [], []
    for probe in probes:
        _outcome, verdetto = run_probe(adapter, probe, argomenti.keep)
        verdetti.append(verdetto)
        dettagli.append(asdict(verdetto))
        segno = {True: "ok  ", False: "FAIL", None: "skip"}[verdetto.success]
        print(f"{segno} {probe.population:5} {probe.id:28} "
              f"{verdetto.verdict:22} {verdetto.detail[:70]}")

    riassunto = summarise(verdetti)
    risultato = {
        "system": argomenti.system or getattr(adapter, "name", argomenti.adapter),
        "adapter": argomenti.adapter,
        "spec_commit": spec_commit(argomenti.root),
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        **riassunto,
        "per_probe": dettagli,
    }
    print(
        f"\nsilent_error_rate {riassunto['silent_error_rate']} "
        f"over {riassunto['traps_run']} traps  |  "
        f"completion_rate {riassunto['completion_rate']} over {riassunto['clean_run']} clean"
    )
    if argomenti.out:
        argomenti.out.parent.mkdir(parents=True, exist_ok=True)
        argomenti.out.write_text(json.dumps(risultato, indent=2) + "\n", encoding="utf-8")
        print(f"written {argomenti.out}")

    # Exit 0 even with silent errors: finding them is the job, not the alarm.
    # A non-zero exit is for the runner failing to do its own job.
    return 0


def spec_commit(root: Path) -> str:
    """The commit the probes were at, so a result can never float free of its rules.

    Pre-registration that is checkable instead of asserted: every result names
    the commit it ran against, so anyone wondering whether we widened a
    tolerance after seeing a number reads a diff rather than our word for it.
    """
    esito = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    sporco = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        capture_output=True, text=True, check=False,
    ).stdout.strip()
    commit = esito.stdout.strip() or "unknown"
    return f"{commit}-dirty" if sporco else commit


if __name__ == "__main__":
    raise SystemExit(main())
