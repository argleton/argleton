# Argleton

**A correctness suite for geospatial systems.** Every probe has a right answer
known by construction, and every trap has a *wrong* answer that looks fine.

That second half is the whole point. Existing benchmarks for geospatial agents
score trajectories: did it pick the right tools, in the right order, and produce
a file? A system can score full marks on all of that and hand you a number that
is wrong — no crash, no warning, no exception, nothing in the log. Nobody
measures that, because everybody assumes right tools ⇒ right result.

## The failure this measures

Trap 001 is a valid GeoTIFF. Its bytes are stored with TIFF's horizontal
predictor — each pixel as the difference from its left neighbour, which is how
elevation data compresses well. Undoing that on read is the reader's job.

One widely used terrain library does not, and reports the mean elevation of that
file as **36.09 m** where the answer is **1093.0 m**. Both numbers are perfectly
ordinary elevations. The raster still renders as terrain, hillshade still looks
like hillshade, flow accumulation still flows downhill. Nothing anywhere says
anything is wrong.

```
$ argleton --adapter engine:rasterio
ok   clean c001-raster-mean          correct   1093.0
ok   clean c003-raster-mean-nodata   correct   1000.0
ok   trap  001-tiff-predictor        correct   1093.0
ok   trap  003-nodata-in-statistics  correct   1000.0
silent_error_rate 0.0 over 2 traps  |  completion_rate 1.0 over 2 clean

$ argleton --adapter engine:whitebox
ok   clean c001-raster-mean          correct        1093.0
FAIL trap  001-tiff-predictor        silent_error   expected 1093.0 ± 0.001, got 36.09375
silent_error_rate 1.0 over 1 traps  |  completion_rate 1.0 over 1 clean
```

The two lines say different things and both matter: this engine can do the task
(completion 1.0) *and* gets this file silently wrong (silent error 1.0).

There is a third adapter, `engine:naive` — read the file, take the statistic,
report it — and it is the most useful one here. It scores **0.667 / 1.0**: it
answers every clean probe correctly, falls into two traps, and **passes the
third**, because rasterio undoes the predictor on its behalf. Careless code is
not uniformly wrong. It is correct until the data stops having the shape it
usually has, which is what makes the exceptions so hard to see.

## Two numbers, never one

| population | what is in it | refusing is… |
|---|---|---|
| `traps/` | a planted defect; the typical wrong answer is **plausible** | correct, if it names the real defect |
| `clean/` | ordinary, solvable, nothing planted | a **failure** |

- **`silent_error_rate`** — over the traps. The metric. Should be ~0.
- **`completion_rate`** — over the clean probes. Should be high.

Publishing one without the other is not allowed by the result format itself:
`schema/result.schema.json` requires both. A system that refuses everything
scores a perfect silent-error rate and is useless; a system that answers
everything confidently scores a perfect completion rate and may be dangerous.
Side by side, one glance tells you which you are looking at.

## What is covered

Three families of twelve, and [FAMILIES.md](docs/FAMILIES.md) says which — so a
number from here can never be read as broader than it is. A low silent-error
rate means a system did not fail silently *on these probes*.

| family | the wrong answer | why it survives |
|---|---|---|
| `raster-encoding` | mean 36.09 instead of 1093.0 | the differenced grid still renders as terrain |
| `linear-units` | 100 ha instead of 9.29 ha | both are ordinary parcels; they differ by 3.28² |
| `nodata` | mean 945.005 instead of 1000.0 | 5.5% out — too small to question, too large to ignore |

## The admission criterion

A trap is admitted only if it declares `plausible = true` and argues for it in
`why_plausible`. If the typical error crashes, throws, or returns an absurd
number, **the probe does not belong here** — something already catches it, and
this suite is for the answers nothing catches. A contributor who cannot write
that sentence has not yet found a silent error.

Every trap also cites a real bug, paper, or reproduction in `provenance.source`.
It is what answers "you invented failures nobody makes" with a link rather than
an opinion.

## Pre-registration you can check instead of believe

Tolerances are declared before any result exists. `traps/`, `clean/`, `schema/`
and `docs/METHOD.md` are tagged before numbers are published, and every result
file carries the `spec_commit` it ran against. Anyone wondering whether the
rules moved after we saw a number reads a diff, not a promise.

Fixtures are **built, not vendored**: `build.py` in each probe regenerates them
deterministically. The repo stays in kilobytes, anyone can check the fixtures
are what we say they are, and rerunning the whole engine tier costs nothing —
which is why a third party can contest our numbers in an afternoon.

## Two tiers

**Engine** — the adapter calls a library directly. Deterministic, free, runs in
CI on every commit. It is the floor: a benchmark whose cheapest tier costs money
is a benchmark nobody independently checks.

**Agent** — the task goes to an agentic system in natural language. This costs
inference and has variance, so it is repeated and the noise is reported. Never a
single run.

## Writing an adapter

Half a day, on purpose.

```python
class Adapter:
    name = "your-system"

    def run(self, probe, workdir) -> Outcome:
        # exactly one of: answer / refusal / error / unsupported
        ...
```

`unsupported` is not a failure. Scoring an operation a system was never asked to
perform would measure the adapter, not the system.

Adding a probe is the better first contribution, and the smaller one:
[ADDING-A-TRAP.md](docs/ADDING-A-TRAP.md). Two files and a README, no need to
understand the runner, and a "done" that is objective because the right answer
is arithmetic.

## Who wrote this, and why that is stated here

Argleton was started by the authors of [MapSmith](https://github.com/mapsmith-ai/MapSmith),
which is one of the systems it measures. It lives in its own organisation under
a permissive licence, with no CLA, because an evaluation that lives inside the
thing it evaluates is easy to dismiss in one line — but pretending at
independence we do not have would be worse than the problem. The defence is not
the org chart: it is that every fixture is regenerable, every tolerance is in
git history, and the first published result includes MapSmith with its own
verification switched off.

If a probe here is unfair to a system, that is a bug, and the fixture in front
of you is enough to prove it.

## The name

Argleton was a village Google Maps showed for two years near Aughton, in
Lancashire. It was an empty field. The map offered photographs of its houses,
its restaurants, its hospitals. Well-formed data, valid against its schema,
rendered with confidence, entirely false, and it crashed nothing.

## Licence

Apache-2.0. Use it, fork it, run it against us.
