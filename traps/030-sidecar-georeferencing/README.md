# 030 — Two georeferencings in one dataset, and no answer says which it used

A raster and the sidecar beside it disagree about where the data is and how big
its cells are. Reading the file gives one answer, reading it with one
environment variable set gives another, and **neither answer says which one it
was**.

| | cell | origin | area |
|---|---|---|---|
| what the GeoTIFF declares | 10 m | 500000, 5030000 | **40 000 m²** |
| what the `.aux.xml` declares | 20 m | 600000, 5040000 | **160 000 m²** |

Four times the area and a hundred kilometres, from one file and one line of
code.

## Why this is not a bug report

GDAL's precedence for GeoTIFF is documented: `GDAL_GEOREF_SOURCES` defaults to
`PAM,INTERNAL,TABFILE,WORLDFILE,NONE`, so a `.aux.xml` beats the file's own
tags. That is deliberate and it has to be — a sidecar is the mechanism by which
somebody corrects georeferencing they know to be wrong, and an override that
loses to the thing it overrides is not an override.

So both numbers are the library behaving exactly as written down. There is
nothing upstream to fix. What is missing is not correctness: it is the sentence
saying which of the two sources produced the number.

That is why this probe exists in a suite about silent errors rather than in a
tracker. **The correct answer is not a number, it is this number with this
configuration.**

## Why the wrong answer is invisible

160 000 m² is sixteen hectares — an ordinary elevation tile. Every internal
check agrees with every other: the cell size, the row count and the area are
mutually consistent, because all three come from the same sidecar. Nothing is
absurd, nothing is negative, nothing is round in a way that invites suspicion.

And a factor of four is not a factor a reader recognises. It is what you get
from cells twice as wide, and nobody knows the cells are twice as wide.

The area is the number this probe grades, but the position is the part that
travels: an area is reported once, while an origin propagates into every clip,
every spatial join and every map that follows.

## The truth, on paper

The GeoTIFF's geotransform declares 10 m cells. Twenty cells is 200 m a side:

    200 m × 200 m = 40 000 m²

Both numbers are written as constants in `build.py`, so the truth does not
depend on reading the fixture back.

## What this probe does not measure

Worth stating, because a probe that oversells itself is the same failure it
grades.

**A system whose environment already disables the sidecar passes for a reason
that has nothing to do with noticing.** `GDAL_PAM_ENABLED=NO` appears in several
container images, and a system running under one returns 40 000 without ever
knowing there was a choice. Argleton grades outcomes, not mechanisms, and this
is one of the places where that shows. The `refusal` clause recognises a system
that *says* it found two sources, which is the only signal in reach here.

**It grades one number, not the record.** A producer that writes which
georeferencing source it read — the `environment` field of the manifest
specification, section 3.8 — is doing the thing this probe is about, and the
scalar cannot see it. That gap is the reason the specification and this probe
are published together: the probe shows the failure exists, the field is what
answers it.

## The clean twin

`clean/c030-single-georeferencing` is the same raster with no sidecar. One
georeferencing, one answer, whatever the environment says. Without it, a rate on
this family could not tell "misreads a dataset with two georeferencings" from
"cannot measure a raster".
