# 021 — The transformation the one-liner picks, and the datum it skips

## The file

One station in `station.gpkg`, stored on the Monte Mario datum with the **Rome**
prime meridian (EPSG:4806), at longitude −3.5 and latitude 45.5. Round numbers,
and unmistakably Rome-meridian ones: −3.5 east of Monte Mario is 8.952333333
east of Greenwich, in Piedmont.

Nothing about the file is unusual. Monte Mario is the datum of Italian cadastral
and historic mapping, and both EPSG variants of it are in daily use: 4265 with
the Greenwich meridian, 4806 with the Rome one.

## The right answer, on paper

Latitude **45.500669074** in WGS 84.

Going from Monte Mario to WGS 84 is the published EPSG operation *Monte Mario to
WGS 84 (4)*, a Position Vector 7-parameter transformation. Its values are in the
EPSG dataset and can be read out of any PROJ install:

| | |
|---|---|
| translations | −104.1, −49.1, −9.9 m |
| rotations | 0.971, −2.917, 0.714 arc-seconds |
| scale | −11.68 ppm |
| source ellipsoid | International 1924 (a = 6378388.0, 1/f = 297.0) |
| stated accuracy | 4 m |

Applied by hand — geodetic to geocentric on International 1924, the Position
Vector formula, geocentric to geodetic on WGS 84 — that gives 45.500669074.

**The arithmetic was done independently and then checked against PROJ applying
the same published operation: they agree to 0.000 m at Milan, Rome and Naples.**
That check is the point. The truth here is the published transformation applied
correctly, and *not* whatever a library chooses to do — because what it chooses
is the thing under examination.

## The wrong answer

**45.5** — the input latitude, unchanged.

`Transformer.from_crs(CRS(4806), CRS(4326))`, the one line every caller writes,
selects a **ballpark** transformation. A ballpark is PROJ declaring that it will
treat the two datums as equivalent: no shift is applied. The Rome meridian is
still handled correctly, so the longitude looks right to within 27 m and the
latitude comes back exactly as it went in.

The operation's accuracy is reported as `-1`. Nothing is raised, nothing is
logged, and the only way to see it is to ask
`get_last_used_operation().accuracy` after the fact.

## Why it is admitted

45.5 is a plausible latitude in Piedmont, and it is 74 m from where the station
is. Seventy-four metres puts a station across a road or in the next field —
enough to change which parcel it falls in, which municipality it is attributed
to, and which side of a boundary it sits on. Not enough for anything downstream
to question. And the longitude, which most eyes check first, is right.

## The clean twin

`c021-greenwich-variant`: **the same physical point, the same datum, the same
truth**, declared as EPSG:4265 instead of EPSG:4806.

That is the whole isolation. On the Greenwich variant PROJ selects the 4 m
operation and lands on 45.500669074 to 0.000 m. So nobody can answer this trap
with *datum transformations are hard*: the difficulty is not the variable. The
variable is which variant the file declares.

A non-ballpark route exists for 4806 too — `TransformerGroup` lists a 44 m
operation first. The one-liner takes the other one.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | 45.5 | **silent error**, and the predicted one |
| GeoPandas 1.1 + Shapely 2 (`to_crs`) | 45.5 | **silent error** |
| MapSmith 0.2.2+ | 45.5 | **silent error** |

Every system measured so far falls in, and they fall in at the same place: all
three end up at `Transformer.from_crs`. On this probe there is no gap between
the careless composition and the ordinary one, because the ordinary one is a
single line.

MapSmith fails this exactly as the naive composition does, and its manifest
records a successful reprojection: `crs_matches` passes, because the output CRS
*is* EPSG:4326. Seven green checks beside a number that is 74 m wrong — the same
finding this suite made about MapSmith on 2026-08-23, on a different operation.

No system passes it yet, so what it takes to pass is stated here as a
specification rather than reported as a score — and being precise about it is
what decides whether the trap is fair: read
`get_last_used_operation().accuracy`, and if it is negative, take the first
operation from `TransformerGroup` that states one. Fourteen lines. **No manifest
and no provenance format is required** — any engine can do it, which is why this
trap is not a vendor benchmark.
