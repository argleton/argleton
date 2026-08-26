# 010 — The band was stored, not measured

## The file

`scene.tif` holds two bands of an optical scene: band 1 red, band 2
near-infrared, both `uint16` digital numbers. The file **declares its own
calibration** in its metadata: scale `0.0001`, offset `-0.1` on both bands.

```
physical = raw × scale + offset        (the GDAL definition, and the one in the file)
red  = 3000 × 0.0001 − 0.1 = 0.2
nir  = 5000 × 0.0001 − 0.1 = 0.4
```

## The right answer, on paper

NDVI = (NIR − RED) / (NIR + RED) = (0.4 − 0.2) / (0.4 + 0.2) = 0.2 / 0.6 =
**1/3 exactly**. Every pixel carries the same pair, so the mean is that number
and no averaging error enters. Tolerance 1e-4, which covers float32 storage and
nothing else.

## The wrong answer

Read the two bands, put them in the formula: **0.25**.

GDAL's raster data model states it plainly — *"applying scale and offset is of
the responsibility of the user, and is not done by methods such as RasterIO()
or ReadBlock()"*. The arrays that come back hold 3000 and 5000. The index comes
out (5000−3000)/(5000+3000) = 0.25, and nothing in an array says it is not a
reflectance.

## Why it is admitted

0.25 and 0.3333 are both ordinary NDVI values for vegetation. Neither is out of
range, neither looks like an artefact, and the gap between them is the sort
that separates a stressed crop from a healthy one — not a bug from a result.

The deeper reason this survives everywhere is worth stating, because it
explains why careful people have this bug:

> **Without an offset, NDVI is invariant to the scale factor.** The scale
> cancels in the ratio. Code that divided digital numbers by 10000 — or skipped
> the conversion entirely — produced exactly the right answer, for years.

Then ESA introduced `BOA_ADD_OFFSET` (−1000 DN) with Sentinel-2 processing
baseline 04.00 on **25 January 2022**. The invariance stopped holding. The same
unchanged pipeline now returns one number for a scene acquired on 24 January
and a different one for the same ground on 26 January, with no error anywhere,
and the difference is not a constant — it depends on the brightness of what you
are looking at.

## The clean twin

[c010-physical-values](../../clean/c010-physical-values/) asks the same
question of a scene already in physical units (float reflectances 0.2 and 0.6,
no scale, no offset): **0.5**. A system that answers the twin and misses the
trap can compute NDVI and ignores declared calibration; one that misses both
cannot compute NDVI, which is a different and lesser finding.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | 0.25 | silent error |
| rasterio 1.5.1 (informed) | 0.3333 | correct |
| MapSmith | 0.3333 | correct |

MapSmith had **no band arithmetic at all** when this trap was written, and the
first run of it returned `unsupported` — the fourth time this suite has named a
gap in its own author's catalogue rather than a defect in someone's code. The
operation that answers it, `band_math`, applies the declared scale and offset
and records the conversion in the manifest; it also computes in float64,
because subtracting two `uint16` bands wraps around at zero, and writes float32
output, because inheriting an integer profile would round an index in [−1, 1]
to zeros and ones. Three silent failures in one operation, which is roughly the
density this family has.
