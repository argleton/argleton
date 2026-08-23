# 003 — Declared nodata cells counted as elevations

## The file

`dem.tif` is a 100×100 int16 DEM in EPSG:32632. Every valid cell holds 1000 m.
Fifty cells hold **−9999**, and the GeoTIFF header declares `nodata = -9999`,
which is where every raster library looks.

Nothing is hidden and nothing is malformed. Voids are what a DEM has where the
sensor saw cloud, water or steep shadow; −9999 and −32768 are the conventions
that fill them, and SRTM and ASTER GDEM ship them by the million.

## The right answer, on paper

9950 valid cells, all 1000. The mean is **1000.0** exactly.

## The wrong answer, also on paper

```
(9950 × 1000 + 50 × −9999) / 10000 = 9450050 / 10000 = 945.005
```

## Why it is admitted, and why this one is worse than it looks

945 m is not merely a possible mean elevation. It is an unremarkable one, and it
is **5.5% from the truth** — far too small for anyone to question, and far too
large to ignore in a volume, a gradient, a flood level or a carbon estimate.

That is the shape that matters. The same defect on a raster with many voids
returns something like −0.99, and the first person to see a negative mean
elevation catches it. The version that survives is the one where the void
fraction is small, and a DEM with 0.5% voids is an ordinary DEM. The bias tracks
the void fraction, so the error is *usually* the invisible size.

Everything else about the run is clean: valid raster, declared and correct CRS,
declared and correct nodata, intact grid, statistic returned without a warning.
The only evidence is a number that looks fine.

## Not a bug in any library

`ds.read(1)` returns the raw array. `ds.read(1, masked=True)` returns the masked
one. Both are one line, and the raw one is the default. Nothing is broken; a
keyword is missing, and nothing downstream can tell.

## Observed

| adapter | answer | |
|---|---|---|
| `engine:rasterio` — `read(1, masked=True)` | 1000.0 | ✓ |
| `engine:naive` — `read(1)` | 945.005 | ✗ |

Worth noting: `engine:naive` **passes** trap 001. The careless composition is
not uniformly careless — it is correct whenever the data happens to be shaped
the way it usually is, which is exactly what makes the cases where it is not so
hard to see.

## Clean twin

`clean/c003-raster-mean-nodata` — the same grid with no void cells, and the same
`nodata = -9999` still declared in the header. The only difference between the
two probes is whether any cell holds that value.
