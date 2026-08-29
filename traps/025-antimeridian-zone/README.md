# 025 — antimeridian

**A survey zone split at the 180th meridian exactly as the standard says to
split it, whose bounding box is the entire planet.**

`zone.geojson` is two degrees of longitude by one of latitude, in Fijian waters:
179°E to 179°W, 17.5°S to 16.5°S. It is 213 km across. `ships.csv` holds twelve
vessel positions. The question is how many are inside the zone.

The right answer is **5**. The composition almost everyone writes says **9**.
Nothing raises.

## Why the file is not wrong

RFC 7946 §3.1.9 is explicit: a geometry crossing the antimeridian **should** be
split into two parts at it, and every coordinate must stay within [-180, 180].
So the zone is a MultiPolygon of exactly two rectangles — one from 179°E to 180°,
one from -180° to 179°W — and there is no ambiguity anywhere in the file about
which two degrees are meant.

The file is standard-conformant. The geometry is valid. Every coordinate is in
range.

## The defect

```python
zone = gpd.read_file("zone.geojson")
minx, miny, maxx, maxy = zone.total_bounds     # (-180.0, -17.5, 180.0, -16.5)
inside = ships.cx[minx:maxx, miny:maxy]        # 9
```

The two parts touch the range limits from opposite ends, so the bounds computed
from their coordinates are a band right around the world. Four vessels at the
same latitude — in the Banda Sea, the South Atlantic, the Coral Sea and off the
coast of Chile — pass the filter.

`cx` is the coordinate-slice idiom out of the GeoPandas documentation, and
narrowing to the bounds of the study area before doing anything expensive is
ordinary practice: it is how a tile is requested, how a `WHERE` clause on
min/max columns is written, how a raster is windowed.

**The two halves of the standard do not compose.** §3.1.9 says to split the
geometry; §5.2 says a bounding box whose western value exceeds its eastern one
is the one that crosses the antimeridian. A geometry split correctly per the
first has bounds that cannot be expressed in the form the second describes, and
nothing in a general-purpose geometry library computes anything else — shapely,
GEOS and PostGIS all work in a plane where longitude is an ordinary number.

## Why nine is plausible

Nine vessels instead of five. Both are ordinary numbers for a survey zone, there
is no second figure to compare against, and a count arrives with no unit and no
magnitude to sanity-check.

A count is the worst kind of answer to be wrong about, because the usual
defences do not apply. An area 16% high can be checked against a plan; a
coordinate can be plotted. Nine is just nine — and if the next step is a
density, a fee per vessel, or a decision about capacity, the error propagates as
a clean multiplication by 1.8.

The four extra vessels are not obviously extra either. A listing shows four
names and four plausible coordinates at the right latitude. Only reading their
longitudes carefully, or plotting them, shows that one is in the Atlantic.

## Three vessels that make it a number instead of a shape

Kadavu South, Wallis and Minerva sit near the antimeridian but outside the
latitude band, so the bounding box excludes them — correctly. Without them the
wrong answer would be *every vessel in the file*, which somebody might notice.

## The clean twin

[`c025-single-hemisphere-zone`](../../clean/c025-single-hemisphere-zone/) is the
same question with the zone moved ten degrees west, to 169°E–171°E. The same
twelve vessels in the same arrangement, the same answer of 5 — and there the
bounding box **is** the zone, so the filter that fails here is exactly right.

The pair does two jobs. It separates "mishandles the antimeridian" from "cannot
count points in a polygon", which are different findings. And it catches the
over-correction: a system that has learned to distrust bounding boxes near the
line still has to answer an ordinary rectangle.

## One more thing, for anyone reaching for a centroid

```python
zone.union_all().centroid        # POINT (0 -17)
```

The centre of this Fijian survey zone, computed by the most ordinary call there
is, is in the Gulf of Guinea. That one is not the probe — it is loud enough that
a map would show it — but it is the same arithmetic, and it is worth knowing
which calls carry it.
