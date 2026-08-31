# Families, and what is actually covered

Twenty-seven families are on the list — twelve planned at the start, fifteen added
from reproductions and from a survey of what the archives and the libraries
themselves warn about. **Twenty-eight are implemented.** That is all of them, as of 2026-08-31. This page exists so that
a number from Argleton can never be read as broader than it is: a low
silent-error rate means a system did not fail silently *on these probes*, and
this is the list of what that sentence covers.

Every result also carries a `by_family` breakdown, so one family with ten probes
cannot read as ten independent findings.

## Implemented

| # | Family | Probes | The wrong answer | Why it survives |
|---|---|---|---|---|
| 1 | `raster-encoding` | [001](../traps/001-tiff-predictor/) + [c001](../clean/c001-raster-mean/) | mean 36.09 instead of 1093.0 | The differenced grid still renders as terrain; hillshade over it still looks like hillshade |
| 3 | `linear-units` | [002](../traps/002-feet-as-metres/) + [c002](../clean/c002-projected-area/) | 100 ha instead of 9.29 ha | Both are ordinary parcels; they differ by 3.28², a factor nothing downstream questions |
| 4 | `mismatched-crs` | [004](../traps/004-mismatched-crs-join/) + [c004](../clean/c004-points-in-polygon/) | 0 points in the zone instead of 12 | An empty spatial result is a finding, not an error — "no wells inside the zone" reads as good news, and nothing downstream questions an empty join |
| 25 | `positional-pairing` | [022](../traps/022-thiessen-pairing/) + [c022](../clean/c022-two-gauges/) | 554 mm of rainfall instead of 268 | The cells are all valid, they tile the extent, the count is right and the map is a Thiessen diagram — only the pairing between a cell and the row it carries is wrong, and the set of cells is identical either way, so nothing about the geometry can show it |
| 26 | `axis-order` | [023](../traps/023-axis-order/) + [c023](../clean/c023-longitude-first/) | 16261 m² instead of 14042 | EPSG:4326 declares latitude first and every geometry library expects longitude first — both conventions are current, both are declared, and a corner schedule read in the order it is written puts the parcel 14 degrees away without leaving the valid range for either coordinate |
| 24 | `datum-ballpark` | [021](../traps/021-ballpark-datum/) + [c021](../clean/c021-greenwich-variant/) | latitude 45.5 instead of 45.500669074, which is 74 m | The longitude is right, the output CRS is right, and the transformation the library chose reports its accuracy as -1 only if you ask after the fact |
| 6 | `nodata` | [003](../traps/003-nodata-in-statistics/) + [c003](../clean/c003-raster-mean-nodata/) | mean 945.005 instead of 1000.0 | 5.5% out — too small to question, too large to ignore in a volume or a flood level |
| 7 | `invalid-geometry` | [005](../traps/005-bowtie-area/) + [c005](../clean/c005-polygon-area/) | 2400 m² instead of 5100 m² | The signed-shoelace artifact of a self-crossing ring: no exception, no warning, and both numbers are ordinary parcels |
| 11 | `ambiguous-layer` | [006](../traps/006-default-layer/) + [c006](../clean/c006-named-layer/) | 4 wells instead of 31 | The container's default layer answers a question nobody asked; the only signal is a stderr warning attached to no result |
| 12 | `implicit-parameter-units` | [007](../traps/007-buffer-in-degrees/) + [c007](../clean/c007-distance-in-metres/) | 24 wells "within 500 m" instead of 3 | The buffer runs in the layer's units (degrees) and swallows the map; the count it returns is an ordinary number for a dense wellfield |
| 13 | `projection-distortion` | [008](../traps/008-web-mercator-area/) + [c008](../clean/c008-equal-area-crs/) | 12000 m² instead of 6654 m² | The CRS declares metres and delivers them — metres of map. The factor is cos²(latitude): smooth, invisible in any single number, and both readings are ordinary parcels |
| 14 | `categorical-resampling` | [009](../traps/009-resampled-classes/) + [c009](../clean/c009-native-resolution-classes/) | 900 m² of a class that is not in the file | The interpolated value between two class codes is another valid class code: averaging forest (1) and water (3) yields urban (2), on the shoreline where a town would actually be |
| 15 | `radiometric-scale-offset` | [010](../traps/010-scale-offset/) + [c010](../clean/c010-physical-values/) | NDVI 0.25 instead of 0.3333 | Without an offset the scale cancels in the ratio, so ignoring both was right for years — Sentinel-2 added a non-zero offset in January 2022 and the same code quietly stopped being right |
| 16 | `polygon-holes` | [011](../traps/011-polygon-holes/) + [c011](../clean/c011-solid-parcel/) | 11600 m² instead of 8400 | The courtyard is added instead of subtracted, and 1.16 ha against 0.84 ha are both ordinary parcels |
| 17 | `double-counting` | [012](../traps/012-double-counting/) + [c012](../clean/c012-disjoint-concessions/), [019](../traps/019-partial-overlap/) + [c019](../clean/c019-fully-contained/) | 20000 m² instead of 16000; 30000 m² of "flooded" farmland instead of 9000 | Summing areas is right whenever nothing overlaps, which is most of the time; and selecting the parcels that intersect quietly changes the unit from the square metre to the parcel |
| 18 | `z-dimension` | [013](../traps/013-z-dimension/) + [c013](../clean/c013-flat-pipeline/) | 400 m of pipe instead of 500 | The elevations are in the file the whole time; the measurement drops them, and in PostGIS the difference is the name of the function |
| 19 | `centroid-outside` | [014](../traps/014-centroid-outside/) + [c014](../clean/c014-convex-parcel/) | the wrong district | The centroid of an L-shaped parcel falls in the notch, on no part of the parcel — and a district name carries no magnitude to sanity-check |
| 20 | `boundary-semantics` | [015](../traps/015-boundary-semantics/) + [c015](../clean/c015-wells-off-the-seam/) | 8 wells of 12 | `within` excludes the boundary, so points on a shared edge belong to neither district and vanish from a partition that covers them |
| 21 | `coordinate-parsing` | [016](../traps/016-coordinate-parsing/) + [c016](../clean/c016-decimal-degrees/) | 41.5324 instead of 41.89 | Both are latitudes in central Italy, 40 km apart: close enough that a map looks right, far enough that every distance is wrong |
| 22 | `aggregation-weighting` | [017](../traps/017-aggregation-weighting/) + [c017](../clean/c017-equal-populations/) | 13.67% unemployment instead of 1.38% | Averaging rates treats a town of a thousand as equal to a city of a hundred thousand, and both figures describe a plausible region |
| 23 | `tabular-join` | [018](../traps/018-join-key-typing/) + [c018](../clean/c018-plain-keys/), [020](../traps/020-join-cardinality/) + [c020](../clean/c020-one-owner-each/) | 62000 people instead of 100000; 65000 m² of land instead of 50000 | A CSV reader turns "001" into 1 and four municipalities leave the join silently; a one-to-many join multiplies the land and the sum counts it twice |

