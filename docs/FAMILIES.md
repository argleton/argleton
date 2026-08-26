# Families, and what is actually covered

Twenty-three families are on the list — twelve planned at the start, eleven added
from reproductions and from a survey of what the archives and the libraries
themselves warn about. **Eighteen are implemented.** This page exists so that
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

Families 13 to 23 were not in the original design. 13 came from building family
3 (`linear-units`), on noticing that a unit label can be *true* while the plane
it measures is not the ground; 14 from writing a resampling operation and asking
what its output alphabet is allowed to contain; 15 to 23 from a survey of what
the archives, the libraries and their own documentation warn about — 47 candidate
mechanisms, of which these are the ones whose truth is arithmetic.

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

## What this list does not claim

That these twenty-three are the complete set. They are the families we can currently
argue for, each with a source. A twenty-fourth that meets the four conditions
belongs here, and the fastest way to improve this suite is to bring one — the
same survey that produced the last nine has more candidates in it than this
list has entries, and being able to say which ones failed the conditions is
part of what the conditions are for.
