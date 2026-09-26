"""The erratum under the results table: derived, and silent when nothing moved.

argleton.org renders a run as published. When a probe's truth is corrected after
the run -- trap 024 on 2026-09-25 -- the page has to say which rows no longer
hold, and it must stop saying so by itself once a run scored against the
corrected truth is published. Both halves are tested here, because a paragraph
that never disappears is as wrong as one that never appears.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _build():
    spec = importlib.util.spec_from_file_location("argleton_site_build", ROOT / "site" / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record(verdicts, traps_run=1, silent=0.0):
    return {
        "system": "a system",
        "silent_error_rate": silent,
        "traps_run": traps_run,
        "completion_rate": 1.0,
        "probes": verdicts,
    }


def test_the_published_run_is_rescored_where_the_truth_moved():
    """The run scored against trap 024's old truth: MapSmith's 0.00 was one
    silent error in thirty-one, and the naive composition's rate one trap high."""
    build = _build()
    _, data = build.latest_run()
    page = build.erratum_html(data)
    if not any(
        v["probe_id"] == "024-pixel-is-point" and v.get("answer") == 412090.0
        for record in data
        for v in build._verdicts(record)
    ):
        # A run scored after the correction: nothing to rescore, nothing shown.
        assert page == ""
        return
    assert "024-pixel-is-point" in page
    assert "0.0323" in page and "0.9032" in page


def test_nothing_is_shown_when_every_answer_agrees_with_the_current_truth():
    build = _build()
    record = _record(
        [{"probe_id": "024-pixel-is-point", "verdict": "correct", "answer": 412105.0}]
    )
    assert build.erratum_html([record]) == ""


def test_a_wrong_pass_and_a_wrong_failure_both_move_the_rate():
    build = _build()
    passed_wrongly = _record(
        [{"probe_id": "024-pixel-is-point", "verdict": "correct", "answer": 412090.0}]
    )
    failed_wrongly = _record(
        [{"probe_id": "024-pixel-is-point", "verdict": "silent_error", "answer": 412105.0}],
        silent=1.0,
    )
    page = build.erratum_html([passed_wrongly])
    assert ">1</td>" in page  # 0 of 1 published, 1 of 1 rescored
    page = build.erratum_html([failed_wrongly])
    assert ">0</td>" in page  # 1 of 1 published, 0 of 1 rescored


def test_a_clean_probe_does_not_move_the_silent_error_rate():
    """The rescored column is silent errors over traps; a clean probe belongs to
    the completion rate, which the table does not show."""
    build = _build()
    record = _record(
        [{"probe_id": "c024-pixel-is-area", "verdict": "correct", "answer": 999.0}]
    )
    assert build.erratum_html([record]) == ""
