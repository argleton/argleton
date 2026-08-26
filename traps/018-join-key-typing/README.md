# 018 — The leading zero the CSV reader threw away

## The file

Twelve municipalities keyed by ISTAT code, four of which begin with a zero, and
`population.csv` with a row for each: 4 × 9500 + 8 × 7750.

## The right answer, on paper

**100000.** The codes are strings on both sides, so every row matches.

## The wrong answer

Read the CSV with type inference: '001' becomes the integer 1, which matches
no code in the layer. Four municipalities drop out of the join with 38000
people, and the total comes back **62000**.

## Why it is admitted

62000 is an ordinary total for twelve municipalities, and the join reports no
error: an inner join that loses rows is indistinguishable from one that had
fewer to find. Leading-zero codes are the norm in national identifier schemes
— ISTAT, FIPS, INSEE, postcodes — and every CSV reader infers integer columns
by default. Verified while building this fixture: pandas reads the column as
int64 and turns '001' into 1.

## The clean twin

[c018-plain-keys](../../clean/c018-plain-keys/) uses twelve codes with no leading zeros and the same 100000 total: type
inference changes nothing, so ignoring key typing works.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | 62000 | silent error |
| MapSmith | 100000 | correct |

Second probe of this family: [020](../020-join-cardinality/), where the join
multiplies the land instead of losing it. `join_table` reads keys as text and
reports the fan-out.
