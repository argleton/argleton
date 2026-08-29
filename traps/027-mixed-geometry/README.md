# 027 — mixed geometry

**A layer of pipes that also contains the treatment plant, and a total length
that includes its fence line.**

`network.gpkg` holds six assets in one layer: five pipe runs and one plant
footprint. The question is how many metres of pipe there are.

The right answer is **2000**. The three-line composition answers **3000**.

## Why the file is not wrong

GeoPackage allows a features table to declare its geometry type as GEOMETRY,
meaning any type, and readers honour it — GDAL reports the layer as Unknown and
hands back the rows. GeoJSON places no restriction on a FeatureCollection
either.

The ESRI shapefile does the opposite: one geometry type per file, enforced. For
thirty years that format did the filtering that code now has to do, which is why
a layer like this appears exactly when data is converted *out* of shapefiles and
the split the old format imposed is merged away.

## The defect

```python
gpd.read_file("network.gpkg", layer="assets").length.sum()   # 3000.0
```

`length` on a polygon is its perimeter. The plant is 300 × 200, so it
contributes 1000 m of "pipe" that is actually a fence line. Shapely is right to
answer — the length of a closed ring is a real quantity — and PostGIS makes the
opposite choice, returning 0 from `ST_Length` for a polygon and keeping
`ST_Perimeter` separate. Two defensible conventions, and the one that returns a
number is the one that adds silently into a sum.

## Why 3000 is plausible

Three kilometres of pipe instead of two. Both are ordinary figures for a works
site, and 3000 is if anything the more ordinary-looking: round, no decimal,
comfortably in range.

**Every individual asset is still correct**, which defeats the usual check. Open
the attribute table and P-01 is 600 m, P-02 is 400 m, each one right. The error
is not in any row, it is in which rows were added up, so a spot check of the
data confirms the data.

And the size of the error is set by the shape of the plant, not by anything
about the pipes, so it does not scale with the network and cannot be caught as a
percentage. A bigger site with the same plant is out by the same 1000 m, which
looks like less.

## The clean twin

[`c027-lines-only`](../../clean/c027-lines-only/) is the same five pipe runs in a
layer that holds only lines — the arrangement the shapefile era enforced — where
summing every geometry's length is exactly right.

One layer in each half, deliberately. A second layer in the twin would have
dragged in the ambiguous-container question, which is real and is a different
family, and the pair has to isolate the geometry types and nothing else.
