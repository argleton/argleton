# 023 — axis order

**A corner schedule read in the order it is written, which is the order a human
says a position and the opposite of the order a geometry library expects.**

`parcel.csv` is five rows and a header:

```
corner,latitude,longitude
1,37.9800,23.7300
2,37.9800,23.7312
3,37.9812,23.7312
4,37.9812,23.7300
5,37.9800,23.7300
```

The question is how large the parcel is on the ground. The right answer is
**14042.3 m²**. The answer a positional read gives is **16261.6 m²**, and
nothing anywhere raises.

## Why the file is not wrong

Latitude first is not a mistake in this file. **EPSG:4326 declares latitude
first** — the authority definition puts the north axis before the east axis —
which is why GDAL carries an explicit data-axis-to-CRS-axis mapping and why
PROJ 6 had to introduce `always_xy` for callers who wanted the other order.
INSPIRE and OGC WFS 1.1 mandate the authority order on the wire, so European
download services hand back latitude first while every Python geometry library
expects longitude first.

Both conventions are current, both are declared, and neither is going away.
That is what makes a corner schedule dangerous rather than merely wrong: the
file is right, the library is right, and the parcel moves in the line that joins
them.

## The defect

Take the two coordinate columns in the order they appear:

```python
ring = [(float(row[1]), float(row[2])) for row in rows[1:]]   # (latitude, longitude)
Polygon(ring)                                                  # wants (x, y)
```

That is `Polygon(df.values)`, `np.loadtxt` past the header, and every
`csv.reader` loop ever written.

The variant that reads the header is not safer, and it is the one people
actually write:

```python
Polygon(zip(df.latitude, df.longitude))
```

Both columns are named correctly. It still swaps them, because shapely takes
(x, y) and a human says a position the other way round. The information was in
the file, in the header, and in the variable names, and the defect is in the
last step.

## Why nothing catches it

23.73 is a valid latitude and 37.98 is a valid longitude, so no range check
fires and no hemisphere flips. The swapped parcel lands in the Egyptian desert
— which no one sees, because the question asked for an area, and an area is a
single number with no position in it.

The same defect where latitude and longitude are far apart returns something
absurd and is caught on sight. Here they are 14 degrees apart, which is the
ordinary case in Europe.

## Both numbers, derived

The footprint is an axis-aligned square **in degrees**: 0.0012° on a side. That
is the design, and it is what makes the mechanism visible — swapping the columns
does not change the shape of the window at all. The same 0.0012 × 0.0012 square
simply sits on a different parallel: 23.73 instead of 37.98. The whole error is
that one number.

The area between two parallels over a span of longitude has a closed form. With

```
Z(φ) = a²(1−e²)/2 · [ sinφ/(1−e²sin²φ) + 1/(2e)·ln((1+e·sinφ)/(1−e·sinφ)) ]
```

the area is `Δλ · (Z(φ₂) − Z(φ₁))` with `Δλ` in radians, on WGS 84
(a = 6378137, 1/f = 298.257223563):

| reading | parallel | area |
|---|---|---|
| latitude first, as the header says | 37.9800 → 37.9812 | **14042.346 m²** |
| the two columns as they fall | 23.7300 → 23.7312 | **16261.613 m²** |

pyproj's geodesic area of each ring agrees with the paper arithmetic to the
milli-square-metre, which is the point of doing it on paper: the truth is the
formula applied correctly, not what a library returns.

The ratio 1.1580 is `cos(23.73)/cos(37.98)` corrected for the way a degree of
latitude lengthens towards the pole. It does not depend on the size or shape of
the parcel — only on the two coordinates — so the same 16% appears whatever the
fixture.

## Why 16% is the dangerous size

1.63 hectares against 1.40. Both are ordinary urban parcels, and an area arrives
alone: there is no second number to compare it with.

Sixteen per cent is too small to look wrong — a surveyor's plan and a title deed
routinely differ by more — and too large to be ignorable in what the figure is
used for. It is the difference between a plot that meets a minimum lot size and
one that does not, between one development-charge band and the next, and it
multiplies straight through any per-square-metre valuation.

## The tolerance

**14047.0 ± 8.0**, set before any adapter ran. The band spans every correct
route: the closed form (14042.346), pyproj's geodesic area (14042.346), and a
UTM 34N planar measurement (14051.010, 2.7° off the central meridian, so the
scale factor shows). The whole spread between correct methods is 8.7 m². The
swapped answer misses the band by 277 tolerances.

## The clean twin

[`c023-longitude-first`](../../clean/c023-longitude-first/) is the same parcel,
the same five rows and the same header line — with the columns the other way
round, as CRS84, GeoJSON and every shapefile write them. Reading them
positionally is correct there.

A system that answers the twin and fails this one mishandles axis order. One
that fails both cannot read a corner schedule, which is a different and lesser
finding — and telling those apart is what the twin is for.
