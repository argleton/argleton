# Method

What this suite claims, how it decides, and what it does not measure. If a
number from Argleton is quoted anywhere, this document is what it means.

## 1. The class of failure

A system under test can fail in several ways. Only one of them is what this
suite is for.

| | someone notices | this suite |
|---|---|---|
| crash, exception, timeout | yes, immediately | counted, but apart |
| refusal | yes | counted, but apart |
| an absurd number (NaN, −9999, 10⁹ m elevation) | yes, on sight | **not admitted** |
| **a wrong number that looks fine** | **no** | **the metric** |

The last row is the only one where nothing in the pipeline objects: no
exception, no log line, no failing test, no reviewer raising an eyebrow. It is
also the row that existing geospatial-agent benchmarks structurally cannot see,
because they score trajectories — tools chosen, order, output file present — and
a silent error scores full marks on all three.

## 2. The admission criterion

A trap is admitted only if `plausible = true`, with an argument in
`why_plausible`. **If the typical error is loud, the probe belongs in an
ordinary test suite**, where something already catches it.

This is deliberately the one criterion that is not a matter of taste, so that a
pull request can be argued on it. "Would a competent person, seeing only this
answer, have any reason to doubt it?" If yes, the probe is out.

Consequence worth stating: this suite is **not** a general correctness test
suite, and a low silent-error rate here does not mean a system is correct. It
means it does not fail *silently* on these families.

## 3. The two populations, and why both

`traps/` alone is trivially gamed: a system that refuses everything scores a
perfect silent-error rate. `clean/` is the control. Refusing a clean probe is
scored as a failure, so the cheap strategy costs exactly what it should.

Every trap family should have a clean twin exercising the same operation
without the defect. Without it, a silent-error rate on that family cannot be
distinguished from "the system could not do the task at all".

## 4. Verdicts

Exactly one per probe, decided by `argleton/score.py`.

| verdict | meaning | success |
|---|---|---|
| `correct` | within the declared tolerance | yes |
| `correct_with_warning` | correct, and said something relevant | yes |
| `refused_correctly` | refused, **naming the real defect** | yes |
| `noisy_failure` | crash, exception, or no answer and no reason | no |
| `refused_wrongly` | refused a clean probe, or refused without naming the defect | no |
| `silent_error` | **wrong, presented as successful** | no |
| `unsupported` | the adapter does not implement the operation | neither |

**A refusal counts only when it names the defect.** "This file looks unusual",
about a file that is unusual for a reason the system never found, is a lucky
guess; scoring it as knowledge would reward hedging over understanding. Each
trap declares the substrings that count in `refusal.accept_if_mentions`.

**`unsupported` is not a failure and not a success.** It leaves both
denominators, and the counts travel with the rates so that an adapter which
skipped half the suite cannot look better than one that faced all of it.

## 5. Tolerances

Absolute, and declared before any result exists.

Absolute rather than relative on purpose: a relative tolerance is most generous
exactly where these defects live — a statistic that collapses towards zero
passes a relative check against a small expected value — and it makes the
threshold depend on the magnitude of the fixture, which the fixture author
chooses.

## 6. Truth is derived, never measured

`truth.derivation` must explain how the value follows from the fixture's own
definition, on paper. **A truth produced by running a reference implementation
measures agreement with that implementation**, and the moment the reference has
the same bug, the suite certifies it.

Where possible, `naive_failure.derivation` does the same for the wrong answer.
When both can be written in closed form, the probe explains a mechanism instead
of reporting an observation — and it stays valid on fixtures of other sizes.

Trap 001 is the worked example: the DEM is `v[i,j] = 1000 + 4j + 2i`, so the
mean is `1000 + 4·15.5 + 2·15.5 = 1093`; and summing the *differenced* values
along a row telescopes to the last value in that row, so the naive answer is the
mean of the last column divided by the width — `1155/32 = 36.09375`. Both were
then observed exactly.

## 7. Pre-registration, as a diff

1. `traps/`, `clean/`, `schema/` and this document are tagged before results.
2. Every result file carries the `spec_commit` it ran against, and a `-dirty`
   suffix when the tree was modified.
3. Whether a tolerance moved after a number was seen is answered by git history.

This is the only form of pre-registration that does not require trusting us.

## 8. Repetition and noise

The engine tier is deterministic: one run is the answer.

The agent tier is not. It is repeated, and the spread is reported alongside the
rate. A single agent run is an anecdote; we learned this from 375 runs of an
earlier experiment in which the interesting-looking effect was inside the noise.

## 9. What this suite does not measure

- **Whether a system is correct.** Only whether it fails silently on these
  families.
- **Whether it picks the right tools.** That is trajectory scoring, which other
  benchmarks do; this one starts after the tools were picked.
- **Performance, cost, or usability.**
- **Anything about families not represented here.** The families are listed in
  `docs/FAMILIES.md` with their current coverage. A family with one probe is one
  probe, and the per-family breakdown in every result says so.

## 10. Related work

August 2026 produced three independent works that make closely related moves.
The similarity is worth stating here before a reader states it for us.

- **Canary Tools** (Anand & Chattaraj,
  [arXiv:2608.04719](https://arxiv.org/abs/2608.04719)) plants diagnostic
  probe tools inside an agent's MCP tool set, each engineered to expose one
  tool-selection weakness, with a six-type taxonomy of traps. The same move —
  plant something false but plausible, watch who notices — applied one layer
  up: it measures which tool gets chosen, not whether the number that comes
  back is right.
- **Outcome Monitors** (Panthi & Abdelfattah,
  [arXiv:2608.19303](https://arxiv.org/abs/2608.19303)) validates tool results
  against outcome contracts, aimed at exactly the failure class of §1: a
  result that arrives in the expected format and is consumed as fact. It is a
  runtime defence; this suite is an offline measurement against derived truth.
  The two are complements — a monitor is what you deploy, a suite is how you
  find out whether you needed one.
- **GISAgentBench** (Pothuri, Jiang, Xu & Yang,
  [arXiv:2608.01645](https://arxiv.org/abs/2608.01645)) scores agents on 349
  practitioner-sourced GIS tasks against exact ground-truth output files, with
  "strict, deterministic, tolerance-aware output matching beyond LLM judging".
  The closest neighbour in the domain: it measures how often real tasks are
  completed correctly. It does not plant defects, so a wrong-but-plausible
  answer lowers a completion rate without ever being identified as the silent
  kind.

None of the three combines planted geospatial defects with truth derived on
paper (§6) and silent-versus-loud as the primary distinction (§1). That
combination is what this suite adds. Three groups converging on adjacent
designs in one month is evidence that the failure class is real, and we cite
them as support, not competition.

## 11. Fairness

If a probe is unfair to a system — the task is ambiguous, the tolerance is
wrong, the "defect" is defensible behaviour — that is a bug in the probe, and
the fixture in front of you is enough to prove it. Open an issue. Probes have
been wrong before and will be again; what must not happen is a probe staying
wrong because arguing about it was harder than accepting the number.
