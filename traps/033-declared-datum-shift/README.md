# 033 — A declared Helmert is not a ballpark

## The file

One station at 8.952333333 east, 45.5 north on Monte Mario. The CRS declares the
full Position Vector transformation: translations −104.1, −49.1, −9.9 m,
rotations 0.971, −2.917, 0.714 arc-seconds, scale −11.68 ppm, on International
1924.

## The right answer, on paper

Latitude **45.500669074**. Geodetic to geocentric on International 1924, the
Position Vector formula above, then geocentric to geodetic on WGS 84 gives that
value. This is the same published operation and closed-form arithmetic as trap
021, but the operation is declared by the CRS itself.

## The failure

PROJ reports `accuracy = -1` for this declared operation, just as it does for a
ballpark. Treating the number alone as the verdict either returns the unchanged
45.5 or refuses despite a valid transformation. The pipeline contains
`+proj=helmert` and returns 45.500669073852286, so both responses lose or reject
information that was present in the file.

## Why it is admitted

The error is only 74 m and the output CRS and longitude still look right. A false
ballpark refusal is also plausible: it sounds like careful handling, but rejects
a transformation that works and has all seven parameters declared.

## The clean twin

`c033-zero-datum-shift` declares the same kind of operation with every parameter
zero. It isolates the rule: negative accuracy must not condemn either a declared
Helmert or a declared no-op.
