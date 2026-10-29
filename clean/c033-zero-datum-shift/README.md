# c033 — A declared zero shift

One station at 8.952333333 east, 45.5 north on International 1924, with all three
`+towgs84` translation parameters zero.

The correct WGS 84 latitude is **45.499178019**. No datum translation is needed,
but converting geodetic coordinates between International 1924 and WGS 84 still
changes the latitude. A zero shift does not mean identical ellipsoids.

PROJ removes the zero operation and can choose a ballpark fallback. That fallback
performs the required ellipsoid conversion correctly, so refusing it merely
because its accuracy is -1 would turn a clean task into a failure.
