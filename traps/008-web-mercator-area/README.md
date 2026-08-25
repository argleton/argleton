# 008 — Metres of map read as metres of ground

## The file

`parcel.gpkg` holds one land parcel in **EPSG:3857** (Web Mercator), an exact
120 × 100 rectangle in the map plane at the latitude of Rome. Everything about
the file is honest: valid geometry, declared CRS, and — unlike the
feet-as-metres trap — the CRS's unit really **is** the metre. What the unit
does not say is metres *of what*.

## The right answer, on paper

EPSG:3857 is defined on a sphere of radius R = 6378137 m, and on that sphere
the ground area of a map rectangle has a closed form:

```
width × R × (tanh(y₂/R) − tanh(y₁/R))
  = 120 × 6378137 × (tanh(5140100/6378137) − tanh(5140000/6378137))
  = 6656.30 m²        (equivalently: 12000 × cos²(41.8601°))
```

On the WGS84 ellipsoid, the geodesic area of the same footprint is
**6651.34 m²** (0.075% below the sphere); a UTM 33N planar measurement gives
**6653.65 m²**. Every correct method lands in a 5 m² band; the truth is pinned
at **6654 ± 8**, which spans them all. The map-plane answer misses the band by
668 tolerances.

## The wrong answer

Read the file, sum `.area`, report it: **12000 m²** — 1.80× the ground.

Web Mercator is conformal, not equal-area. At latitude φ its linear scale is
1/cos φ (1.34 at 41.86°N), so every planar area is 1/cos²φ times the ground it
covers. The shoelace over the coordinates is arithmetically exact — in the
wrong plane. No exception, no warning: the CRS declared metres and delivered
metres, of map.

## Why it is admitted

Both numbers are ordinary parcels — 1.2 hectares against 0.67 — and nothing in
any single number betrays the smooth, latitude-dependent factor between them.
EPSG:3857 is the CRS every web-exported dataset ships in; the EPSG registry
itself remarks the projection is "not a recognised geodetic system", and a 2014
NGA advisory bans it for mission use over errors "of up to 40,000 meters".
This is feet-as-metres one step deeper: there the unit label lied; here the
label is true and the plane it measures is not the ground.

## The clean twin

[c008-equal-area-crs](../../clean/c008-equal-area-crs/) asks the same question
about the same kind of file in **EPSG:3035** (Lambert Azimuthal Equal-Area),
where the planar shoelace *is* the ground area — 10000 m² exactly, by
construction. The composition that falls into this trap answers the twin
correctly, which is what separates "mishandles distortion" from "cannot
measure an area".
