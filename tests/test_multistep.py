from __future__ import annotations

from pathlib import Path

import pytest

from argleton.model import load_probe
from argleton.run import load_adapter, run_probe

ROOT = Path(__file__).resolve().parent.parent
IDS = ("034-buffered-well-ids", "c034-buffered-well-ids")


def test_naive_composition_returns_the_predicted_complete_id_list():
    adapter = load_adapter("engine:naive")
    trap = load_probe(ROOT / "traps" / IDS[0])
    _outcome, verdict = run_probe(adapter, trap)
    assert verdict.answer == trap.naive_failure.observed_value
    assert verdict.verdict == "silent_error"


@pytest.mark.parametrize("adapter_name", ["engine:geopandas", "adapters.mapsmith:Adapter"])
@pytest.mark.parametrize("probe_id", IDS)
def test_careful_compositions_execute_the_chain_and_return_exact_ids(adapter_name, probe_id):
    if adapter_name.startswith("engine:"):
        pytest.importorskip("geopandas")
    else:
        pytest.importorskip("mapsmith")
    population = "traps" if probe_id.startswith("0") else "clean"
    probe = load_probe(ROOT / population / probe_id)
    _outcome, verdict = run_probe(load_adapter(adapter_name), probe)
    assert verdict.answer == probe.truth.value
    assert verdict.verdict in ("correct", "correct_with_warning")
