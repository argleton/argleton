# Changelog

All notable changes to Argleton are documented here, in the format of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project follows
[semantic versioning](https://semver.org/).

This file starts at 0.5.0. Releases before it are described by their tags and
by the dated sections of [`results/README.md`](results/README.md), which is
where this project's findings have always been written — the omission was that
a reader had nowhere to see, in one place, what changed between two versions of
the suite itself.

## [Unreleased]

Nothing yet.

## [0.5.0] - 2026-09-21

Thirty-one commits since 0.4.0. The headline is that a third-party system was
measured against the engine it wraps, for the first time, and the result is
that the wrapper is not the thing to blame.

### Added

- **Three QGIS rows, and they are the same QGIS.** The processing engine driven
  headless through `qgis_process`, and the two MCP servers that run inside a
  live QGIS and forward to it — `nkarasiak/qgis-mcp` 0.14.0 over its plugin
  socket, QGIS Agent MCP 0.5.0 over its local bridge. All three answer **every
  one of the thirty-one traps**, nothing unsupported, and all three come out at
  the same silent-error rate of **0.3871**.

  That equality is the finding, and it is only readable because the engine has
  a row of its own: the wrappers inherit it, neither adding a correct answer
  nor losing one. Without the engine's row, three equal numbers read as three
  equally defective servers, and that reading would be wrong. The engine's row
  was built first for exactly this reason.

  The chains are shared by all three adapters in one file, so a difference
  between the rows can only come from the system rather than from a chain that
  drifted between copies.

- **`gis-mcp` 0.15.0**, the first system here whose defects are not ours to
  fix, published on 2026-09-10 after its maintainer was told first.

- **Family 29, `ring-role-by-winding`.** A shapefile carries no nesting, so
  which ring is a hole is decided by the direction it is wound and by nothing
  else. An inner ring wound like its parent reads as a second shell and its
  area is added: 31000 m² where the truth is 29000, +6.9% in the owner's
  favour, with the right bounding box, the right CRS and no warning.

### Changed

- **`argleton.__version__` is derived instead of written.** It answered
  `0.1.0.dev0` while 0.4.0 was on PyPI, across four releases, because the
  number lived in two places and only one was on a checklist. Nothing inside
  the package read it, so nothing caught it. It now comes from the installed
  distribution, or from `pyproject.toml` when running from a checkout, and a
  test compares the two.

- **The naive baseline pin moves to 0.9355**, which is the pin doing its job
  rather than a number being adjusted: the denominator grew when the suite
  reached thirty-one traps.

- **A fixture build that dies with no output is retried on its signature, not
  on a count.** One retry had been calibrated against 370 builds, where a
  doubled failure is about one in a thousand. At nine adapters and 558 builds
  the same doubled failure is about one in twenty. The constant was not wrong
  when it was written; it went wrong when the table grew, and nothing was
  watching it. The retry now keys on what the death looks like — both output
  streams empty, because the process never ran — which is stricter than what it
  replaces: a builder that fails while saying something now fails on the first
  attempt.

### Fixed

- **The site sorted both QGIS MCP servers below the naive baseline**, the row
  that exists to be the worst line on the page, because neither matched a
  prefix in the ordering list and an unmatched row sorts last. The comment
  above that list had named their correct place two months earlier — beside
  `gis-mcp`, with the engine they call directly underneath. A rule stated in a
  comment and not executed by code is not a rule; a test covers it now.

- **The site said "every system here completes every clean probe"** directly
  under a column showing two systems that do not.

- **Three surfaces said every number comes from calling code in the same
  process rather than over a transport.** Two rows are a TCP socket and a local
  bridge into a live QGIS, which is what their own labels say.

- **The results page said we had "found nothing of its own" about one wrapper**,
  seven lines after describing a property of that wrapper. The true sentence is
  "nothing that makes an answer wrong", and the notification rule is restated
  around it.

- **"In opposite directions" described two rows with the same probe, the same
  verdict and the same completion rate.** They differ in how they fail.

- **`FAMILIES.md` published four false sentences about its own count** while
  two guards on counts were green, because they watched three other sentence
  shapes. The numbers are derived now, and an unexplained spelled-out number in
  that file is a failure rather than a gap.

- **The results index counts its own rows** instead of only checking the ones
  that happen to be listed, and the tool count is asked of the server rather
  than written down.

- **`publish_run.py`** — in the private workspace, but its effects are here —
  refuses to publish an adapter whose failures all carry one message: that is a
  system we could not reach, not a system that got things wrong. A run was
  minutes from publishing `completion 0.2258` for a third-party server whose
  62 probes had all failed to connect.
