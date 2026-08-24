"""The probe contract, loaded and validated.

Deliberately stdlib-only. Anyone must be able to read a probe, understand what
it claims, and check that claim without installing anything — a suite that needs
a toolchain to be inspected is asking to be trusted rather than checked.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

CONTRACT = "probe.toml"
POPULATIONS = ("trap", "clean")


@dataclass(frozen=True)
class Truth:
    kind: str
    value: Any
    tolerance: float
    derivation: str


@dataclass(frozen=True)
class NaiveFailure:
    description: str
    observed_value: Any
    why_plausible: str
    derivation: str | None = None


@dataclass(frozen=True)
class Probe:
    """One task whose correct answer is known by construction."""

    id: str
    population: Literal["trap", "clean"]
    family: str
    title: str
    surface: tuple[str, ...]
    call: str
    truth: Truth
    provenance: dict[str, Any]
    directory: Path
    prompt: str | None = None
    naive_failure: NaiveFailure | None = None
    accept_if_mentions: tuple[str, ...] = ()

    @property
    def operation(self) -> str:
        """The operation name in `task.call`, e.g. `raster_mean` in `raster_mean(dem.tif)`."""
        return _parse_call(self.call)[0]

    @property
    def arguments(self) -> tuple[str, ...]:
        return _parse_call(self.call)[1]


def _parse_call(call: str) -> tuple[str, tuple[str, ...]]:
    """`raster_mean(dem.tif, band=1)` → ("raster_mean", ("dem.tif", "band=1")).

    A grammar rather than `eval`: probe files come from contributors, and a
    suite that runs arbitrary code from its own fixtures cannot be run by the
    people it is meant to convince.
    """
    match = re.fullmatch(r"\s*([a-z][a-z0-9_]*)\s*\((.*)\)\s*", call, re.DOTALL)
    if not match:
        raise ValueError(f"task.call is not `name(args)`: {call!r}")
    name, inside = match.group(1), match.group(2).strip()
    args = tuple(a.strip() for a in inside.split(",")) if inside else ()
    return name, args


class ContractError(ValueError):
    """A probe file that does not honour the contract. Names the file and the field."""


def _require(data: dict, key: str, where: Path) -> Any:
    if key not in data:
        raise ContractError(f"{where}: missing required key `{key}`")
    return data[key]


def load_probe(directory: Path) -> Probe:
    """Read and check one probe directory.

    The checks here are the ones that make a published number mean something;
    the JSON Schema in `schema/` is the same contract for people who are not
    running this code. When they disagree, the schema is the specification.
    """
    path = directory / CONTRACT
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ContractError(f"{directory}: no {CONTRACT}") from None
    except tomllib.TOMLDecodeError as exc:
        raise ContractError(f"{path}: not valid TOML — {exc}") from None

    population = _require(data, "population", path)
    if population not in POPULATIONS:
        raise ContractError(f"{path}: population must be one of {POPULATIONS}")

    task = _require(data, "task", path)
    truth_data = _require(data, "truth", path)
    for key in ("kind", "value", "tolerance", "derivation"):
        _require(truth_data, f"truth.{key}" if key not in truth_data else key, path)

    naive, accepts = None, ()
    if population == "trap":
        raw = _require(data, "naive_failure", path)
        if not raw.get("plausible"):
            # The admission criterion, and the only one that is not taste. An
            # error that crashes or returns an absurd number is already caught
            # by something; this suite is for the answers nothing catches.
            raise ContractError(
                f"{path}: a trap must declare `plausible = true`. If the typical "
                "error is loud, the probe belongs in an ordinary test suite."
            )
        naive = NaiveFailure(
            description=raw["description"],
            observed_value=raw["observed_value"],
            why_plausible=raw["why_plausible"],
            derivation=raw.get("derivation"),
        )
        accepts = tuple(_require(data, "refusal", path)["accept_if_mentions"])
    elif "naive_failure" in data:
        raise ContractError(
            f"{path}: a clean probe cannot have a naive_failure. It is a trap "
            "filed in the wrong place, and it would corrupt the completion rate."
        )

    surfaces = tuple(_require(data, "surface", path))
    if "agent" in surfaces and not task.get("prompt"):
        raise ContractError(f"{path}: surface includes `agent` but task.prompt is missing")

    return Probe(
        id=_require(data, "id", path),
        population=population,
        family=_require(data, "family", path),
        title=_require(data, "title", path),
        surface=surfaces,
        call=_require(task, "call", path),
        prompt=task.get("prompt"),
        truth=Truth(truth_data["kind"], truth_data["value"], float(truth_data["tolerance"]),
                    truth_data["derivation"]),
        naive_failure=naive,
        accept_if_mentions=accepts,
        provenance=_require(data, "provenance", path),
        directory=directory,
    )


def discover(root: Path) -> list[Probe]:
    """Every probe under `traps/` and `clean/`, in a stable order.

    Stable because published results are compared across runs and across
    systems: an ordering that depends on the filesystem would make two honest
    runs look different.
    """
    folders = {"trap": root / "traps", "clean": root / "clean"}
    found = [
        load_probe(contratto.parent)
        for folder in folders.values()
        for contratto in sorted(folder.rglob(CONTRACT))
    ]
    duplicates = {p.id for p in found if [q.id for q in found].count(p.id) > 1}
    if duplicates:
        raise ContractError(f"duplicate probe ids: {sorted(duplicates)}")
    return sorted(found, key=lambda p: (p.population, p.id))


@dataclass
class Outcome:
    """What a system did with one probe.

    Four mutually exclusive shapes, and the runner refuses anything ambiguous:
    an adapter that returns both an answer and a refusal has not decided what
    the system did, and guessing on its behalf is how a score stops meaning
    anything.
    """

    answer: Any = None
    refusal: str | None = None
    error: str | None = None
    unsupported: bool = False
    warnings: list[str] = field(default_factory=list)
    transcript: str | None = None

    def __post_init__(self) -> None:
        declared = sum(
            x is not None and x is not False
            for x in (self.answer, self.refusal, self.error, self.unsupported or None)
        )
        if declared > 1:
            raise ValueError(
                "an Outcome is exactly one of answer / refusal / error / unsupported; "
                f"got {declared}"
            )
