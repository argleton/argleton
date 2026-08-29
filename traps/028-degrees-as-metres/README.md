# 028 — geographic CRS

**A field delivered in degrees, and the one conversion factor everybody knows.**

`field.geojson` is a 9 ha maize parcel in the Po valley, in WGS 84 as GeoJSON
requires. The question is how large it is on the ground.

The right answer is **89 900 m²**. The conversion everybody reaches for gives
**127 143** — 41% too much, and the ratio is √2 exactly.

## Why the file is not wrong

RFC 7946 §4 fixes GeoJSON's coordinate reference system to WGS 84 and removes
the ability to name another, so the great majority of open vector data, web APIs
and hand-drawn polygons arrive in degrees. This one is ordinary in every
respect.

What the file does not carry is a length. Shapely computes area in the
coordinates' own units, by design, because nothing else can know what they are —
so this parcel's area is 1.026 × 10⁻⁵ **square degrees**, and it has to be
converted.

## The defect

```python
field.area * 111320 ** 2        # 127143.381
```

111 320 m is one degree at the equator: the most copied number in this field.
It is close enough for a degree of *latitude* anywhere, and right for a degree
of *longitude* only on the equator, because the meridians converge — a degree of
longitude is 111320·cos(φ). At 45° it has shrunk to 0.7071 of its equatorial
length, so the area comes back 1/cos(45°) = **1.4142** times too large.

## The warning is part of the trap

GeoPandas does warn here:

```
UserWarning: Geometry is in a geographic CRS. Results from 'area' are likely
incorrect. Use 'GeoSeries.to_crs()' to re-project geometries to a projected CRS
before this operation.
```

It says the number is likely incorrect, which is true, and it does not say by
how much or in which direction. It fires on *every* area call over a geographic
CRS, including the ones where the caller is about to convert correctly, so it is
routinely filtered out as noise.

And a caller who reads it and acts on it has been told to fix the units — which
is precisely what multiplying by 111 320² is an attempt to do. The warning does
not defend against this trap; it points at it.

## Why 41% is the dangerous size

12.7 hectares instead of 8.99. Both are ordinary fields, the shape is unchanged,
the position is unchanged, and an area arrives alone with no second figure
beside it.

Forty-one per cent is far too small to be absurd — two surveys of the same field
can differ by more than a percent, and nobody has a prior tight enough to reject
12.7 ha for a parcel they have not walked. It is far too large to be ignorable
in what the figure is used for: a subsidy per hectare, a yield per hectare that
now looks 30% worse, an application rate, a lease. Every one of those is a
multiplication.

And the error is a smooth function of latitude, so it is invisible across a
dataset: every parcel in the region is wrong by the same 1.41, totals stay
consistent, ratios between parcels are exactly right. Only a measurement from
outside the data would show it.

## The clean twin

[`c028-projected-field`](../../clean/c028-projected-field/) is the same four
corners in EPSG:32632, whose unit is the metre — nothing to convert, and the
composition that fails here is right there.

It is a GeoPackage rather than a GeoJSON on purpose: GeoJSON is defined on
WGS 84, and a projected GeoJSON would be the wrong kind of unusual. The twin also
catches the over-correction — a system that has learned to distrust degrees and
now applies a cosine everywhere would divide this parcel by 0.7071 and be wrong
by the same 41% the other way.
