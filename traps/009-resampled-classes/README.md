# 009 — A class that is not in the file, produced by resampling

## The file

`landcover.tif` is a 3×3 grid of 20 m cells in EPSG:32633, with the legend
`1=forest, 2=urban, 3=water` written into its tags. The two west columns are
forest, the east column is water. **No cell is urban.**

The question asks for the urban area on a **15 m** grid — the resolution of
another dataset it has to line up with, which is the ordinary reason anyone
resamples anything.

## The right answer, on paper

The file contains exactly two values, 1 and 3. A class code is a label, not a
measurement, so no resampling rule that is valid for labels can produce a label
that was not there: nearest neighbour and mode both *select* one of the
contributing cells' values, so the output alphabet is a subset of the input
alphabet `{1, 3}`.

**The urban area is exactly 0 m².** Tolerance 0 — this is not a measurement with
error bars, it is the extent of something that does not exist. The answer holds
at any target resolution, which is what makes the derivation robust: it does not
depend on how the grids happen to line up.

## The wrong answer

Resample with a method that produces smooth output: **900 m² of urban.**

With a 60 m extent and 15 m cells the output is 4×4, and the new cell centres
fall *between* the old ones. Across the forest/water boundary the interpolated
value is the average of 1 and 3 — which is 2. Four cells of 225 m² come back
coded urban.

Measured on rasterio 1.5.1, three methods do this and two do not:

| method | urban cells | urban area | distinct codes |
|---|---|---|---|
| `nearest` | 0 | 0 m² | 1, 3 |
| `mode` | 0 | 0 m² | 1, 3 |
| **`bilinear`** | **4** | **900 m²** | 1, **2**, 3 |
| **`cubic`** | **4** | **900 m²** | 1, **2**, 3 |
| **`average`** | **4** | **900 m²** | 1, **2**, 3 |

## Why it is admitted

900 m² of urban between a forest and a lake is not a suspicious number: it is
what a road, a car park or a few buildings on a shoreline look like — and
shorelines are exactly where settlements are. Nothing in the result hints that
the value was derived rather than observed: the raster is well formed, every
code is in the legend, and the areas still add up.

The tell-tale would be the code 2 appearing where the input had none, and no
raster library reports that. rasterio's documentation recommends bilinear and
cubic for *"continuous data"* and carries no warning anywhere about categorical
data — reasonably, because **nothing in a GeoTIFF says which of the two it is
holding**. The rule "use nearest or majority for discrete data" is in every
vendor's manual (Esri's Resample tool, GDAL's `-r mode`) and is enforced by
none of them.

The trap plants the case where the invented code is a class that *exists in the
legend*, so the wrong answer is a plausible quantity rather than an obvious
artefact. A `1.5` would have been noticed; a `2` is urban.

## The clean twin

[c009-native-resolution-classes](../../clean/c009-native-resolution-classes/)
asks the same question about a file that is already on the 15 m grid and has
four genuinely urban cells: **900 m², for real**. Deliberately the same number
the trap's naive answer produces — what separates the two probes is not the
quantity but whether the class is in the data.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | 900.0 | silent error |
| rasterio 1.5.1 (informed) | 0.0 | correct |
| MapSmith | 0.0 | correct |

MapSmith's pass is earned in a specific and narrow way, worth stating because
the suite exists to keep its authors honest: `resample_raster` has **no default
method**, so the composition had to choose one, and a caller who has been told
the legend chooses a categorical method. Had it chosen `bilinear` anyway, the
result would have come back carrying `invented_values: [2.0]` and a check named
`no_invented_class_codes` — not a refusal, a report. The defence is that the
question is asked, and that the answer is checked against the input's own
alphabet afterwards.
