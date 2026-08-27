# 022 — Thiessen cells paired with their rows by position

## The files

`gauges.gpkg` holds five rain gauges in UTM 33N with one annual rainfall reading
each; `site.gpkg` holds one site. Round coordinates, ordinary readings, valid
geometry, a declared metric CRS. There is nothing wrong with the data, and that
is deliberate: this trap is not about a file, and not about a bug in any library.
It is about three lines of composition.

| gauge | position | reading |
|---|---|---|
| G-1 | (0, 0) | 412.0 mm |
| G-2 | (400, 300) | 268.0 mm |
| G-3 | (800, 600) | 731.0 mm |
| G-4 | (1200, 900) | 554.0 mm |
| G-5 | (200, 900) | 197.0 mm |

The site is at (300, 500).

## The right answer, on paper

**268.0 mm.**

The Thiessen method assigns every location the reading of the nearest gauge — the
cells are a way of drawing that assignment, not a separate definition of it. So
the answer follows from five distances, all exact by construction:

| gauge | distance from the site | reading |
|---|---|---|
| G-2 | √(100² + 200²) = 223.6068 m | **268.0** |
| G-5 | √(100² + 400²) = 412.3106 m | 197.0 |
| G-3 | √(500² + 100²) = 509.9020 m | 731.0 |
| G-1 | √(300² + 500²) = 583.0952 m | 412.0 |
| G-4 | √(900² + 400²) = 984.8858 m | 554.0 |

G-2 wins by 188.70 m over the runner-up, so the site sits well inside one cell
and no rounding decides anything. No two gauges are within 5 m of equidistant
from the site: the question admits exactly one answer, and the tolerance is 0
because the answer is one of five numbers already in the file.

## What goes wrong

```python
cells = shapely.voronoi_polygons(MultiPoint(list(gauges.geometry)))
gauges["geometry"] = list(shapely.get_parts(cells))     # <- the defect
answer = gauges.sjoin(site)["rainfall_mm"]
```

`voronoi_polygons` returns the cells in an order that is an implementation
detail, not the input order. Shapely has an `ordered=True` for exactly this, and
it is **off by default** — and it only arrived in shapely 2.1 (2025), so every
recipe written before then, and every recipe copied from one, pairs by position.

On this layout the default order puts **one of the five** cells on its own point.
The cell that covers the site arrives carrying G-4's reading: a gauge 985 m away,
across two other cells. The answer comes back **554.0 mm**.

## Why it is silent

Every check a person would actually run passes.

- Five gauges in, five cells out.
- Every cell is a valid polygon.
- The cells tile the extent with no gap and no overlap.
- The total area is right.
- The map looks exactly like a Thiessen diagram — because it *is* one.

The **set** of cells is identical whichever order they come in; only the pairing
differs. Measured: the sorted cell areas are the same to the millimetre with
`ordered=False` and `ordered=True`. So no property of the geometry can reveal the
error, and no amount of looking at the map will.

And the answer is one of the file's own readings. 554 mm is an ordinary annual
total, in range, in the right units, sitting next to four other ordinary totals.
The person who asked receives a number measured by a real gauge. It is simply the
wrong gauge, and nothing in the result says which one it came from.

There is one more thing worth saying about this failure: it does not degrade
gracefully, and it is not stable. With a different gauge layout the same code
answers correctly **by luck** — of six candidate layouts tried while building
this trap, five hid the defect that way. A pipeline that was right yesterday on
other data is wrong today on this, and nothing changed but the data.

## Measured

| | |
|---|---|
| shapely | 2.1.2 — `voronoi_polygons(ordered=False)` by default |
| geopandas | 1.1.4 — `sjoin` and row order are both faithful; the defect is upstream |
| `ordered=False` | 1 of 5 cells on its own point → **554.0** |
| `ordered=True` | 5 of 5 cells on their own point → **268.0** |

## The clean twin

`clean/c022-two-gauges` asks the same question of two gauges 5 km apart, with the
site 224 m from one of them. There the pairing cannot go wrong: every pairing an
implementation can produce puts the site in G-1's cell, and both orders answer
305.0. A system that gets the twin right and the trap wrong has met the defect; a
system that misses both could not do the task at all; and a system that refuses
everything to keep its silent-error rate down is caught by the twin, where there
is nothing to refuse.

## How to beat it

Two ways, and both are ordinary.

1. **Ask the right question.** The Thiessen method *is* nearest-neighbour
   assignment, so compute the nearest gauge and read its value. No polygons, no
   ordering to get wrong. This is what `engine_geopandas` does, in two lines.
2. **Verify the pairing instead of assuming it.** If you do build the cells,
   check that each one contains the point whose row it carries — a containment
   test per row, which is closed-form and cheap. Asking for `ordered=True` is
   necessary and not sufficient: it is a declaration, and this is the check.
