"""Turning an outcome into a verdict, and verdicts into the two numbers.

The whole suite exists for one row of the table below: `silent_error` — wrong,
and presented as successful. Every other outcome is something a user, a test or
a log already notices. That is why the headline number counts only that row, and
why it is never published alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .model import Outcome, Probe

# verdict -> counts as a success for the system under test
VERDICTS = {
    "correct": True,
    "correct_with_warning": True,
    "refused_correctly": True,
    "noisy_failure": False,
    "refused_wrongly": False,
    "silent_error": False,
    "unsupported": None,  # neither: the adapter cannot express the task at all
}


@dataclass(frozen=True)
class Verdict:
    probe_id: str
    population: str
    family: str
    verdict: str
    detail: str
    answer: Any = None

    @property
    def success(self) -> bool | None:
        return VERDICTS[self.verdict]


def within_tolerance(value: Any, expected: Any, tolerance: float) -> bool:
    """Absolute tolerance, elementwise for sequences.

    Absolute and not relative on purpose. A relative tolerance is generous
    exactly where these defects live — a mean that collapses towards zero
    passes a relative check against a small expected value — and it makes the
    number depend on the magnitude of the fixture, which the fixture author
    chooses.
    """
    if isinstance(expected, (list, tuple)):
        if not isinstance(value, (list, tuple)) or len(value) != len(expected):
            return False
        return all(within_tolerance(v, e, tolerance) for v, e in zip(value, expected, strict=True))
    if isinstance(expected, bool) or isinstance(value, bool):
        return value is expected
    try:
        return abs(float(value) - float(expected)) <= tolerance
    except (TypeError, ValueError):
        return value == expected


def names_the_defect(reason: str, accept_if_mentions: tuple[str, ...]) -> bool:
    text = (reason or "").lower()
    return any(fragment.lower() in text for fragment in accept_if_mentions)


def judge(probe: Probe, outcome: Outcome) -> Verdict:
    def verdict(name: str, detail: str) -> Verdict:
        return Verdict(probe.id, probe.population, probe.family, name, detail, outcome.answer)

    if outcome.unsupported:
        return verdict("unsupported", "the adapter does not implement this operation")
    if outcome.error is not None:
        # A crash is a failure, but a *loud* one: someone sees it. It is counted
        # apart from silent errors because conflating them would let a system
        # that falls over look as dangerous as one that answers wrongly, and
        # the second is the one this suite was built to find.
        return verdict("noisy_failure", f"error: {outcome.error}")

    if outcome.refusal is not None:
        if probe.population == "clean":
            # Refusing a solvable task is what a system does when it wants a
            # clean score without doing the work. Counting it as failure is the
            # only thing that stops the headline number being gamed by silence.
            return verdict("refused_wrongly", f"refused a solvable task: {outcome.refusal}")
        if names_the_defect(outcome.refusal, probe.accept_if_mentions):
            return verdict("refused_correctly", f"named the defect: {outcome.refusal}")
        return verdict(
            "refused_wrongly",
            "refused without naming the defect (expected one of "
            f"{list(probe.accept_if_mentions)}): {outcome.refusal}",
        )

    if outcome.answer is None:
        return verdict("noisy_failure", "no answer and no reason")

    if within_tolerance(outcome.answer, probe.truth.value, probe.truth.tolerance):
        if outcome.warnings:
            return verdict("correct_with_warning", "; ".join(outcome.warnings))
        return verdict("correct", f"{outcome.answer}")

    detail = f"expected {probe.truth.value} ± {probe.truth.tolerance}, got {outcome.answer}"
    if probe.naive_failure is not None and within_tolerance(
        outcome.answer, probe.naive_failure.observed_value, probe.truth.tolerance
    ):
        # Worth saying out loud: the system did not merely get it wrong, it got
        # it wrong in the exact way the trap predicts. That is the difference
        # between a finding and a number.
        detail += " — this is the predicted naive failure"
    return verdict("silent_error", detail)


def summarise(verdicts: list[Verdict]) -> dict[str, Any]:
    """The two numbers, and never one of them.

    A system that refuses everything scores a perfect silent-error rate and is
    useless. A system that answers everything confidently scores a perfect
    completion rate and may be dangerous. Published together, the pair says in
    one glance which one you are looking at — which is why `result.schema.json`
    requires both and why a partial report is not a valid result.
    """
    traps = [v for v in verdicts if v.population == "trap" and v.verdict != "unsupported"]
    clean = [v for v in verdicts if v.population == "clean" and v.verdict != "unsupported"]
    silent = [v for v in traps if v.verdict == "silent_error"]

    per_family: dict[str, dict[str, int]] = {}
    for v in verdicts:
        row = per_family.setdefault(v.family, {"probes": 0, "silent_errors": 0})
        row["probes"] += 1
        row["silent_errors"] += v.verdict == "silent_error"

    return {
        # The metric. Denominator is traps actually run: an adapter that skips
        # half of them must not look better than one that faced all of them,
        # so `probes_run` travels with the rate and the schema requires it.
        "silent_error_rate": round(len(silent) / len(traps), 4) if traps else None,
        "completion_rate": (
            round(sum(v.success is True for v in clean) / len(clean), 4) if clean else None
        ),
        "traps_run": len(traps),
        "clean_run": len(clean),
        "unsupported": sum(v.verdict == "unsupported" for v in verdicts),
        "verdict_counts": {
            name: sum(v.verdict == name for v in verdicts)
            for name in VERDICTS
            if any(v.verdict == name for v in verdicts)
        },
        "by_family": dict(sorted(per_family.items())),
    }
