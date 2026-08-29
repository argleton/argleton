# 029 — empty result

**Nothing outside the reserve, because the subtraction ran the other way.**

`concession.gpkg` is a 24 ha mining licence. `reserve.gpkg` is an 8 ha nature
reserve wholly inside it. The question is how much of the concession lies
outside the reserve — the part that can be worked.

The right answer is **160 000 m²**. Reversing two arguments gives **0**.

## The defect

```python
overlay(concession, reserve, how="difference")   # 160000.0, one feature
overlay(reserve, concession, how="difference")   #      0.0, no features
```

Difference is not commutative, and both calls are valid. The reserve minus the
concession is a perfectly good question whose answer here is nothing at all,
because the reserve is entirely inside.

The wrong order is easy to reach for because of how the question is phrased.
*How much of the concession lies outside the reserve* puts the reserve in the
prominent position, and `reserve.difference(concession)` reads like the English
sentence. Every API takes two positional arguments of the same type: OGC Simple
Features `Difference(a, b)`, PostGIS `ST_Difference`, and the desktop erase tools
that name the two roles — input features and erase features — which helps only if
the reader knows which role the question puts first. None of them complains,
because the wrong order is a valid question.

## Why zero is the most dangerous answer

An empty result reads as a **finding** rather than as a failure. *No part of the
concession lies outside the reserve* is a sentence a board acts on: the whole
licence is protected, the application is withdrawn, the asset is written down.
Nobody reruns a query that told them something clear.

Zero also survives every check a wrong number would trip. There is no magnitude
to be suspicious of, no unit to be wrong, no geometry that looks misshapen, no
coordinate in the wrong hemisphere. The layer is valid, the CRS is right, the
operation succeeded.

And nothing raises. Both layers are in the same projected CRS, both geometries
are valid, and those two rectangles really do have an empty difference in that
order. Everything is correct except which one was subtracted from which.

**Containment is what hides it.** Two rectangles overlapping only partly would
return something in either order and the numbers would differ visibly. Here one
order returns 160 000 and the other returns nothing.

## The clean twin, which is the whole family

[`c029-coincident-boundaries`](../../clean/c029-coincident-boundaries/) is the
same concession with a reserve gazetted over exactly its footprint — a real
arrangement, digitised from the same survey. **There the answer is a legitimate
zero.**

That pairing is the family. A system that answers 0 to everything passes the
twin and fails the trap. A system that treats an empty result as a failure — that
raises or refuses rather than reporting nothing — fails the twin, and being
unable to report a real zero is its own defect: it is what teaches a caller to
distrust the zeroes that matter.

The distinction from family 4 (`mismatched-crs`) is deliberate. There the zero
comes from data that does not line up; here the data is perfect and the
operation was asked backwards.
