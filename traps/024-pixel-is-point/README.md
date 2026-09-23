# 024 — pixel is point

**A grid whose own metadata says its values sit at the nodes, read by the
coordinate helpers as if they filled the cells.**

`hollow.tif` is an 8×8 digital elevation model at 30 m spacing, a shallow
depression with exactly one lowest cell. The question is where that cell is.

The right answer is an easting of **412090**. The composition almost everyone
writes says **412105**, half a cell east. Whitebox says **412120**, a whole cell.
Nothing warns either time — and a caller who reads one extra line of metadata
gets it right, which is what makes this the caller's error rather than the
library's.

## Why the file is not wrong

GeoTIFF defines two raster types, and they differ by half a pixel in each axis:

- **`RasterPixelIsArea`** — a value describes the cell it fills, and the tie
  point is that cell's upper-left corner. The default, and what most data ships
  as.
- **`RasterPixelIsPoint`** — a value is a *sample at a grid node*, and the tie
  point is the node itself.

`hollow.tif` declares the second. That is not exotic: the USGS elevation
products — the 3DEP/NED lineage — are pixel-is-point, and so are many national
DEMs. GDAL reads the key faithfully and exposes it as the `AREA_OR_POINT`
metadata item, and its documentation is explicit that it does **not** adjust the
geotransform for it. The value is reported; the caller decides.

So the file is right, the library is right, and the position moves in the line
that joins them.

## The defect

```python
with rasterio.open(path) as src:
    values = src.read(1)
    row, col = np.unravel_index(np.argmin(values), values.shape)
    easting, northing = src.xy(row, col)      # 412105.0
```

`xy` returns the centre of the cell under the area reading, always. There is no
argument on it that mentions registration and nothing in its name suggests it
has taken a side.

The tag is one call away on the same object:

```python
src.tags()["AREA_OR_POINT"]                   # 'Point'
```

Same open dataset, same breath. The information survives all the way to the
caller and is discarded in the last line.

## Three compositions, three answers

| engine | answer | how far |
|---|---|---|
| truth | 412090 | — |
| naive composition | 412105 | half a cell east |
| rasterio, carefully | **412090** | correct |
| whitebox-workflows | 412120 | a *whole* cell east |

**The careful rasterio adapter passes**, and that row is the point of the
family. Four lines — read the tag, subtract half a cell when it says `Point` —
and both this probe and its clean twin come out right. The information is
available, acting on it is cheap, and the failure is that nothing prompts you
to. That is what makes this the caller's error and not the library's.

Whitebox is the other case, and it is worse — for a reason this page got wrong
until 2026-09-23. It read as though whitebox *reacted* to the tag, because its
reported grid origin shifts on this file and not on the twin. It does not react
to it. The origin shifts because **the two files do not carry the same tie
point**: GDAL writes `AREA_OR_POINT=Point` by moving the tie point half a cell
south-east, so that the tie point names the centre of pixel (0, 0) as the
GeoTIFF standard requires. Measured on the two fixtures' bytes — `412015,
5107985` here against `412000, 5108000` on the twin, and geokey 1025 set to 2
against 1.

Whitebox then takes that tie point for a cell **corner**, because it never reads
geokey 1025 at all. In the open `whitebox-tools` source the flag that would
carry it, `configs.pixel_is_area`, is assigned in exactly four places, all of
them copying another raster's configs; it defaults to `true`, and every read of
it is on the GeoTIFF *write* path, where it decides whether to emit the key as 1
or 2. `geokeys.rs` maps the key to the strings `RasterPixelIsArea` and
`RasterPixelIsPoint` and nothing consumes the result.

That accounts for the number exactly: corner 412015, so the centre of pixel
(0, 0) is 412030, so the centre of pixel (2, 3) is 412030 + 90 = **412120**, one
full cell from the truth. Half of that error is the tag it did not read; the
other half is the half-cell it correctly adds to reach a centre. Which is why
the uniform +0.5 shift somebody always proposes is not a fix: it is right on the
twin and doubles the error here.

*(Source read on `jblindsay/whitebox-tools` at master, which is the CLI. The row
in the results table is `whitebox-workflows` 2.0.6, a different package whose
source is not public — there, ignoring the key is what the measured 412120
predicts uniquely, not something we have read.)*

## Why fifteen metres is the dangerous amount

It is smaller than the error of the handheld GPS somebody will use to walk to
the coordinates, so a field crew sent out finds the sinkhole, confirms it, and
reports that the position was right.

It is larger than every tolerance that matters afterwards: a borehole, a pole, a
service trench, a property corner, the cell of any 10 m grid this gets joined
to.

And it is **systematic**. Every position derived from this DEM moves the same
way, so nothing looks inconsistent — two datasets built this way agree with each
other perfectly and disagree with the ground.

## The clean twin

[`c024-pixel-is-area`](../../clean/c024-pixel-is-area/) is the same surface, the
same tie point, the same spacing, the same lowest node, and one different tag.
Its correct answer is **412105** — precisely the number that is wrong here.

That pairing is the point. A system that has learned about pixel-is-point and
now subtracts half a cell everywhere passes this trap and fails the twin. A
system that never heard of it passes the twin and fails this. Only one that
reads the tag answers both.

## How it was found

Writing a contour operation. The engine placed every contour half a cell from
where the elevation it named actually occurred, which was noticed by checking
the output against the input rather than by reading the documentation — sample
the DEM where the line says it is, and the elevation has to match. Asking how
far that generalised produced the raster-type key, and a convention that is
declared in the file, reported faithfully by every library, and honoured by none
of the coordinate helpers built on top of them.
