# 016 — Degrees, minutes and seconds read as a decimal

## The file

`stations.csv` has three stations with their coordinates in separate degree,
minute and second columns. ST-1 is at 41° 53′ 24″ N.

## The right answer, on paper

41 + 53/60 + 24/3600. In sixtieths: 3180/3600 + 24/3600 = 3204/3600 = 0.89
exactly, so **41.89** with no rounding anywhere.

## The wrong answer

Concatenate the fields into a decimal: **41.5324**.

It is what happens when a DMS string is parsed with the wrong pattern, when a
spreadsheet column is read as a number, or when three columns are pasted
together — and the result is a well-formed latitude.

## Why it is admitted

41.53 and 41.89 are both latitudes in central Italy, 40 km apart: close enough
that a map still looks right at country scale, far enough that every distance,
every join and every catchment is wrong. The value is in range, has the right
number of decimals, and carries no trace of the conversion that did not happen.

## The clean twin

[c016-decimal-degrees](../../clean/c016-decimal-degrees/) holds the same stations already in decimal degrees: nothing to convert.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | 41.5324 | silent error |
| MapSmith | 41.89 | correct |

`parse_coordinates` makes the caller name the columns, because the file cannot
say which of the two readings is meant.
