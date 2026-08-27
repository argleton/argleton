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


def _default_root() -> Path:
    """Where the probes are: the repository if we are in it, the package if not.

    Two layouts, and the difference is not cosmetic. Run from a checkout, the
    probes are `traps/` and `clean/` beside the package and that is what a
    contributor edits. Installed from PyPI, they are bundled inside the package,
    because a wheel that ships the runner without the probes is a command that
    finds nothing and exits 2 — and looks like it worked.
    """
    checkout = Path(__file__).resolve().parent.parent
    if (checkout / "traps").is_dir():
        return checkout
    bundled = Path(__file__).resolve().parent / "probes"
    if (bundled / "traps").is_dir():
        return bundled
    return checkout


ROOT = _default_root()


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
    proc = subprocess.run(
        [sys.executable, str(builder), str(workdir)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{probe.id}: build.py failed\n{proc.stdout}\n{proc.stderr}")


def load_adapter(name: str):
    """`engine:rasterio` → adapters.engine_rasterio; `x.y:Z` → an importable object."""
    if name.startswith("engine:"):
        module = importlib.import_module(f"adapters.engine_{name.split(':', 1)[1]}")
        return module.Adapter()
    module, _, attr = name.partition(":")
    loaded = importlib.import_module(module)
    return getattr(loaded, attr or "Adapter")()


def run_probe(adapter, probe: Probe, keep: Path | None = None) -> tuple[Outcome, Verdict]:
    with tempfile.TemporaryDirectory(prefix=f"argleton-{probe.id}-") as tmp:
        workdir = Path(keep / probe.id) if keep else Path(tmp)
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
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            # Probe text is UTF-8 and consoles are not, on the platform where
            # this was written. A mangled tolerance sign in a published run is
            # a small thing that makes a careful reader distrust the rest.
            stream.reconfigure(encoding="utf-8", errors="replace")

    sys.path.insert(0, str(args.root))
    probes = discover(args.root)
    if args.population:
        probes = [p for p in probes if p.population == args.population]
    if args.only:
        probes = [p for p in probes if p.id in set(args.only)]
    if not probes:
        print("no probes matched", file=sys.stderr)
        return 2

    adapter = load_adapter(args.adapter)
    verdicts, details = [], []
    for probe in probes:
        _outcome, verdict = run_probe(adapter, probe, args.keep)
        verdicts.append(verdict)
        details.append(asdict(verdict))
        mark = {True: "ok  ", False: "FAIL", None: "skip"}[verdict.success]
        print(f"{mark} {probe.population:5} {probe.id:28} "
              f"{verdict.verdict:22} {verdict.detail[:70]}")

    summary = summarise(verdicts)
    result = {
        "system": args.system or getattr(adapter, "name", args.adapter),
        "adapter": args.adapter,
        "spec_commit": spec_commit(args.root),
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        **summary,
        "per_probe": details,
    }
    print(
        f"\nsilent_error_rate {summary['silent_error_rate']} "
        f"over {summary['traps_run']} traps  |  "
        f"completion_rate {summary['completion_rate']} over {summary['clean_run']} clean"
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"written {args.out}")

    # Exit 0 even with silent errors: finding them is the job, not the alarm.
    # A non-zero exit is for the runner failing to do its own job.
    return 0


def spec_commit(root: Path) -> str:
    """The commit the probes were at, so a result can never float free of its rules.

    Pre-registration that is checkable instead of asserted: every result names
    the commit it ran against, so anyone wondering whether we widened a
    tolerance after seeing a number reads a diff rather than our word for it.
    """
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    dirty = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        capture_output=True, text=True, check=False,
    ).stdout.strip()
    commit = proc.stdout.strip() or "unknown"
    return f"{commit}-dirty" if dirty else commit


if __name__ == "__main__":
    raise SystemExit(main())
