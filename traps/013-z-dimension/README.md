# 013 — The pipe measured in plan view

## The file

`pipeline.gpkg` holds one pipe running from (0, 0, 0) to (400, 0, 300) in
local metres: 400 m across the ground and 300 m up.

## The right answer, on paper

√(400² + 300²) = **500 m** exactly — a 3-4-5 triangle, chosen so the answer
has no decimals to argue about.

## The wrong answer

Take the length: **400 m**.

In PostGIS the error is literally the name of the function — `ST_Length` is
2D, `ST_3DLength` is 3D — and in Shapely `.length` ignores Z without saying
so. The geometry carries its elevations the whole time; the measurement
drops them.

## Why it is admitted

400 m of pipe is an ordinary quantity, and 20% short is invisible to every
downstream check: it becomes a bill of materials, a cost estimate, a
procurement order. Nothing in the number says a dimension was dropped.

## The clean twin

[c013-flat-pipeline](../../clean/c013-flat-pipeline/) is the same pipe on flat ground: 3D and 2D agree at 500 m, so a system
that ignores Z answers it correctly.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | 400.0 | silent error |
| MapSmith | 500.0 | correct |

MapSmith returned `unsupported` the first time this ran — it had no length
operation at all. `measure_length(method='3d')` is the answer, and a flat
measurement on 3D geometry now comes back with the 3D length beside it.
