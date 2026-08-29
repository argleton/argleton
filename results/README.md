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
the suite. Twenty-seven families of twenty-seven are implemented
([FAMILIES.md](../docs/FAMILIES.md)).

- **A 0.00 means a system did not fail silently *on these probes*.** Not that it
  is correct, not that it is safe, and not that it would survive the five
  families that are named and not yet built — nor the thirty further
  mechanisms a survey of the literature turned up while this run was being
  made.
- **Read "not applicable" before the rate.** A rate over two traps and a rate
  over twenty-two are different claims. An adapter that can only be asked two
  questions must not be able to look better than one that faced all of them.
- **One family can still move any of these rates a long way**, because most of
  them carry one trap each — treat a difference of one probe as one probe.
- **Engine tier only.** Every number here comes from an adapter calling a
  library directly. Nothing on this page measures an agent, and the agent tier
  will be reported with its variance rather than as a single run.
- **The wall clock in every result is not a benchmark.** One observation per
  probe, one machine, no repetition and no warm-up control. Read it for gross
  differences — a factor of ten — and never as a ranking. Two systems that ran
  different subsets of the suite did different work, so `probes` travels with
  the timing; and where an adapter reports a breakdown, most of its wall clock
  may belong to our harness rather than to the product: the one that spawns a
  fresh interpreter per probe spends about six seconds per probe importing its
  library before any geoprocessing happens. `METHOD.md` §9b is the full
  statement.
