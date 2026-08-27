# Argleton

**A correctness suite for geospatial systems.** Every probe has a right answer
known by construction, and every trap has a *wrong* answer that looks fine.

**[argleton.org](https://argleton.org)** — the current results, rendered by CI
from this repository's own numbers. Nothing on that page is typed in by hand.

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

Seeing it needs one install — every fixture is rebuilt deterministically on your
machine, so there is nothing to download and nothing to take on trust:

```
pip install "argleton[fixtures]"
```

The probes ship with the runner, so that is the whole setup. To read them, change
them, or add one, take the checkout instead — the probes are the point of the
repository and `probe.toml` is meant to be read:

```
git clone https://github.com/argleton/argleton
cd argleton
pip install -e ".[fixtures]"
```

```
$ argleton --adapter engine:rasterio
ok   clean c001-raster-mean               correct   1093.0
ok   clean c003-raster-mean-nodata        correct   1000.0
ok   clean c009-native-resolution-classes correct   900.0
ok   clean c010-physical-values           correct   0.5
ok   trap  001-tiff-predictor             correct   1093.0
ok   trap  003-nodata-in-statistics       correct   1000.0
ok   trap  009-resampled-classes          correct   0.0
ok   trap  010-scale-offset               correct   0.3333333333333334
silent_error_rate 0.0 over 4 traps  |  completion_rate 1.0 over 4 clean

$ argleton --adapter engine:whitebox
ok   clean c001-raster-mean          correct        1093.0
ok   clean c003-raster-mean-nodata   correct        1000.0
FAIL trap  001-tiff-predictor        silent_error   expected 1093.0 ± 0.001, got 36.09375
ok   trap  003-nodata-in-statistics  correct        1000.0
silent_error_rate 0.5 over 2 traps  |  completion_rate 1.0 over 2 clean
```

(`skip … unsupported` lines trimmed: the vector probes are outside what these
two raster engines can be asked, and skipping them is not a failure.)

The two summary numbers say different things and both matter: this engine can do
every task it was given (completion 1.0) *and* gets this file silently wrong
(the 0.5).

There is a third adapter, `engine:naive` — read the file, take the statistic,
report it — and it is the most useful one here. It scores **0.9524 / 1.0**: it
answers every clean probe correctly, falls into twenty of the twenty-one traps, and
**passes the remaining one**, because rasterio undoes the predictor on its
behalf. Careless code is not uniformly wrong. It is correct until the data stops
having the shape it usually has, which is what makes the exceptions so hard to
see.

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

Nineteen families of twenty-four, and [FAMILIES.md](docs/FAMILIES.md) says which — so a
number from here can never be read as broader than it is. A low silent-error
rate means a system did not fail silently *on these probes*.

| family | the wrong answer | why it survives |
|---|---|---|
| `raster-encoding` | mean 36.09 instead of 1093.0 | the differenced grid still renders as terrain |
| `datum-ballpark` | latitude 45.5 instead of 45.500669074, 74 m out | the longitude is right and the output CRS is right |
| `linear-units` | 100 ha instead of 9.29 ha | both are ordinary parcels; they differ by 3.28² |
| `nodata` | mean 945.005 instead of 1000.0 | 5.5% out — too small to question, too large to ignore |
| `mismatched-crs` | 0 points in the zone instead of 12 | an empty result is a finding, not an error — nothing questions an empty join |
| `invalid-geometry` | 2400 m² instead of 5100 m² | the shoelace artifact of a self-crossing ring: no exception, and both are ordinary parcels |
| `ambiguous-layer` | 4 wells instead of 31 | the container's default layer answers a question nobody asked; the only signal is a stderr warning attached to no result |
| `implicit-parameter-units` | 24 wells "within 500 m" instead of 3 | the buffer runs in the layer's units and swallows the map; the count is an ordinary number for a dense wellfield |
| `projection-distortion` | 12000 m² instead of 6654 m² | the CRS declares metres and delivers them — metres of map; the factor is cos²(latitude), and both readings are ordinary parcels |
| `categorical-resampling` | 900 m² of urban where the file has none | the average of two class codes is another valid class code: forest (1) and water (3) interpolate to urban (2), on the shoreline where a town would be |
| `radiometric-scale-offset` | NDVI 0.25 instead of 0.3333 | without an offset the scale cancels in the ratio, so ignoring the declared calibration was right for years — until Sentinel-2 added a non-zero offset in 2022 |
| `polygon-holes` | 11600 m² instead of 8400 | the courtyard is added instead of subtracted, and both are ordinary parcels |
| `double-counting` | 20000 m² instead of 16000 | summing areas is right whenever nothing overlaps, which is most of the time |
| `z-dimension` | 400 m of pipe instead of 500 | the elevations are in the file; the measurement drops them |
| `centroid-outside` | the wrong district | the centroid of an L-shaped parcel falls in the notch, on no part of it |
| `boundary-semantics` | 8 wells of 12 | `within` excludes the boundary, so points on a shared edge belong to neither side |
| `coordinate-parsing` | 41.5324 instead of 41.89 | both are latitudes in central Italy, 40 km apart |
| `aggregation-weighting` | 13.67% instead of 1.38% | averaging rates treats a village as equal to a city |
| `tabular-join` | 62000 people instead of 100000 | a CSV reader turns "001" into 1 and four municipalities leave the join |

## Results

Engine tier, nineteen families, `spec_commit` pinned — [every run, and what the
numbers do not say](results/).

| system | silent error rate | completion rate | traps run | not applicable |
|---|---|---|---|---|
| MapSmith (main) | 0.00 | 1.00 | 21 | 0 |
| rasterio 1.5.1 (careful composition) | 0.00 | 1.00 | 4 | 34 |
| GeoPandas 1.1 + Shapely 2 (careful composition) | 0.00 | 1.00 | 7 | 28 |
| whitebox-workflows 2.0.6 | 0.50 | 1.00 | 2 | 38 |
| naive composition | 0.9524 | 1.00 | 21 | 0 |

The last two columns are not decoration. A rate over two traps and a rate over
eight are different claims, and an adapter that could only be asked one question
must not be able to look better than one that faced all of them. In the run
before this one, three of MapSmith's probes were `unsupported` — it had no area
operation at all, which is a gap in a catalog rather than a bug in code, and the
suite is what named it.

Three findings frame everything here, one per run. From the first run:
**MapSmith scored 0.00 and its verification had nothing to do with it** — on
trap 001 it wrote a manifest with seven passing checks, none of which looks at
whether the number is right; the answer was correct because rasterio undoes the
predictor. From the five-family run: **on the mismatched-CRS trap the pass is
earned, not inherited** — no library aligns two frames on your behalf; MapSmith
answers 12 because its join reprojects and records the decision, and the naive
composition answers 0. And from the six-family run: **the suite caught its
author** — MapSmith's reader resolves a multi-layer container to its default
layer silently, answered 4 where the truth is 31, and the failure was
[filed against MapSmith](https://github.com/mapsmith-ai/MapSmith/issues/29)
before the trap was published, with the fix landing after this run rather than
before it. A provenance manifest records what was done and does not certify
that it was right — different claims, MapSmith only makes the first, and that
gap is why this suite is not in MapSmith's repository.

And from the eight-family run: **the suite wrote its author's roadmap.** Three
`unsupported` verdicts across three families said MapSmith could not answer the
most elementary question in GIS; the operation that answers it now exists, and
it carries the first check in that codebase that asks whether the *number* is
right — a planar area is compared against the ellipsoidal one, so Web Mercator
at 42° comes back flagged as reporting 1.80× the land it covers.

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
git history, and every headline finding in [results](results/) so far has cost
MapSmith something — a 0.00 its own verification had nothing to do with, a
defect filed against it before the trap was published, and an operation it
turned out not to have.

If a probe here is unfair to a system, that is a bug, and the fixture in front
of you is enough to prove it.

## The name

Argleton was a village Google Maps showed for two years near Aughton, in
Lancashire. It was an empty field. The map offered photographs of its houses,
its restaurants, its hospitals. Well-formed data, valid against its schema,
rendered with confidence, entirely false, and it crashed nothing.

## Licence

Apache-2.0. Use it, fork it, run it against us.
