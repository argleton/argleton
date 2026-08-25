"""Which run is the published one.

One function, because this question had three answers. The page builder, the
showcase test and the Pages workflow each sorted the directory names and took
the last, which works only while the names sort in the order they were made.
Two runs on one day broke that — "2026-08-25-eight-families" sorts before
"2026-08-25-six-families" — and all three agreed on the older run, so nothing
disagreed and nothing caught it.

`results/LATEST` names the published run. A pointer can be forgotten, which a
test checks; it cannot be wrong by accident, which sorting can.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def published_run(root: Path | None = None) -> Path:
    """The results directory `results/LATEST` names."""
    results = (root or ROOT) / "results"
    directories = sorted(p.name for p in results.iterdir() if p.is_dir())
    if not directories:
        raise RuntimeError("no results yet — run the suite before publishing anything")
    pointer = results / "LATEST"
    if not pointer.exists():
        raise RuntimeError(
            f"{pointer} is missing: write the name of the run to publish into it "
            f"(one of {directories})"
        )
    name = pointer.read_text(encoding="utf-8").strip()
    run = results / name
    if not run.is_dir():
        raise RuntimeError(
            f"results/LATEST names {name!r}, which is not a results directory "
            f"(have: {directories})"
        )
    return run


def published_results(root: Path | None = None) -> list[dict]:
    """Every result record in the published run, in filename order."""
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(published_run(root).glob("*.json"))
    ]
