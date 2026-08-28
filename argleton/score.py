"""Turning an outcome into a verdict, and verdicts into the two numbers.

The whole suite exists for one row of the table below: `silent_error` — wrong,
and presented as successful. Every other outcome is something a user, a test or
a log already notices. That is why the headline number counts only that row, and
why it is never published alone.
"""

from __future__ import annotations

import statistics
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
    # Wall clock of the adapter call alone, in milliseconds. Building the
    # fixtures is outside it: that cost is ours and identical for every system,
    # so charging it to the system under test would flatter the fast ones and
    # slander nobody usefully.
    duration_ms: float | None = None
    timings: dict[str, float] | None = None

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
        "timing": _timing(verdicts),
        "verdict_counts": {
            name: sum(v.verdict == name for v in verdicts)
            for name in VERDICTS
            if any(v.verdict == name for v in verdicts)
        },
        "by_family": dict(sorted(per_family.items())),
    }


def _timing(verdicts: list[Verdict]) -> dict[str, Any] | None:
    """Wall clock per probe, reported so it cannot be read as a benchmark.

    Three deliberate choices, each because the obvious alternative misleads.

    **The median, not the mean.** One probe that pays a library's first import
    can be twenty times the others, and a mean over 44 probes carries that cost
    into every comparison as if it recurred.

    **`first_probe_ms` is reported separately**, because that is usually where
    the import went, and a reader who cannot see it cannot subtract it. It is
    the first ATTEMPTED probe, since a skipped one imports nothing.

    **`slowest` names the probe.** A single number invites "system A is slower
    than system B"; a number attached to a probe id invites the useful question,
    which is *what is slow*. The families do not cost the same: a trap over a
    24x24 DEM and a trap over one polygon are not comparable work, and two
    adapters that ran different subsets of the suite did different work
    altogether -- which is why `probes` travels with the numbers.

    This is ONE observation per probe on one machine, not a benchmark: no
    repetition, no warm-up control, no isolation from whatever else the machine
    was doing. It is here to make gross differences visible, and gross means a
    factor of ten.
    """
    # Only the probes the adapter ATTEMPTED. An `unsupported` returns in
    # microseconds because nothing ran, and on an adapter that skips 36 of 44
    # the median over everything comes out 0 ms -- a number that is precisely
    # true and says nothing. Same principle as the silent-error denominator:
    # count what was actually run.
    timed = [
        v for v in verdicts
        if v.duration_ms is not None and v.verdict != "unsupported"
    ]
    if not timed:
        return None
    durations = sorted(v.duration_ms for v in timed)
    worst = max(timed, key=lambda v: v.duration_ms)
    breakdown: dict[str, float] = {}
    for v in timed:
        for name, value in (v.timings or {}).items():
            breakdown[name] = round(breakdown.get(name, 0.0) + value, 1)
    return {
        "probes": len(timed),
        "total_ms": round(sum(durations), 1),
        "median_ms": round(statistics.median(durations), 1),
        "first_probe_ms": round(timed[0].duration_ms, 1),
        "slowest": {"probe_id": worst.probe_id, "ms": round(worst.duration_ms, 1)},
        # Summed adapter-reported breakdown, when the adapter reports one.
        "adapter_breakdown_ms": breakdown or None,
    }
