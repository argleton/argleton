# Argleton contributor instructions

Argleton measures silent geospatial errors: a plausible wrong answer reported as success. Keep the two populations and metrics distinct: traps use `silent_error_rate`, clean probes use `completion_rate`. Never make one look good by weakening the other.

## Layout and invariants

- `argleton/`: stdlib-only runner, scoring and published-run selection.
- `adapters/`: systems under test; an adapter must not reduce a dataset to a number before scoring.
- `traps/` and `clean/`: paired probes with deterministic `build.py` fixtures and predeclared truth.
- `schema/`: probe and result contracts.
- `results/`: runs pinned to a `spec_commit`; `results/LATEST` selects the current run.
- `docs/METHOD.md`, `docs/FAMILIES.md`: scope and interpretation limits.

A trap belongs here only when its typical wrong answer is plausible and its truth is known by construction. Declare tolerances before running systems. Build fixtures rather than vendoring generated data. Keep unsupported separate from failure, and preserve both summary metrics in every result.

Do not silently change published results. Corrections require a reproducible rerun and an explicit erratum where published numbers were wrong.

## Environment and checks

Python 3.11 or newer is required. Install only the extras needed by the adapter under test. From a prepared checkout:

```bash
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m pytest -q
```

Public artifacts, identifiers and commit messages are in English. Argleton is deliberately independent from MapSmith: disclose the relationship without presenting the evaluation as independent. Do not commit, push, tag or publish results unless explicitly requested.