- **These are not verdicts on libraries.** whitebox-workflows fails one trap
  because of [one open upstream defect](https://github.com/jblindsay/whitebox_next_gen/issues/32)
  we reported; everything else here is a library behaving exactly as documented.

Nobody is notified before publication as long as nothing here is a new claim
about a third party: the Whitebox defect was reported upstream first, and the
rest is documented behaviour. That changes the moment a result says something a
maintainer has not already been told.

## 2026-08-30 (later) — the famous one, and why it took twenty-five traps

Published run: [`2026-08-30-antimeridian/`](2026-08-30-antimeridian/).
Engine tier, `spec_commit` [`74a620f`](../../../commit/74a620f), twenty-three families.

| system | silent error rate | completion rate | traps run | not applicable | probes timed | total | median |
|---|---|---|---|---|---|---|---|
| MapSmith (main) | **0.00** | 1.00 | 25 | 0 | 50 | 6.7 s | 112 ms |
| GeoPandas 1.1 + Shapely 2 (careful composition) | 0.00 | 1.00 | 10 | 30 | 20 | 0.9 s | 14 ms |
| rasterio 1.5.1 (careful composition) | 0.00 | 1.00 | 5 | 40 | 10 | 0.4 s | 6 ms |
| whitebox-workflows 2.0.6 | 0.6667 | 1.00 | 3 | 44 | 6 | 0.1 s | 8 ms |
| naive composition | 0.96 | 1.00 | 25 | 0 | 50 | 1.4 s | 11 ms |

The new family is [`antimeridian`](../traps/025-antimeridian-zone/), which was in
the original twelve and took until the twenty-fifth trap to build. That is worth
saying plainly, because it is the opposite of what a roadmap suggests: **famous
is not the same as easy to plant.**

Every obvious formulation of this failure is loud. An extent that spans 358
degrees, a distance of 40 000 km between two islands, a centroid in the Gulf of
Guinea — all real, all produced by ordinary code, and all absurd enough that
something already catches them. A probe whose typical failure is absurd belongs
in a unit test; this suite is for the answers nothing catches. What took the time
was finding the quiet version.

The quiet version is a **count**. The zone is two degrees by one in Fijian
waters, written the way RFC 7946 §3.1.9 says to write it: a MultiPolygon split at
180, every coordinate in range, geometry valid, nothing ambiguous in the file. Its
bounds are therefore `(-180, -17.5, 180, -16.5)` — a band round the planet — so
filtering to the study area's bounding box before testing containment, which is
the coordinate-slice idiom out of the GeoPandas documentation, admits every vessel
at that latitude. Nine instead of five.

Nine is plausible in the way counts are: no unit, no magnitude, nothing to compare
against. The four extra vessels are real positions at the right latitude, and only
their longitudes give them away.

**The two halves of the standard do not compose**, and that is the finding rather
than any one library's behaviour. §3.1.9 says split the geometry at the line;
§5.2 says a bounding box whose west exceeds its east is the one that crosses it. A
geometry split correctly per the first has bounds that cannot be written in the
form the second describes, and no planar geometry library computes anything else.

Careful GeoPandas and MapSmith both answer 5, on the trap and on its clean twin.
The twin moves the zone ten degrees west, where the bounding box *is* the zone and
the failing filter is exactly right — so a system that has learned to distrust
bounding boxes near the line still has to answer an ordinary rectangle.

## 2026-08-30 — half a cell, and the engine that half-honours the convention

Published run: [`2026-08-30-grid-registration/`](2026-08-30-grid-registration/).
Engine tier, `spec_commit` [`9322b17`](../../../commit/9322b17), twenty-two families.

| system | silent error rate | completion rate | traps run | not applicable | probes timed | total | median |
|---|---|---|---|---|---|---|---|
| MapSmith (main) | **0.00** | 1.00 | 24 | 0 | 48 | 6.1 s | 100 ms |
| GeoPandas 1.1 + Shapely 2 (careful composition) | 0.00 | 1.00 | 9 | 30 | 18 | 0.9 s | 17 ms |
| rasterio 1.5.1 (careful composition) | 0.00 | 1.00 | 5 | 38 | 10 | 0.4 s | 5 ms |
| whitebox-workflows 2.0.6 | 0.6667 | 1.00 | 3 | 42 | 6 | 0.1 s | 9 ms |
| naive composition | 0.9583 | 1.00 | 24 | 0 | 48 | 1.4 s | 11 ms |

One family is new — [`grid-registration`](../traps/024-pixel-is-point/) — and it
is the one where the answer is written in the file and thrown away in the last
line. GeoTIFF has two raster types: under `RasterPixelIsArea` a value describes
the cell it fills, under `RasterPixelIsPoint` it is a sample at a grid node, and
they differ by half a pixel in each axis. USGS elevation products are the second
kind. `hollow.tif` declares it.

Asked where the lowest cell of an 8×8 DEM at 30 m spacing is, the correct
easting is **412090**. The naive composition answers **412105**, half a cell
east. Whitebox answers **412120** — a whole cell. The careful rasterio
composition answers **412090**, and that is the row that makes the family worth
having.

**The careful adapter passes because four lines are enough.** Read
`src.tags()["AREA_OR_POINT"]`, subtract half a cell when it says `Point`. The
information is on the same open dataset that `src.xy()` reads from, acting on it
is cheap, and nothing in the API prompts you to — which is what makes this the
caller's error rather than the library's, and what separates it from a defect we
could only report upstream.

It also cost this suite a red build to get right. The first run of this trap had
the careful rasterio adapter at 0.20, because the adapter used `xy` and stopped
there; the CI gate that requires the careful adapters to stay at zero went red
and was correct to. *Careful* is defined in that gate as composing a library the
way somebody who knows it does, in the cases where the library offers the right
path. rasterio offers it. The adapter was not careful, and the gate — not a
reviewer — is what said so.

**Whitebox is the other case, and it is worse.** It reacts to the tag: its
reported grid origin shifts on this file where it does not on the twin. But it
shifts in the direction that makes a caller who then adds the usual half cell for
a centre land one full cell out. An engine that half-honours a convention is
harder to be careful with than one that ignores it, because the correction that
fixes the second breaks on the first.

**MapSmith reported `unsupported` twice when this run was first published, and
answers both probes now.** The gap was the finding and it was worth publishing as
one: no operation said *where* a cell is, and no line of MapSmith read the
raster-type tag — the same absence twice, because nothing had ever needed to ask
the question. Fixing it was not a patch at the point of failure. Every place that
turned an index into a coordinate had the defect, so the decision moved into one
module and a test now fails if a second copy appears.

The two published numbers for MapSmith are unchanged at 0.00 and 1.00, and the
denominator moved from 23 to 24. That is the only honest way this could improve:
the rate was already zero, and what the trap actually bought was a column of the
table nobody looks at.

The trap was found while writing a contour operation for MapSmith. The engine
placed every contour half a cell from where the elevation it named actually
occurred, and it was caught by checking the output against the input — sample the
DEM where the line says it is, and the elevation has to match — rather than by
reading any documentation. That check now ships with the operation, which is the
only reason the shipped product does not have this defect on area-registered
DEMs. On point-registered ones it refuses to produce contours at all, loudly,
which is the correct behaviour available today and not the one we want.

## 2026-08-29 — the two columns in the order a human says them

Published run: [`2026-08-29-axis-order/`](2026-08-29-axis-order/).
Engine tier, `spec_commit` [`243f912`](../../../commit/243f912), twenty-one families.

| system | silent error rate | completion rate | traps run | not applicable | probes timed | total | median |
|---|---|---|---|---|---|---|---|
| MapSmith (main) | **0.00** | 1.00 | 23 | 0 | 46 | 8.1 s | 104 ms |
| rasterio 1.5.1 (careful composition) | 0.00 | 1.00 | 4 | 38 | 46 | 0.5 s | 7 ms |
| GeoPandas 1.1 + Shapely 2 (careful composition) | 0.00 | 1.00 | 9 | 28 | 46 | 1.0 s | 14 ms |
| whitebox-workflows 2.0.6 | 0.50 | 1.00 | 2 | 42 | 46 | 0.1 s | 20 ms |
| naive composition | 0.9565 | 1.00 | 23 | 0 | 46 | 1.4 s | 13 ms |

One family is new — [`axis-order`](../traps/023-axis-order/) — and it is the one
where the file is not wrong. EPSG:4326 declares latitude first; every Python
geometry library expects longitude first; INSPIRE and WFS 1.1 mandate the
authority order on the wire. Both conventions are current and both are declared,
so a corner schedule can be written either way round and the header is the only
thing that says which.

The naive composition reads the two coordinate columns in the order it finds
them and reports **16261.6 m² instead of 14042.3** — 1.63 hectares against 1.40.
Nothing raises: 23.73 is a valid latitude and 37.98 a valid longitude, so no
range check fires, and the swapped parcel lands in the Egyptian desert, which
nobody sees because the question asked for an area.

**The careful compositions and MapSmith all answer 14042.345991909504**, which is
the closed-form ellipsoidal area to the milli-square-metre. That agreement is
worth more than the verdict: the truth for this probe was derived on paper from
the zone integral before any adapter ran, and three independent routes landed on
it.

MapSmith's pass is not luck, and it is the kind of thing this suite exists to
distinguish. `parse_coordinates` has no positional path — `latitude_columns` and
`longitude_columns` are both required, with no default — because it was written
for the DMS trap under the rule *the caller says which, because the file cannot*.
The same rule closes this trap. A design that refuses to guess refuses to guess
about more than the thing it was designed for.

Two adapters report `unsupported`: rasterio and whitebox are raster engines and a
corner schedule is not a raster. That is the honest verdict and it is why the
"not applicable" column is published beside the rate.

## 2026-08-28 (later) — the same run, now with a stopwatch

Published run: [`2026-08-28-timings/`](2026-08-28-timings/).
Engine tier, `spec_commit` [`4a6dbac`](../../../commit/4a6dbac), twenty families.
Same verdicts as the run above; what is new is the last three columns.

| system | silent error rate | completion rate | traps run | not applicable | probes timed | total | median | first probe |
|---|---|---|---|---|---|---|---|---|
| MapSmith (main) | **0.00** | 1.00 | 22 | 0 | 44 | 6.3 s | 103 ms | 1.9 s |
| rasterio 1.5.1 (careful composition) | 0.00 | 1.00 | 4 | 36 | 8 | 0.6 s | 6 ms | 0.6 s |
| GeoPandas 1.1 + Shapely 2 (careful composition) | 0.00 | 1.00 | 8 | 28 | 16 | 1.0 s | 16 ms | 0.6 s |
| whitebox-workflows 2.0.6 | 0.50 | 1.00 | 2 | 40 | 4 | 0.2 s | 16 ms | 0.2 s |
| naive composition | 0.9545 | 1.00 | 22 | 0 | 44 | 1.2 s | 11 ms | 0.2 s |

**Read the "probes timed" column before the times.** Four of these five adapters
answered a fraction of the suite: rasterio attempted 8 probes of 44 and MapSmith
attempted all 44, so their totals are not two measurements of the same thing.
The median is the comparable figure, and even that compares different work,
because a probe over a 24×24 elevation model and a probe over one polygon are
not the same task.

**MapSmith is the slowest per probe, and that is the honest headline.** 103 ms
against 11 ms for the careless composition — about nine times. The difference is
not mysterious: on every write MapSmith hashes its inputs, records the CRS
decision, runs the deterministic checks and writes a manifest beside the output.
The naive composition reads the file, takes the statistic and returns. It is
buying nothing, so of course it is cheaper, and 0.9545 of its answers on these
traps are silently wrong.

Whether ninety milliseconds is worth a manifest is a question for whoever is
paying, and this page is not going to answer it. What the page can do is stop
the number being invisible. It is also the number to watch: if provenance ever
costs a second instead of a tenth of one, that is a regression whatever the
verdicts say.

**What these times are not** is in [`METHOD.md` §9b](../docs/METHOD.md): one
observation per probe on one machine, no repetition, no warm-up control. They
are here to make a factor of ten visible, not to rank anything. Fixture building
is outside the stopwatch, and skipped probes are excluded — an `unsupported`
returns in microseconds because nothing ran, and including those put rasterio's
median at 0 ms in the first version of this measurement.

## 2026-08-28 — a defect that is not in any file

Published run: [`2026-08-28-thiessen-pairing/`](2026-08-28-thiessen-pairing/).
Engine tier, `spec_commit` [`45cfd14`](../../../commit/45cfd14), twenty families.

| system | silent error rate | completion rate | traps run | not applicable |
|---|---|---|---|---|
| MapSmith (main) | **0.00** | 1.00 | 22 | 0 |
| rasterio 1.5.1 (careful composition) | 0.00 | 1.00 | 4 | 36 |
| GeoPandas 1.1 + Shapely 2 (careful composition) | 0.00 | 1.00 | 8 | 28 |
| whitebox-workflows 2.0.6 | 0.50 | 1.00 | 2 | 40 |
| naive composition | 0.9545 | 1.00 | 22 | 0 |

**Every trap in this suite so far has been a property of a file or of a
library.** A unit that lies, a datum the one-liner skips, a predictor a reader
does not undo, a CRS whose metres are metres of map. [Trap
022](../traps/022-thiessen-pairing/) is the first that is neither: the file is
five rain gauges with round coordinates and ordinary readings, every library
involved behaves exactly as documented, and the defect lives entirely in three
lines of composition.

```python
cells = shapely.voronoi_polygons(MultiPoint(list(gauges.geometry)))
gauges["geometry"] = list(shapely.get_parts(cells))     # <- here
answer = gauges.sjoin(site)["rainfall_mm"]
```

The cells come back in an order that is an implementation detail. Pairing them
with the rows by position gives the site a reading measured 985 m away, across
two other cells: 554 mm where the answer is 268 mm.

What makes it worth a family of its own is that **the geometry cannot show it**.
Five gauges in, five cells out; every cell valid; the cells tile the extent with
no gap and no overlap; the total area right; the map is a Thiessen diagram
because it is one. The *set* of cells is identical whichever order they arrive
in — the sorted cell areas match to the millimetre — so every check a person
would run on the output passes. And the wrong answer is one of the file's own
readings, an ordinary annual total sitting beside four other ordinary totals.

**The failure is also not stable, which is the part worth carrying away.** Of
six candidate gauge layouts tried while building the trap, five hid the defect
by luck: shapely's default order happened to put the site's cell on the right
row. Only one exposes it. A pipeline that was right yesterday on other data is
wrong today on this, and nothing changed but the data — which is why a passing
run on your own data is not evidence about this class of error.

MapSmith answers 268 mm, and it is worth being exact about why. Not because it
asks shapely for `ordered=True`: that is a declaration, and this suite exists
because declarations are what fail silently. Its `voronoi_polygons` **verifies
the pairing geometrically**, cell by cell, and the check is in the manifest.
`engine_geopandas` answers 268 mm too, by a different and simpler route — the
Thiessen method *is* nearest-neighbour assignment, so it computes the nearest
gauge and never builds a polygon. Two lines, no ordering to get wrong. That
route is the reason the trap is fair: it is beaten by understanding the
operation, not by owning a feature.

The suite is 22 traps and 22 clean twins across twenty families. MapSmith runs
all 22 with nothing marked not-applicable, which is a statement about coverage
and not about correctness: the caveats at the top of this page apply to this run
exactly as they apply to the others.

## 2026-08-27 — the datum shift MapSmith was not applying

Published run: [`2026-08-27-datum-shift-fixed/`](2026-08-27-datum-shift-fixed/).
Engine tier, `spec_commit` [`3e98cf6`](../../../commit/3e98cf6), nineteen families.

| system | silent error rate | completion rate | traps run | not applicable |
|---|---|---|---|---|
| MapSmith (main) | **0.00** | 1.00 | 21 | 0 |
| rasterio 1.5.1 (careful composition) | 0.00 | 1.00 | 4 | 34 |
| GeoPandas 1.1 + Shapely 2 (careful composition) | 0.00 | 1.00 | 7 | 28 |
| whitebox-workflows 2.0.6 | 0.50 | 1.00 | 2 | 38 |
| naive composition | 0.9524 | 1.00 | 21 | 0 |

**MapSmith is back at 0.00, and the run where it was not stays published above.**
That is not tidiness: the interesting fact about a suite written next to a
product is what happens on the days the product fails, and deleting yesterday's
row would remove the only evidence that the metric ever moved.

`reproject_layer` now picks the transformation and then looks at which one was
picked. Where PROJ's default is a ballpark — no datum shift, coordinates carried
across unchanged — it takes the first operation from the group that states an
accuracy, and records the pipeline, the accuracy and `is_ballpark` in
`crs_decisions.transformation`, plus a note saying in words that the library's
own default applied no shift. Where every route is a ballpark it still runs,
because sometimes the datums really are equivalent, and the record says so.

**It is a computation, not a disclosure**, and that is what keeps the trap from
being a benchmark for this product: `accuracy` and `TransformerGroup` are plain
pyproj. The independent GeoPandas adapter answers the same probe with the same
digits — 45.50072600332309, declaring 44 m and landing 6.33 m from the truth,
honest inside its own stated bound.

One measurement is worth repeating because it is counter-intuitive and it is in
the code as a comment: handing PROJ the data's own extent as `area_of_interest`
looks obviously right and makes the answer **worse**. On EPSG:4806 with the
data's extent the group comes back holding only the ballpark — the 44 m
operation disappears — so the better-looking call would fall back to no datum
shift at all.

## 2026-08-26 (evening) — nineteen families, and MapSmith stops being 0.00

Published run: [`2026-08-26-nineteen-families/`](2026-08-26-nineteen-families/).
Engine tier, `spec_commit` [`461ef15`](../../../commit/461ef15), nineteen families:
one new one, `datum-ballpark`, joins the eighteen below.

| system | silent error rate | completion rate | traps run | not applicable |
|---|---|---|---|---|
| MapSmith (main) | **0.0476** | 1.00 | 21 | 0 |
| rasterio 1.5.1 (careful composition) | 0.00 | 1.00 | 4 | 34 |
| GeoPandas 1.1 + Shapely 2 (careful composition) | 0.00 | 1.00 | 7 | 28 |
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

**One row passes it, and reading which one is the whole exercise.** The careful
composition over GeoPandas does — fourteen lines that read
`get_last_used_operation().accuracy` and, when it is negative, take the first
`TransformerGroup` operation that states one. No manifest, no provenance format:
the trap is beaten by a computation any engine can do, which is the property that
keeps it from being a benchmark for the product this suite was built beside.

**The naive composition and MapSmith both fall in, and they fall in at the same
line.** `to_crs` is one line and it hands the pair to `Transformer.from_crs`,
which is also the line under MapSmith's `reproject_layer`. Two of the three
failures are the same failure reached two ways.

A note on the labels, because a number here is easy to over-read and on
2026-08-26 ours was: the careful rows are **not scores for GeoPandas or
rasterio**. Those libraries do the ordinary thing by default, and the ordinary
thing is what the naive row measures — same libraries, no care. The gap between
the two rows is the finding. For one evening this table read
"GeoPandas 1.1 + Shapely 2 | 0.00" with no qualifier, which told a reader the
library handles a case it does not.

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
