# 005 — A self-intersecting parcel whose area is computed anyway

## The file

`parcel.gpkg` holds one polygon in **EPSG:32632** whose ring crosses itself: a
bowtie with two unequal lobes. Nothing refuses to store it — GeoPackage writes
it, every reader reads it back unchanged, and it renders as two filled
triangles that look like an ordinary odd-shaped parcel. Invalid rings are
endemic in real cadastral and digitised data, which is why every serious
engine ships a repair function.

## The right answer, on paper

The ring is A=(0,0), B=(0,100), C=(120,20), D=(120,80) in local metres. Edges
B→C and D→A cross at X=(75,50), splitting the figure into two triangles:

```
(A, B, X): 100 · 75 / 2 = 3750 m²
(C, D, X):  60 · 45 / 2 = 1350 m²        total: 5100 m²
```

**5100 is the only defensible answer.** Both fill rules (even-odd and nonzero
winding) fill both lobes — which is also what any renderer draws — and
repairing the ring with `make_valid` yields exactly the two triangles as a
MultiPolygon of area 5100. A refusal that names the self-intersection is also
accepted: repairing and refusing-with-reason are both careful behaviours.

## The wrong answer

Read the file, take `.area`, report it: **2400**.

That is the shoelace sum over the ring, in which the two lobes carry opposite
orientation and partially cancel: |3750 − 1350| = 2400 — a number that matches
no definition of a region at all. And it arrives more quietly than the
library's own manual predicts: Shapely's documentation says of self-crossing
rings that "exceptions will be raised when they are operated on" — for the
area, nothing is raised. No exception, no warning, a plausible number.

## Why it is admitted

2400 m² and 5100 m² are both entirely ordinary parcels. The file is well
formed, the CRS is declared and metric, the geometry renders. The only wrong
thing is that a ring crosses itself and nothing in the composition ever asked
`is_valid` — the repair function exists in every engine, and a repair function
that is never called protects nobody.

## Observed

| adapter | answer | |
|---|---|---|
| `engine:geopandas` — checks validity, repairs with `make_valid`, **and says so** | 5100.0, `correct_with_warning` | ✓ |
| `engine:naive` — sums `.area` | 2400.0 | ✗ |

The careful adapter's verdict is worth a note: it is scored
`correct_with_warning`, not plain `correct`, because it *communicated* the
repair. Measuring after a silent repair would be trading one silence for
another.

## Clean twin

`clean/c005-polygon-area` — a valid L-shaped parcel, same CRS, same question,
area 7600 m² by decomposition on paper. The trap and its control differ in
exactly one thing: whether the ring crosses itself.
