# 006 — A two-layer container that answers a question nobody asked

## The file

`project.gpkg` holds two layers, both valid, both honestly named: `zones`
(4 polygons, written first — which makes it the container's **default**) and
`wells` (31 points, written second). GeoPackage is explicitly a multi-layer
format; a single project container holding zones and wells together is its
normal, documented use. Nothing about this file is unusual.

## The right answer, on paper

The question names the layer: *how many features are in the `wells` layer?*
By construction, `wells` holds W-1 through W-31. **The count is 31**, an
integer with no room for disagreement; the tolerance is 0.

## The wrong answer

Read the file, count the rows: **4**.

`read_file(path)` with no layer argument returns the container's default
layer — `zones`. This one is not fully mute, and the honest description says
so: pyogrio emits a UserWarning naming the default (*"More than one layer
found in 'project.gpkg': 'zones' (default), 'wells'. Specify layer parameter
to avoid this warning."*). But the warning goes to stderr, the returned frame
is perfectly well formed, and nothing in the **result** carries any trace of
it. A pipeline that logs-and-forgets — the overwhelming default, and the only
option in most agent stacks, where stderr never reaches the model — reports 4.

## Why it is admitted

"4 wells" is an entirely ordinary count, and a count carries no fingerprint of
the layer it came from. The person who asked about wells receives a number
computed on zones, and no property of the number says so. The one signal that
exists is attached to a stream, not to a result — and a signal nothing
downstream can see is not a defence, it is a description of the defect.

## Observed

| adapter | answer | |
|---|---|---|
| `engine:geopandas` — passes the layer the question names | 31 | ✓ |
| `engine:naive` — reads "the file" | 4 | ✗ |
| `adapters.mapsmith` — `describe_dataset`, which takes a path and nothing else | 4 | ✗ **silent error** |

The third row is the reason this probe exists, and it is about the suite's own
author: MapSmith's reader resolves a multi-layer container to its default
layer **silently** — its inspection result says `feature_count: 4` with no
warning field at all, quieter than the bare pyogrio call it wraps. Filed as
[MapSmith issue #29](https://github.com/mapsmith-ai/MapSmith/issues/29)
before this trap was published. When it is fixed, this row is the regression
test with a date on it.

## Clean twin

`clean/c006-named-layer` — one layer, honestly named, 17 points, same
question. With a single layer there is nothing to choose wrongly: a system
that answers the control and returns 4 on the trap has told us exactly one
thing — it never chose a layer at all.
