"""The suite's own tests: the probes must honour the contract they publish.

A benchmark that does not check its own fixtures is asking to be trusted, which
is the posture it exists to argue against.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from argleton.model import ContractError, Outcome, Probe, discover, load_probe
from argleton.score import judge, summarise, within_tolerance

ROOT = Path(__file__).resolve().parent.parent
PROBES = discover(ROOT)


def test_there_are_probes():
    assert PROBES, "no probes discovered — the runner would report a vacuous 0.0"


@pytest.mark.parametrize("probe", PROBES, ids=lambda p: p.id)
def test_probe_matches_the_published_schema(probe: Probe):
    """The TOML loader and `schema/probe.schema.json` are the same contract for
    two audiences. When they disagree, the schema is the specification — and a
    contributor validating against it must get the same answer we do."""
    jsonschema = pytest.importorskip("jsonschema")
    import tomllib

    schema = json.loads((ROOT / "schema" / "probe.schema.json").read_text(encoding="utf-8"))
    dati = tomllib.loads((probe.directory / "probe.toml").read_text(encoding="utf-8"))
    jsonschema.validate(dati, schema)


@pytest.mark.parametrize("probe", PROBES, ids=lambda p: p.id)
def test_the_fixtures_are_deterministic(probe: Probe, tmp_path):
    """Built twice, byte for byte the same.

    Every published number is anchored to a `spec_commit`, which is worth
    nothing if the same commit can produce different files."""
    builder = probe.directory / "build.py"
    if not builder.exists():
        pytest.skip("no fixtures")
    impronte = []
    for giro in ("a", "b"):
        fuori = tmp_path / giro
        subprocess.run([sys.executable, str(builder), str(fuori)], check=True, timeout=300)
        impronte.append({
            f.name: f.read_bytes() for f in sorted(fuori.iterdir()) if f.is_file()
        })
    assert impronte[0].keys() == impronte[1].keys()
    for nome in impronte[0]:
        assert impronte[0][nome] == impronte[1][nome], f"{probe.id}: {nome} differs between builds"


@pytest.mark.parametrize("probe", [p for p in PROBES if p.population == "trap"], ids=lambda p: p.id)
def test_a_trap_is_not_trivially_passed(probe: Probe):
    """The naive failure must be OUTSIDE the tolerance.

    Otherwise the trap is scored `correct` no matter what the system does, and
    it silently inflates every result that includes it — a silent error in the
    silent-error suite."""
    assert not within_tolerance(
        probe.naive_failure.observed_value, probe.truth.value, probe.truth.tolerance
    ), f"{probe.id}: the naive failure is within tolerance of the truth"


@pytest.mark.parametrize("probe", PROBES, ids=lambda p: p.id)
def test_every_family_has_a_clean_twin(probe: Probe):
    """A silent-error rate on a family whose task the system cannot perform at
    all measures reach, not silence."""
    famiglie_pulite = {p.family for p in PROBES if p.population == "clean"}
    if probe.population == "trap":
        assert probe.family in famiglie_pulite, (
            f"family '{probe.family}' has traps but no clean control"
        )


def test_a_clean_probe_cannot_carry_a_naive_failure(tmp_path):
    (tmp_path / "probe.toml").write_text(
        'id = "x"\npopulation = "clean"\nfamily = "f"\ntitle = "a title here"\n'
        'surface = ["engine"]\n[task]\ncall = "raster_mean(a.tif)"\n'
        '[truth]\nkind = "scalar"\nvalue = 1\ntolerance = 0\nderivation = "twenty characters"\n'
        '[naive_failure]\ndescription = "d"\nobserved_value = 2\nplausible = true\n'
        'why_plausible = "w"\n[provenance]\nsource = "s"\nfound_by = "f"\ndate = "2026-01-01"\n',
        encoding="utf-8",
    )
    with pytest.raises(ContractError, match="trap filed in the wrong place"):
        load_probe(tmp_path)


def test_an_implausible_trap_is_refused(tmp_path):
    """The admission criterion, enforced rather than documented."""
    (tmp_path / "probe.toml").write_text(
        'id = "x"\npopulation = "trap"\nfamily = "f"\ntitle = "a title here"\n'
        'surface = ["engine"]\n[task]\ncall = "raster_mean(a.tif)"\n'
        '[truth]\nkind = "scalar"\nvalue = 1\ntolerance = 0\nderivation = "twenty characters"\n'
        '[naive_failure]\ndescription = "d"\nobserved_value = 2\nplausible = false\n'
        'why_plausible = "w"\n[refusal]\naccept_if_mentions = ["x"]\n'
        '[provenance]\nsource = "s"\nfound_by = "f"\ndate = "2026-01-01"\n',
        encoding="utf-8",
    )
    with pytest.raises(ContractError, match="plausible = true"):
        load_probe(tmp_path)


def test_refusing_everything_does_not_win():
    """The property the two-number score exists to guarantee.

    A system that refuses every probe gets a perfect silent-error rate. The
    completion rate is what stops that from looking like a good result."""
    verdetti = [judge(p, Outcome(refusal="I am not sure about this file")) for p in PROBES]
    riassunto = summarise(verdetti)
    assert riassunto["silent_error_rate"] == 0.0
    assert riassunto["completion_rate"] == 0.0


def test_an_outcome_cannot_be_two_things_at_once():
    with pytest.raises(ValueError, match="exactly one of"):
        Outcome(answer=1.0, refusal="but also this")


def test_a_published_result_validates_against_its_own_schema(tmp_path):
    """The result format carries a claim, so it has to be enforced.

    `result.schema.json` requires both rates. A system that refuses everything
    scores a perfect silent-error rate and is useless, so a report quoting one
    number without the other is not a valid result — and a schema is the only
    place that rule can live where someone else's tooling will see it.
    """
    jsonschema = pytest.importorskip("jsonschema")

    from argleton.run import main

    fuori = tmp_path / "result.json"
    assert main(["--adapter", "engine:naive", "--root", str(ROOT), "--out", str(fuori)]) == 0
    risultato = json.loads(fuori.read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schema" / "result.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(risultato, schema)

    # The naive composition is not uniformly careless: it passes trap 001,
    # because rasterio undoes the predictor for it. Pinning that is the point —
    # a trap that stops catching it has changed what it measures.
    assert risultato["completion_rate"] == 1.0
    assert risultato["silent_error_rate"] > 0, "the naive adapter fell into no trap at all"
    assert set(risultato["by_family"]) == {p.family for p in PROBES}