| 9 | `antimeridian` | [025](../traps/025-antimeridian-zone/) + [c025](../clean/c025-single-hemisphere-zone/) | 9 vessels in the zone instead of 5 | The zone is split at 180 exactly as RFC 7946 3.1.9 says to split it, so its bounds are (-180, ..., 180, ...) — a band round the planet — and the standard's own inverted-bbox convention has no representation in any planar geometry library. A count arrives with no unit and no magnitude to check |
| 2 | `geographic-crs` | [028](../traps/028-degrees-as-metres/) + [c028](../clean/c028-projected-field/) | 12.7 ha instead of 8.99 | GeoJSON is defined on WGS 84, so area comes back in square degrees and has to be converted — and the factor everybody knows, 111320, is right for latitude and right for longitude only at the equator. The library's own warning points at the conversion that is the trap |
| 5 | `empty-result` | [029](../traps/029-difference-order/) + [c029](../clean/c029-coincident-boundaries/) | 0 m² workable instead of 160000 | Difference is not commutative and both orders are valid questions. An empty result reads as a finding rather than a failure — *no part of the licence lies outside the reserve* is a sentence a board acts on |
| 8 | `mixed-geometry` | [027](../traps/027-mixed-geometry/) + [c027](../clean/c027-lines-only/) | 3000 m of pipe instead of 2000 | A GeoPackage layer may hold more than one geometry type, and `length` on a polygon is its perimeter. Every individual asset is still correct, so a spot check of the data confirms the data |
| 10 | `raster-affine` | [026](../traps/026-south-up-grid/) + [c026](../clean/c026-north-up-grid/) | 45° of slope instead of 5.7° | The fifth number of a geotransform may be positive, and an engine that cannot express that discards the georeferencing — cells of 1 m at the origin. A slope is a rise over a run, and every cell is wrong by the same factor, so the map has the right shape and the wrong legend |
| 27 | `grid-registration` | [024](../traps/024-pixel-is-point/) + [c024](../clean/c024-pixel-is-area/) | easting 412105 instead of 412090 — and 412120 from a second engine | The file says `AREA_OR_POINT=Point` and the library hands you the tag from the same object whose coordinate helper ignores it. Half a cell is 15 m on a 30 m DEM: smaller than the GPS a crew walks in with, larger than every tolerance afterwards, and systematic, so the whole analysis stays internally consistent |
| 28 | `hidden-configuration` | [030](../traps/030-sidecar-georeferencing/) + [c030](../clean/c030-single-georeferencing/) | 160000 m2 instead of 40000, and an origin 100 km away | A `.aux.xml` beside a GeoTIFF georeferences it too, and GDAL prefers the sidecar by documented design because that is how a user overrides georeferencing they know to be wrong. Both readings are the library behaving as written; neither answer says which one it used, and one environment variable switches between them |

