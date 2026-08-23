# 001 — TIFF horizontal predictor is not undone on read

## The file

`dem.tif` is an ordinary GeoTIFF: 32×32, int16 elevations, EPSG:32632, 30 m
pixels, deflate compression, **predictor 2**.

Predictor 2 is TIFF tag 317 set to `2`, horizontal differencing. Before
compressing, each sample is replaced by the difference from its left neighbour,
because the differences of a smooth surface compress far better than the values.
It is standard, it is what GDAL writes when you ask for it, and undoing it on
read is the reader's job — not an optional optimisation.

`dem_plain.tif` holds the identical elevations without the predictor. A
conforming reader returns the same array from both, and it is in the fixture so
that anyone can check that in one line.

## The right answer, on paper

The elevations are defined in `build.py` as

```
v[i,j] = 1000 + 4j + 2i      i, j = 0..31
```

so the mean is `1000 + 4·mean(j) + 2·mean(i) = 1000 + 4·15.5 + 2·15.5` = **1093.0**
exactly. No reference implementation is consulted: it is arithmetic on the
definition. That matters — a truth obtained by running some other library
measures agreement with that library, and the day it has the same bug, the
suite certifies it.

## The wrong answer, also on paper

A reader that returns the stored differences sees `v[i,0]` in the first column
and a constant `4` everywhere else. Summing along row `i` telescopes:

```
v[i,0] + Σ (v[i,j] − v[i,j−1]) = v[i,31]
```

so the total is `Σ_i v[i,31] = 32 · (1124 + 2·15.5) = 32 · 1155`, and the mean is
`36960 / 1024` = **36.09375** — the mean of the last column divided by the width.

The wrong answer is not noise. It is a different, predictable statistic, which
is exactly why a system can produce it with complete confidence.

## Why it is admitted

36 m is an unremarkable mean elevation. No NaN, no negative, no nodata sentinel,
no exception. The grid the number came from still renders as terrain; hillshade
over it still looks like hillshade and flow accumulation still flows downhill,
which is how the upstream bug was noticed at all — not because anything failed,
but because the terrain was subtly the wrong terrain.

Only a comparison against the true elevations reveals it, and nothing in an
ordinary workflow performs that comparison.

## Observed

| system | answer |
|---|---|
| rasterio / GDAL | 1093.0 ✓ |
| whitebox-workflows | 36.09375 ✗ |

Reproduced 2026-08-23. Upstream report:
<https://github.com/jblindsay/whitebox_next_gen/issues/32>.

If upstream fixes this, the probe does not stop being useful: it becomes a
regression test with a date on it.

## Clean twin

`clean/c001-raster-mean` — the same elevations, stored plainly. Without it, a
silent-error rate on this family could not be told apart from "the system cannot
open the file at all".
