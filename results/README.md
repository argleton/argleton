# Results

Every file here names the `spec_commit` it ran against. That is the
pre-registration: whether a tolerance or a task moved after a number was seen is
answered by a diff, not by our word.

## 2026-08-25 — six families, and the suite catches its author

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

### What these numbers do not say

Three families of twelve are implemented ([FAMILIES.md](../docs/FAMILIES.md)).
A 0.00 here means a system did not fail silently **on these probes** — not that
it is correct, and not that it is safe. With this few probes, one new family can
move any of these rates a long way, which is the honest state of a suite that is
four days old.

Nobody was notified before publication because nothing here is a new claim about
a third party: the Whitebox defect was reported upstream first, and everything
else is a library behaving as documented. That changes the moment a result says
something a maintainer has not already been told.
