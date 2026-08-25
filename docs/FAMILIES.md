# Families, and what is actually covered

Thirteen families are on the list — twelve planned at the start, one added from
a reproduction while building. **Eight are implemented.** This page exists so that
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

Family 13 was not in the original design: it came out of building family 3
(`linear-units`) and noticing that the unit label can be *true* while the plane
it measures is not the ground. Added under the same four conditions as the
rest — which is what the closing section of this page asks of anyone.

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

That these thirteen are the complete set. They are the families we can currently
argue for, each with a source — and the thirteenth arrived exactly the way a
fourteenth should: it turned up while building another one, met the four
conditions, and was added. A fourteenth that meets them belongs here, and the
fastest way to improve this suite is to bring one.
