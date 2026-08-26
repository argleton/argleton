# Results

Every file here names the `spec_commit` it ran against. That is the
pre-registration: whether a tolerance or a task moved after a number was seen is
answered by a diff, not by our word.

`LATEST` names the published run — the one [argleton.org](https://argleton.org)
renders. Each section below links the directory its numbers come from, one JSON
record per system, with a per-probe verdict and a `by_family` breakdown so one
family with several probes cannot read as several independent findings.

## What these numbers do not say

This section is at the top rather than the bottom on purpose, and it grows with
the suite. Nineteen families of twenty-four are implemented
([FAMILIES.md](../docs/FAMILIES.md)).

- **A 0.00 means a system did not fail silently *on these probes*.** Not that it
  is correct, not that it is safe, and not that it would survive the five
  families that are named and not yet built — nor the thirty further
  mechanisms a survey of the literature turned up while this run was being
  made.
- **Read "not applicable" before the rate.** A rate over two traps and a rate
  over twenty are different claims. An adapter that can only be asked two
  questions must not be able to look better than one that faced all of them.
- **One family can still move any of these rates a long way**, because most of
  them carry one trap each — treat a difference of one probe as one probe. Treat a difference of one probe as one
  probe.
- **Engine tier only.** Every number here comes from an adapter calling a
  library directly. Nothing on this page measures an agent, and the agent tier
  will be reported with its variance rather than as a single run.
- **These are not verdicts on libraries.** whitebox-workflows fails one trap
  because of [one open upstream defect](https://github.com/jblindsay/whitebox_next_gen/issues/32)
  we reported; everything else here is a library behaving exactly as documented.

Nobody is notified before publication as long as nothing here is a new claim
about a third party: the Whitebox defect was reported upstream first, and the
rest is documented behaviour. That changes the moment a result says something a
maintainer has not already been told.

## 2026-08-26 (evening) — nineteen families, and MapSmith stops being 0.00

Published run: [`2026-08-26-nineteen-families/`](2026-08-26-nineteen-families/).
Engine tier, `spec_commit` [`461ef15`](../../../commit/461ef15), nineteen families:
one new one, `datum-ballpark`, joins the eighteen below.

| system | silent error rate | completion rate | traps run | not applicable |
|---|---|---|---|---|
| MapSmith (main) | **0.0476** | 1.00 | 21 | 0 |
| rasterio 1.5.1 | 0.00 | 1.00 | 4 | 34 |
| GeoPandas 1.1 + Shapely 2 | **0.1429** | 1.00 | 7 | 28 |
| whitebox-workflows 2.0.6 | 0.50 | 1.00 | 2 | 38 |
| naive composition | 0.9524 | 1.00 | 21 | 0 |

**MapSmith's 0.00 ended here, and on the first family that asked a question the
previous twenty did not.** The trap is
[021](../traps/021-ballpark-datum/): a station stored on Monte Mario with the Rome
prime meridian, asked for its WGS 84 latitude.
`Transformer.from_crs(CRS(4806), CRS(4326))` — the one line every caller writes,
and the line under MapSmith's `reproject_layer` — selects a **ballpark**
transformation. A ballpark is PROJ declaring that it will treat the two datums as
equivalent: no shift is applied, the Rome meridian is still handled correctly so
the longitude looks right, and the latitude comes back exactly as it went in.
74.4 m out, accuracy reported as `-1`, nothing raised and nothing logged.

MapSmith's manifest for that run records a **successful** reprojection, and it is
not lying: `crs_matches` passes, because the output CRS really is EPSG:4326.
Seven green checks beside a number 74 m wrong — which is word for word the
finding this suite made about MapSmith on 2026-08-23, on a different operation.
A manifest records what was done; it does not certify that it was right.

**The clean twin is what makes the trap arguable.** `c021` is the same physical
point, the same datum and the same truth, declared as EPSG:4265 instead of 4806.
There PROJ selects a 4 m operation and lands on the truth to 0.000 m. So the
answer to this trap cannot be *datum transformations are hard*: difficulty is not
the variable, the declared variant is.

**Nothing passes this trap yet**, and that is worth saying plainly rather than
leaving to a reader to notice. GeoPandas falls in too: `to_crs` is one line and it
hands the pair to the same `Transformer.from_crs`, which is also the line under
MapSmith's `reproject_layer`. All three failures are the same failure, reached
three ways.

What it takes to pass is a **computation**, not a declaration: read
`get_last_used_operation().accuracy`, and if it is negative take the first
`TransformerGroup` operation that states one. Fourteen lines, no manifest and no
provenance format — which is the property that keeps this trap from being a
benchmark for the product the suite was built beside. It is stated in the trap's
README as the specification of a fix, and deliberately not scored under any
library's name: an earlier version of this run did exactly that, and told a
reader GeoPandas handles a case it does not.

## 2026-08-26 (tier A) — eighteen families, and two that are not geometry at all

Published run: [`2026-08-26-eighteen-families/`](2026-08-26-eighteen-families/).
Engine tier, `spec_commit` [`cadf41b`](../../../commit/cadf41b), eighteen families:
eight new ones join the ten below.

| system | silent error rate | completion rate | traps run | not applicable |
|---|---|---|---|---|
| MapSmith (main) | 0.00 | 1.00 | 20 | 0 |
| rasterio 1.5.1 | 0.00 | 1.00 | 4 | 32 |
| GeoPandas 1.1 + Shapely 2 | 0.00 | 1.00 | 6 | 28 |
| whitebox-workflows 2.0.6 | 0.50 | 1.00 | 2 | 36 |
| naive composition | 0.95 | 1.00 | 20 | 0 |

**The eight new families are the ones whose truth is arithmetic**, selected from a
survey of forty-seven documented mechanisms because their fixtures are small enough
to derive on paper: a courtyard subtracted rather than added, overlapping concessions
united rather than summed, a pipe measured through space rather than in plan view, a
parcel located by a point in its own notch, wells on a shared edge belonging to
neither district, degrees-minutes-seconds read as a decimal, unemployment rates
averaged as though the towns were the same size, and a leading zero thrown away by a
CSV reader.

**Two of them are not geometric at all** — `aggregation-weighting` and `tabular-join`
— and that is deliberate. An agent joins attribute tables and aggregates columns far
more often than it reprojects, and no suite was measuring that. They are also the
cheapest fixtures in the whole set, which says something about why the gap existed.

**Verifying the survey's numbers before building changed three of them.** The
partial-overlap band touched four parcels instead of three, because the fourth
started exactly where the band ended and `intersects` counts a zero-area contact —
which is a different family, so the fixture moved rather than the derivation. The
join fixture's populations did not add up to a round total. And the ring-orientation
candidate turned out not to be reproducible with Shapely at all, which ignores
winding order: it is documented as planned rather than quietly built against an
engine that cannot fail it.

**MapSmith answered five of the ten new traps with `unsupported` on the first run**,
and the operations that close them exist now — a length that counts the third
dimension, a join that reads keys as text and measures its own fan-out, a weighted
aggregate, a coordinate parser, and a representative point that is verified to lie on
its feature. Fifth time this suite has written its author's roadmap.

**And trap 011 found a defect in code that had shipped the day before.** MapSmith's
geodesic area took `abs()` of the whole geometry, so a courtyard was added on the
ellipsoid while the planar path subtracted it — 11609 against 8400. What noticed was
the distortion check comparing the two paths, which is a second-order reason for
having it. Fixed before this run, which is why the row above says 0.00.

## 2026-08-26 (later) — ten families, and the archive's own calibration

Published run: [`2026-08-26-ten-families/`](2026-08-26-ten-families/).
Engine tier, `spec_commit` [`d97d2ae`](../../../commit/d97d2ae), ten families:
`radiometric-scale-offset` (010) joins the nine below.

| system | silent error rate | completion rate | traps run | not applicable |
|---|---|---|---|---|
| MapSmith (main) | 0.00 | 1.00 | 10 | 0 |
| rasterio 1.5.1 | 0.00 | 1.00 | 4 | 12 |
| GeoPandas 1.1 + Shapely 2 | 0.00 | 1.00 | 6 | 8 |
| whitebox-workflows 2.0.6 | 0.50 | 1.00 | 2 | 16 |
| naive composition | 0.90 | 1.00 | 10 | 0 |

**The new family is about a conversion the file asks for and nobody performs.**
A scene declares scale 0.0001 and offset −0.1, so its stored 3000 and 5000 are
reflectances of 0.2 and 0.4 and NDVI is exactly one third. Read the bands and
apply the formula and the answer is 0.25 — GDAL's documentation states that
applying scale and offset is the caller's responsibility and that `RasterIO`
does not do it.

**Why careful people have this one.** Without an offset, NDVI is invariant to
the scale factor: it cancels in the ratio. Dividing digital numbers by 10000,
or skipping the conversion entirely, gave the right answer for years — until
ESA introduced a non-zero `BOA_ADD_OFFSET` with Sentinel-2 baseline 04.00 on
25 January 2022. The invariance stopped holding, on unchanged code, for scenes
acquired after that date and not before.

**MapSmith returned `unsupported` the first time this trap ran**: it had no
band arithmetic at all. That is the fourth gap this suite has named in its own
author's catalogue rather than in someone else's code, and the pattern is now
the normal way this repository sets MapSmith's roadmap.

## 2026-08-26 — nine families, and a class that was never there

Published run: [`2026-08-26-nine-families/`](2026-08-26-nine-families/).
Engine tier, `spec_commit` [`cfb2919`](../../../commit/cfb2919), nine families:
`categorical-resampling` (009) joins the eight below.

| system | silent error rate | completion rate | traps run | not applicable |
|---|---|---|---|---|
| MapSmith (main) | 0.00 | 1.00 | 9 | 0 |
| rasterio 1.5.1 | 0.00 | 1.00 | 3 | 12 |
| GeoPandas 1.1 + Shapely 2 | 0.00 | 1.00 | 6 | 6 |
| whitebox-workflows 2.0.6 | 0.50 | 1.00 | 2 | 14 |
| naive composition | 0.8889 | 1.00 | 9 | 0 |

**The new family measures an alphabet, not a quantity.** A land-cover file holds
the codes 1 (forest) and 3 (water); the legend also defines 2 (urban), which no
cell carries. Asked for the urban area on a 15 m grid — the ordinary reason
anyone resamples — the correct answer is zero at any resolution, because a rule
that is valid for labels selects an existing label and cannot mint a new one.
Interpolate instead and the forest/water boundary averages to 2: four cells,
900 m² of urban on a shoreline, where a town would plausibly be. rasterio's
bilinear, cubic and average all do it; nearest and mode do not.

**What makes it admissible is that nothing can tell the difference for you.**
Nothing in a GeoTIFF says whether it holds measurements or labels, so no library
can warn: rasterio's documentation recommends bilinear and cubic for
"continuous data" and carries no categorical-data warning anywhere. The rule is
in every vendor's manual and enforced by none of them.

**MapSmith's pass is earned narrowly, and the narrow part is the point.** Its
resampling operation has no default method, so the composition had to state one,
and a caller who was told the legend states a categorical one. Had it said
bilinear anyway, the result would have carried `invented_values: [2.0]` and a
failed non-critical check named `no_invented_class_codes`. Two defences: the
question is asked, and the answer is checked against the input's own alphabet
afterwards. Neither is the manifest — a manifest records what was done, and this
is about what came back.

## 2026-08-25 (later) — eight families, and the suite writes its author's roadmap

Published run: [`2026-08-25-eight-families/`](2026-08-25-eight-families/).
Engine tier, `spec_commit` [`bc95d3b`](../../../commit/bc95d3b), eight families:
`projection-distortion` (008) joins the seven below.

| system | silent error rate | completion rate | traps run | not applicable |
|---|---|---|---|---|
| MapSmith (main @ 40bddcb) | **0.00** | 1.00 | 8 | 0 |
| rasterio 1.5.1 | **0.00** | 1.00 | 2 | 12 |
| GeoPandas 1.1 + Shapely 2 | **0.00** | 1.00 | 6 | 4 |
| whitebox-workflows 2.0.6 | **0.50** | 1.00 | 2 | 12 |
| naive composition | **0.875** | 1.00 | 8 | 0 |

**Read the "not applicable" column before the rate.** In the run above, three
of MapSmith's eight probes came back `unsupported`, across three families —
because MapSmith had **no area operation at all**, and area is the most
elementary question in GIS. Composing one out of raw SQL would have measured
DuckDB, so the adapter said so instead, three times. That is what a suite is
for: the gap was in our catalog and the number named it.

The operation exists now (`measure_area`), and this run is the first where
MapSmith answers every probe. Two of the four passes it earned today are worth
separating from the two it inherited:

- **002, feet-as-metres — earned.** The linear unit is read off the CRS and
  applied once: 10⁶ square US survey feet is 92903.41 m², never 10⁶.
- **005, bowtie — earned, and reported.** The invalid ring is repaired *before*
  the measurement, and the repair lands in the manifest's `repairs` and in the
  tool result. The planar area of a self-crossing ring is the signed shoelace:
  2400 for a 5100 m² parcel, returned without complaint by everything that does
  not look.
- **008, Web Mercator — earned by default, not by care.** Ground area is
  geodesic unless asked otherwise, so the map plane never enters. Ask for the
  planar area of the same parcel and MapSmith answers 12000 — and attaches the
  ratio 1.8038 against the ellipsoidal area as a non-critical check. That is
  the first check in the codebase that asks whether the *number* is right
  rather than whether the operation ran, which is exactly the criticism this
  suite levelled at MapSmith's seven green checks on 2026-08-23.
- **001, TIFF predictor — still inherited.** rasterio undoes the predictor;
  MapSmith's checks would pass either way. Unchanged since the first run, and
  still the honest reading.

The naive composition is now at 0.875 — seven traps of eight, saved only by
rasterio on the predictor.

## 2026-08-25 — six families, and the suite catches its author

Superseded run: [`2026-08-25-six-families/`](2026-08-25-six-families/).
Engine tier, `spec_commit` [`06d4e66`](../../../commit/06d4e66), six families:
`ambiguous-layer` (006) joins the five below.

| system | silent error rate | completion rate | traps run | not applicable |
|---|---|---|---|---|
| MapSmith 0.2.2 (main @ d681b54) | **0.25** | 1.00 | 4 | 4 |
| rasterio 1.5.1 | **0.00** | 1.00 | 2 | 8 |
| GeoPandas 1.1 + Shapely 2 | **0.00** | 1.00 | 4 | 4 |
| whitebox-workflows 2.0.6 | **0.50** | 1.00 | 2 | 8 |
| naive composition | **0.8333** | 1.00 | 6 | 0 |

**MapSmith's 0.00 is gone, and we took it away ourselves.** Trap 006 hands
every reader a two-layer container and asks about the layer by name. MapSmith's
reader resolves to the container's default layer **silently** — quieter than
the bare pyogrio call it wraps, which at least warns on stderr — so its
inspection tool answered 4 where the truth is 31, with no warning field and,
per [issue #29](https://github.com/mapsmith-ai/MapSmith/issues/29), no record
in the manifest of which layer was read. The issue was filed before the trap
was published, and the fix lands after this run — in that order on purpose: a
suite that publishes its author's failures only once they are fixed is an
advertisement, not a measurement.

The rest moves as the families predict: the careful GeoPandas composition
passes everything it can be asked (repairing the bowtie **and saying so**),
and the naive composition now stands at 0.83 — five traps of six, still saved
on the predictor by rasterio.

## 2026-08-24 — five families

Superseded run: [`2026-08-24-five-families/`](2026-08-24-five-families/).
Engine tier, `spec_commit` [`7856f88`](../../../commit/7856f88), five families:
the three below plus `mismatched-crs` (004) and `invalid-geometry` (005), both
added since the first run.

| system | silent error rate | completion rate | traps run | not applicable |
|---|---|---|---|---|
| MapSmith 0.2.2 (main @ d681b54) | **0.00** | 1.00 | 3 | 4 |
| rasterio 1.5.1 | **0.00** | 1.00 | 2 | 6 |
| GeoPandas 1.1 + Shapely 2 | **0.00** | 1.00 | 3 | 4 |
| whitebox-workflows 2.0.6 | **0.50** | 1.00 | 2 | 6 |
| naive composition | **0.80** | 1.00 | 5 | 0 |

The first run's finding was that MapSmith's 0.00 was inherited from its
engines, not earned by its checks. The counterpoint arrived with family 4:
**on the mismatched-CRS trap the pass is earned.** There is no library that
aligns two coordinate frames on your behalf — the naive composition answers 0
("no points in the zone", a finding-shaped wrong answer) with no exception and
no warning, while MapSmith answers 12 because its join reprojects and records
the decision in `crs_decisions`. First family where the discipline, not the
dependency, produces the number.

Family 5 adds the other side of the careful/careless line: the careful
GeoPandas adapter repairs the self-intersecting ring with `make_valid` **and
says so**, scoring `correct_with_warning` — the verdict that exists to reward
communication. The naive composition reports the shoelace artifact (2400 m²
for a 5100 m² parcel), which matches no definition of a region at all.

MapSmith's own area operation does not exist, so families 3 and 5 were never
put to it ("not applicable" is not a pass). The naive composition now stands
at 0.80: four traps out of five, still saved on trap 001 by rasterio undoing
the predictor on its behalf.

## 2026-08-23 — first run

Superseded run: [`2026-08-23-first-run/`](2026-08-23-first-run/).
Engine tier, `spec_commit` [`1584e5d`](../../../commit/1584e5d), three families.

| system | silent error rate | completion rate | traps run | not applicable |
|---|---|---|---|---|
| MapSmith 0.2.2 | **0.00** | 1.00 | 2 | 2 |
| rasterio 1.5.1 | **0.00** | 1.00 | 2 | 2 |
| GeoPandas 1.1 + Shapely 2 | **0.00** | 1.00 | 1 | 4 |
| whitebox-workflows 2.0.6 | **0.50** | 1.00 | 2 | 2 |
| naive composition | **0.67** | 1.00 | 3 | 0 |

Read the second column with the first. Every system here has a completion rate
of 1.00 — each can do the task it was given. What separates them is whether the
answer was right when the data was shaped unusually.

### The finding that matters, and it is about us

**MapSmith scores 0.00, and its verification had nothing to do with it.**

On trap 001 MapSmith wrote a manifest with seven checks. All seven passed:

```
input_crs_present    'zones_path': EPSG:32632
input_not_empty      'zones_path': 1 features
crs_present          EPSG:32632
crs_matches          expected EPSG:32632, got EPSG:32632
geometry_valid       all valid
geometry_not_empty   none empty
feature_count_exact  expected 1, got 1
```

Not one of them looks at whether the number is right. MapSmith got the answer
because rasterio undoes the TIFF predictor and exactextract honours nodata — the
engines were correct, and the verification would have recorded seven passing
checks beside a wrong answer just as cheerfully.

That is worth saying plainly on the first page of results, because the opposite
is what a reader would assume: **a provenance manifest records what was done, and
does not certify that it was right.** Those are different claims and MapSmith
only makes the first. The suite exists to measure the second, which is precisely
why it is not in MapSmith's repository.

The README at launch promised that the first published result would include
MapSmith with its verification switched off. There is no such switch, and we are
not adding one —
a "skip the checks" flag on a product whose argument is that it checks is a
footgun somebody eventually ships with. On these three families it would change
nothing anyway, for the reason above. When a family arrives that verification
*does* catch, the comparison becomes meaningful and will be run by disabling the
specific check rather than the mechanism.

### The rest

**whitebox-workflows 0.50** — it fails trap 001, the TIFF predictor, which is
[an open upstream issue](https://github.com/jblindsay/whitebox_next_gen/issues/32)
we reported. It handles nodata correctly. This is not a verdict on the library:
it is one defect, in one reader, reported to its author, and the number will
change when it is fixed.

**naive composition 0.67** — read the file, take the statistic, report it. It
falls into two traps and **passes the third**, because rasterio undoes the
predictor on its behalf. Careless code is not uniformly wrong; it is correct
until the data stops having the shape it usually has.

**"Not applicable"** counts probes an adapter cannot express, and it is not a
failure. MapSmith exposes no area operation, so `002-feet-as-metres` was never
put to it. Scoring an operation a system was never asked to perform would
measure the adapter.

### What the first run's numbers did not say

Kept as written, because a superseded caveat is still a record of what was
claimed at the time: three families of twelve were implemented, so a 0.00 over
two traps was a narrow statement — and one that four later families have since
tested. The standing version of this caveat is
[at the top of this page](#what-these-numbers-do-not-say).
