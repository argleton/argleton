# 020 — The join that multiplied the land

## The file

Ten parcels of 5000 m² and an owners table of thirteen rows, because three
parcels are jointly held by two people each.

## The right answer, on paper

**50000 m²** of land. A parcel's area does not depend on how many names are
on the deed.

## The wrong answer

Join and sum: thirteen rows, the three shared parcels counted twice,
**65000 m²** — 30% more land than exists.

## Why it is admitted

6.5 ha against 5 ha are both ordinary figures for a cadastral sheet, and the
join succeeded: no error, no duplicate warning, thirteen perfectly good rows.
Joint ownership is the norm rather than the exception in cadastral data, and
the inflation is proportional to how much of it there is — so the figure is
wrong by a different amount in every sheet, which makes it impossible to spot
by comparison.

## The clean twin

[c020-one-owner-each](../../clean/c020-one-owner-each/) gives each parcel one owner: ten rows, 50000, and summing after joining
works.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | 65000.0 | silent error |
| MapSmith | 50000.0 | correct |

Second probe of the tabular-join family ([018](../018-join-key-typing/)).
`join_table` measures cardinality rather than assuming it: it reports that the
table turned 10 features into 13, which is the fact a SUM would otherwise
discover for you.
