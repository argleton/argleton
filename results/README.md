# Results

Every file here names the `spec_commit` it ran against. That is the
pre-registration: whether a tolerance or a task moved after a number was seen is
answered by a diff, not by our word.

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

The README promises that the first published result includes MapSmith with its
verification switched off. There is no such switch, and we are not adding one —
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
