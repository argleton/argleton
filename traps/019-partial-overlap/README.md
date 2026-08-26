# 019 — The whole parcel counted as flooded

## The file

Five fields of 10000 m² and a flood band 300 m wide and 30 m deep, covering a
strip of the first three. There is a 10 m gap after the third — a road — so the
band does not touch the fourth.

## The right answer, on paper

3 × (100 × 30) = **9000 m²** of farmland inside the band.

## The wrong answer

Select the fields that intersect the band and sum their areas: **30000 m²**.

The selection is right — those three fields do meet the band — and the
aggregation quietly changes the unit of measurement from the square metre to
the parcel.

## Why it is admitted

3 ha of flooded farmland is an ordinary figure, and it is more than three
times the truth. Nothing says the parcels were counted whole: the query
returned the right features, the sum returned a number, and the report reads
as an area. This is how exposure and compensation figures are inflated without
anyone making an arithmetic mistake.

## The clean twin

[c019-fully-contained](../../clean/c019-fully-contained/) uses a band deep enough to contain three whole fields, where
intersection area and parcel area agree at 30000.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | 30000.0 | silent error |
| MapSmith | 9000.0 | correct |

Second probe of the double-counting family ([012](../012-double-counting/)):
the same mechanism — an aggregation whose unit is not the one the question asks
about — in the form it takes in exposure analysis.
