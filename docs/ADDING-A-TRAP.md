# Adding a trap

A trap is a small, self-contained thing: two files and a README, no need to
understand the runner, and a "done" that is objective because the right answer
is arithmetic. It is the best first contribution to this repository, and it is
where the suite gets better.

There is no CLA. The licence is Apache-2.0.

## The four conditions

A probe is admitted when all four hold. The first is the only one that is not a
matter of taste, and it is the one most proposals fail.

### 1. The typical wrong answer must be plausible

**If the defect crashes, throws, or returns an absurd number, the probe does not
belong here.** Something already catches it — a test, a log, the first person to
look. This suite exists for the answers nothing catches.

Write the argument in `why_plausible`. The test is: *would a competent person,
seeing only this answer, have any reason to doubt it?* If yes, the probe is out.

The best traps are wrong by a little. Trap 003 returns a mean elevation 5.5% low
and that is exactly why it is dangerous; the same defect on a different raster
returns a negative elevation, and nobody ships that.

### 2. The truth must be derived, not measured

`truth.derivation` explains how the value follows from the fixture's own
definition, on paper. **A truth obtained by running a reference implementation
measures agreement with that implementation**, and certifies it the day it has
the same bug.

Where you can, do the same for the wrong answer in `naive_failure.derivation`.
When both are closed form, the probe explains a mechanism instead of reporting
an observation, and it stays true on fixtures of other sizes. Trap 001 is the
worked example: the mean is `1000 + 4·15.5 + 2·15.5 = 1093`, and the naive
answer is the mean of the last column divided by the width, because summing
differenced values along a row telescopes.

### 3. The task must have exactly one correct answer

This is the condition that caught us. The first version of trap 002 asked for
"the area in square metres", which admits at least three defensible answers —
planar in the source CRS, geodesic on the ellipsoid, planar after reprojecting
somewhere. It scored a *careful* adapter as a silent error for choosing a
different one.

A probe measures one thing. Any ambiguity in the task is a bug in the probe.

### 4. It must cite something real

`provenance.source` takes a bug report, a paper, or a reproduction. It answers
"you invented failures nobody makes" with a link rather than an opinion. Trap
001 cites an upstream issue; trap 003 cites a class old enough to be folklore
and still undetected.

## The files

```
traps/0NN-short-name/
  probe.toml    the contract — schema/probe.schema.json validates it
  build.py      generates the fixture, deterministically
  README.md     the failure, in prose, with both numbers derived
clean/cNN-short-name/
  probe.toml    the same task without the defect
  build.py
```

**Fixtures are built, never committed.** The repository stays in kilobytes,
anyone can regenerate them and check they are what we say, and rerunning the
engine tier costs nothing — which is what lets a third party contest a number
instead of taking it.

`build.py` takes an output directory as `argv[1]`, writes its files there, and
must produce **byte-identical output on every run**; a test enforces it. Watch
for formats that stamp the clock: GeoPackage writes the write time into
`gpkg_contents`, which is why the vector builders pin `OGR_CURRENT_DATE`.

## Every family needs a clean twin

Same operation, same shape of task, no defect. Without it, a silent-error rate
on the family cannot be told apart from "the system could not do the task at
all". A test enforces this too.

Refusing a clean probe is scored as a failure. That is what stops a system
scoring perfectly by refusing everything, and it is why the two rates are always
published together.

## Refusals

A refusal counts as success **only when it names the real defect**. List the
substrings that count in `refusal.accept_if_mentions`. "This file looks unusual"
about a file that is unusual for a reason the system never found is a lucky
guess, and scoring it as knowledge would reward hedging over understanding.

## Check it before you open the pull request

```bash
pip install -e .[fixtures,dev]
pytest -q                                   # contract, determinism, clean twin
argleton --adapter engine:naive  --only 0NN-your-trap   # should be silent_error
argleton --adapter engine:rasterio --only 0NN-your-trap # should be correct
```

`engine:naive` is the composition almost everyone writes first: read the file,
take the statistic, report it. If your trap does not catch it, the trap may be
measuring care rather than a defect. If a careful adapter fails it, condition 3
is probably the problem.

## Tolerances

Absolute, and set **before** you have seen any result. Absolute rather than
relative because a relative tolerance is most generous exactly where these
defects live — a statistic collapsing towards zero passes a relative check
against a small expected value — and because it would make the threshold depend
on the magnitude of the fixture, which you chose.

Widening a tolerance after seeing a number is visible in the git history. That
history is the pre-registration; it is why every published result carries the
`spec_commit` it ran against.

## If a probe here is wrong

Open an issue. Probes have been wrong before — twice on the first day — and they
will be again. The fixture in front of you is enough to prove it, which is the
whole design. What must not happen is a probe staying wrong because arguing
about it was harder than accepting the number.
