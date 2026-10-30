# 034 — The plan completes, the IDs exist, and the buffer used degrees

## The composition

The task has three required stages: select W-01, buffer it by 500 metres, join
the other wells within that buffer. It returns their IDs in lexicographic order
rather than a count, so the result checks the selected rows as well as their
number.

The fixture is in EPSG:4326. W-02, W-03 and W-04 are about 300, 398 and 359
metres away; every other well is at least 4 km away. The answer is therefore
`[W-02, W-03, W-04]` by construction.

## The silent failure

Applying `buffer(500)` in the layer's own units covers the whole fixture. The
composition returns all 24 other IDs. They are real IDs, correctly ordered,
produced by the requested sequence. Only the discarded intermediate polygon
shows the unit error.

This extends Argleton beyond scoring a single statistic without changing the
probe schema: the ordered array is the closed-form truth for a multi-step
spatial composition. It still does not score an agent's plan or execute a
general DAG; those remain separate measurements.
