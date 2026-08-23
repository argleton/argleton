# Families, and what is actually covered

Twelve families are planned. **Three are implemented.** This page exists so that
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
| 6 | `nodata` | [003](../traps/003-nodata-in-statistics/) + [c003](../clean/c003-raster-mean-nodata/) | mean 945.005 instead of 1000.0 | 5.5% out — too small to question, too large to ignore in a volume or a flood level |

## Planned

Numbered as in the original design, so the gaps stay visible rather than being
renumbered away.

| # | Family | The error |
|---|---|---|
| 2 | `geographic-crs` | A metric operation on a geographic CRS with no reprojection — degrees treated as a length |
| 4 | `mismatched-crs` | Join or overlay across two layers in different, individually valid, coordinate systems |
| 5 | `empty-result` | An intersection that is empty because of a defect, told apart from one that is legitimately empty |
| 7 | `invalid-geometry` | Self-intersecting polygons whose area is computed anyway |
| 8 | `mixed-geometry` | A layer holding more than one geometry type |
| 9 | `antimeridian` | Extents that invert across the 180th meridian or at the poles |
| 10 | `raster-affine` | Flipped axes or a non-standard affine transform |
| 11 | `ambiguous-layer` | A multi-layer container with no chosen layer, or an ambiguous geometry column |
| 12 | `implicit-parameter-units` | A buffer of "500" against coordinates measured in degrees |

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

That these twelve are the complete set. They are the families we can currently
argue for, each with a source. A thirteenth that meets the four conditions
belongs here, and the fastest way to improve this suite is to bring one.
