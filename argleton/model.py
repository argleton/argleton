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
    name, dentro = match.group(1), match.group(2).strip()
    argomenti = tuple(a.strip() for a in dentro.split(",")) if dentro else ()
    return name, argomenti


class ContractError(ValueError):
    """A probe file that does not honour the contract. Names the file and the field."""


def _require(dati: dict, chiave: str, dove: Path) -> Any:
    if chiave not in dati:
        raise ContractError(f"{dove}: missing required key `{chiave}`")
    return dati[chiave]


def load_probe(directory: Path) -> Probe:
    """Read and check one probe directory.

    The checks here are the ones that make a published number mean something;
    the JSON Schema in `schema/` is the same contract for people who are not
    running this code. When they disagree, the schema is the specification.
    """
    percorso = directory / CONTRACT
    try:
        dati = tomllib.loads(percorso.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ContractError(f"{directory}: no {CONTRACT}") from None
    except tomllib.TOMLDecodeError as exc:
        raise ContractError(f"{percorso}: not valid TOML — {exc}") from None

    popolazione = _require(dati, "population", percorso)
    if popolazione not in POPULATIONS:
        raise ContractError(f"{percorso}: population must be one of {POPULATIONS}")

    task = _require(dati, "task", percorso)
    verita = _require(dati, "truth", percorso)
    for chiave in ("kind", "value", "tolerance", "derivation"):
        _require(verita, f"truth.{chiave}" if chiave not in verita else chiave, percorso)

    naive, accetta = None, ()
    if popolazione == "trap":
        grezzo = _require(dati, "naive_failure", percorso)
        if not grezzo.get("plausible"):
            # The admission criterion, and the only one that is not taste. An
            # error that crashes or returns an absurd number is already caught
            # by something; this suite is for the answers nothing catches.
            raise ContractError(
                f"{percorso}: a trap must declare `plausible = true`. If the typical "
                "error is loud, the probe belongs in an ordinary test suite."
            )
        naive = NaiveFailure(
            description=grezzo["description"],
            observed_value=grezzo["observed_value"],
            why_plausible=grezzo["why_plausible"],
            derivation=grezzo.get("derivation"),
        )
        accetta = tuple(_require(dati, "refusal", percorso)["accept_if_mentions"])
    elif "naive_failure" in dati:
        raise ContractError(
            f"{percorso}: a clean probe cannot have a naive_failure. It is a trap "
            "filed in the wrong place, and it would corrupt the completion rate."
        )

    superfici = tuple(_require(dati, "surface", percorso))
    if "agent" in superfici and not task.get("prompt"):
        raise ContractError(f"{percorso}: surface includes `agent` but task.prompt is missing")

    return Probe(
        id=_require(dati, "id", percorso),
        population=popolazione,
        family=_require(dati, "family", percorso),
        title=_require(dati, "title", percorso),
        surface=superfici,
        call=_require(task, "call", percorso),
        prompt=task.get("prompt"),
        truth=Truth(verita["kind"], verita["value"], float(verita["tolerance"]),
                    verita["derivation"]),
        naive_failure=naive,
        accept_if_mentions=accetta,
        provenance=_require(dati, "provenance", percorso),
        directory=directory,
    )


def discover(root: Path) -> list[Probe]:
    """Every probe under `traps/` and `clean/`, in a stable order.

    Stable because published results are compared across runs and across
    systems: an ordering that depends on the filesystem would make two honest
    runs look different.
    """
    cartelle = {"trap": root / "traps", "clean": root / "clean"}
    trovate = [
        load_probe(contratto.parent)
        for cartella in cartelle.values()
        for contratto in sorted(cartella.rglob(CONTRACT))
    ]
    doppioni = {p.id for p in trovate if [q.id for q in trovate].count(p.id) > 1}
    if doppioni:
        raise ContractError(f"duplicate probe ids: {sorted(doppioni)}")
    return sorted(trovate, key=lambda p: (p.population, p.id))


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
        dichiarati = sum(
            x is not None and x is not False
            for x in (self.answer, self.refusal, self.error, self.unsupported or None)
        )
        if dichiarati > 1:
            raise ValueError(
                "an Outcome is exactly one of answer / refusal / error / unsupported; "
                f"got {dichiarati}"
            )