Families 13 to 23 were not in the original design. 13 came from building family
3 (`linear-units`), on noticing that a unit label can be *true* while the plane
it measures is not the ground; 14 from writing a resampling operation and asking
what its output alphabet is allowed to contain; 15 to 23 from a survey of what
the archives, the libraries and their own documentation warn about — 47 candidate
mechanisms, of which these are the ones whose truth is arithmetic.

Family 9 was in the original twelve and took until the twenty-fifth trap to
build, which is worth saying plainly: it is famous, and being famous is not the
same as being easy to plant. Every obvious formulation of it is LOUD — an extent
that spans 358 degrees, a distance of 40 000 km, a centroid in the Atlantic — and
a probe whose typical failure is absurd belongs in an ordinary test suite,
because something already catches it. What took the time was finding the quiet
one: a count, where 9 and 5 are equally ordinary numbers.

Family 27 arrived differently again, and the way it arrived is the argument for
building instruments before opinions. It came out of writing a contour operation
for MapSmith: the engine placed every contour half a cell from where the
elevation it named actually occurs, which was found by checking the output
against the input rather than by reading the documentation. Asking how far that
generalised produced the GeoTIFF raster-type key, a convention that is declared
in the file, reported faithfully by every library, and honoured by none of the
coordinate helpers built on top of them.

Two of them are not geometric at all (`aggregation-weighting`, `tabular-join`),
and that is deliberate: an agent joins attribute tables and aggregates columns
far more often than it reprojects, and no suite was measuring that.

All were added under the same four conditions as the rest — which is what the
closing section of this page asks of anyone.

## Planned

Numbered as in the original design, so the gaps stay visible rather than being
renumbered away.

| # | Family | The error |
|---|---|---|
| 2 | `geographic-crs` | A metric operation on a geographic CRS with no reprojection — degrees treated as a length |
| 5 | `empty-result` | An intersection that is empty because of a defect, told apart from one that is legitimately empty |
| 8 | `mixed-geometry` | A layer holding more than one geometry type |
| 9 | `antimeridian` | Extents that invert across the 180th meridian or at the poles |
| 10 | `raster-affine` | Flipped axes or a non-standard affine transform |

Three more came out of a 2026 survey of what the industry is shipping now, and
matter because they are wrong on the asset class everyone is adopting:

| Family | The error |
|---|---|
| `embedding-dequantisation` | int8 satellite embeddings dequantised linearly when the encoding is `sign(q)·(\|q\|/127.5)²` |
| `utm-zone-edge` | The wrong UTM zone chosen at a tile boundary |
| `temporal-aggregation` | An annual composite used for a phenomenon that is sub-annual |
| `time-reference` | A timestamp read in the wrong zone, or GPS time taken for UTC (18 s apart) |
| `ring-orientation` | A polygon wound the wrong way, which on an S2-based engine becomes the rest of the world |
| `hidden-configuration` | The same expression answering differently depending on a project setting nothing records |

## What a family needs before it counts

1. **At least one trap and one clean twin.** Without the twin, a silent-error
   rate on the family cannot be told apart from "the system could not do the
   task at all".
2. **A closed-form truth.** Derived from the fixture's own definition, on paper.
   A truth obtained by running a reference implementation measures agreement
   with that implementation, and certifies it the day it has the same bug.
3. **A plausible naive failure**, argued in `why_plausible`. If the typical
   error is loud, something already catches it and the probe belongs in an
   ordinary test suite.
4. **A real source** in `provenance.source` — a bug report, a paper, or a
   reproduction. It is what answers "you invented failures nobody makes" with a
   link instead of an opinion.

See [ADDING-A-TRAP.md](ADDING-A-TRAP.md).

Families 2, 5, 8 and 10 were the last four of the original twelve, built on
2026-08-30, and what they cost is worth recording. Three of them had been
postponed for the same reason: every obvious formulation was LOUD. A metric
operation on degrees usually returns something absurd; an empty intersection is
usually an empty intersection; a flipped raster is usually noticed the moment
anybody looks at it. A probe whose typical failure is absurd belongs in an
ordinary test suite, because something already catches it, and finding the quiet
version of each took longer than building it.

The quiet versions turned out to share a shape. In all four the wrong answer is
a perfectly ordinary quantity of the right kind — 12.7 hectares, 3 kilometres of
pipe, 45 degrees of slope, nought hectares — and in three of them every
individual row of the data is still correct. What is wrong is which rows were
added up, or what a unit meant, or which of two arguments came first.

## What this list does not claim

That these twenty-seven are all of them. They are the families we can currently
argue for, each with a source. A twenty-eighth that meets the four conditions
belongs here, and the fastest way to improve this suite is to bring one — the
same survey that produced the last nine has more candidates in it than this
list has entries, and being able to say which ones failed the conditions is
part of what the conditions are for.
