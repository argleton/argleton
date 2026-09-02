"""The public face must say what the repository measures — mechanically.

Three numbers went stale in one day: a transcript still showed a run over one
trap after the suite had five, a hand-typed "nine more families" survived two
family additions, and the README kept promising a result that was never going
to exist. None of that is caught by testing the probes, because "we wrote it"
and "we published it" are different acts. These tests are the difference.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from argleton.model import discover

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "twenty-one": 21, "twenty-two": 22, "twenty-three": 23,
    "twenty-four": 24, "twenty-five": 25, "twenty-six": 26,
    "twenty-seven": 27, "twenty-eight": 28, "twenty-nine": 29,
    # Filled in as the suite reaches them, and the cost of the gap is a
    # `KeyError` rather than a false pass — which is the safe direction, and how
    # this line came to be written: the run of 2026-09-02 took the suite to
    # thirty traps and the word was not here.
    "thirty": 30, "thirty-one": 31, "thirty-two": 32, "thirty-three": 33,
}


def latest_run() -> tuple[str, dict[str, dict]]:
    """The published run — the one `results/LATEST` names — keyed by system.

    This used to sort the directory names and take the last, which is the same
    mistake the page builder made: two runs on one day sort by their words, so
    "…-eight-families" came before "…-six-families" and both the page and this
    test agreed on the older one. A test that shares the defect it exists to
    catch is worse than no test, and this is the second time in this repo.
    """
    from argleton.published import published_run

    run = published_run(ROOT)
    data = {}
    for f in sorted(run.glob("*.json")):
        record = json.loads(f.read_text(encoding="utf-8"))
        data[record["system"]] = record
    assert data, f"{run.name} holds no result files"
    return run.name, data


def test_the_published_run_is_the_one_with_the_most_families():
    """`results/LATEST` is written by hand, so it can be forgotten. It cannot
    silently point at a run measuring fewer families than one we already have:
    that is the superseded-front-page failure, one indirection later."""
    published, systems = latest_run()
    covered = max(len(r["by_family"]) for r in systems.values())
    for directory in (ROOT / "results").iterdir():
        if not directory.is_dir() or directory.name == published:
            continue
        for f in directory.glob("*.json"):
            other = json.loads(f.read_text(encoding="utf-8"))
            assert len(other["by_family"]) <= covered, (
                f"{directory.name} covers more families than the published "
                f"{published}: update results/LATEST"
            )


def by_base_name(name: str, systems: dict[str, dict]) -> dict:
    """Match a table row to a result record, ignoring the parenthetical
    (the README says "(main)", the record says "(main @ <sha>)")."""
    base = name.split(" (")[0].strip()
    matches = [r for s, r in systems.items() if s.split(" (")[0].strip() == base]
    assert len(matches) == 1, f"{name!r} matches {len(matches)} systems in the latest run"
    return matches[0]


def parse_result_rows(text: str) -> list[tuple[str, list[str]]]:
    """Markdown table rows whose numeric cells look like rates and counts."""
    rows = []
    for line in text.splitlines():
        cells = [c.strip().strip("*").strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.fullmatch(r"\d\.\d+", cells[1]):
            rows.append((cells[0], cells[1:]))
    return rows


def test_the_readme_results_table_is_the_latest_run():
    """Every number in the README's Results table must exist in the newest
    `results/` directory. A front page showing a superseded run is the exact
    failure this suite measures in other people's software."""
    _, systems = latest_run()
    section = README.split("## Results", 1)[1].split("\n## ", 1)[0]
    rows = parse_result_rows(section)
    assert len(rows) == len(systems), (
        f"README Results table has {len(rows)} rows, the latest run measured {len(systems)} systems"
    )
    for name, cells in rows:
        record = by_base_name(name, systems)
        assert float(cells[0]) == record["silent_error_rate"], f"{name}: silent error rate"
        assert float(cells[1]) == record["completion_rate"], f"{name}: completion rate"
        assert int(cells[2]) == record["traps_run"], f"{name}: traps run"


def test_the_results_index_has_a_section_for_the_latest_run_and_it_agrees():
    """`results/README.md` must open a dated section for the newest run, and
    that section's table must match the JSON beside it."""
    run_name, systems = latest_run()
    text = (ROOT / "results" / "README.md").read_text(encoding="utf-8")
    date = run_name[:10]
    heading = re.search(rf"^## {re.escape(date)}\b.*$", text, re.MULTILINE)
    assert heading, f"results/README.md has no section for the {run_name} run"
    section = text[heading.end():].split("\n## ", 1)[0]
    for name, cells in parse_result_rows(section):
        record = by_base_name(name, systems)
        assert float(cells[0]) == record["silent_error_rate"], f"{name}: silent error rate"
        assert float(cells[1]) == record["completion_rate"], f"{name}: completion rate"
        assert int(cells[2]) == record["traps_run"], f"{name}: traps run"
        assert int(cells[3]) == record["unsupported"], f"{name}: not-applicable count"


def test_the_readme_transcripts_print_todays_summary_lines():
    """The `$ argleton --adapter engine:X` transcripts quote summary lines. Each
    quoted line must be what that adapter produces on the current probes — a
    transcript from an older suite is a wrong number on the first screen."""
    _, systems = latest_run()
    adapter = None
    checked = 0
    for line in README.splitlines():
        command = re.match(r"\$ argleton --adapter engine:(\w+)", line.strip())
        if command:
            adapter = command.group(1)
            continue
        summary = re.match(
            r"silent_error_rate ([\d.]+) over (\d+) traps\s+\|\s+"
            r"completion_rate ([\d.]+) over (\d+) clean",
            line.strip(),
        )
        if summary and adapter:
            record = next(r for r in systems.values() if r["adapter"] == f"engine:{adapter}")
            assert float(summary.group(1)) == record["silent_error_rate"], adapter
            assert int(summary.group(2)) == record["traps_run"], adapter
            assert float(summary.group(3)) == record["completion_rate"], adapter
            assert int(summary.group(4)) == record["clean_run"], adapter
            checked += 1
    assert checked >= 1, "no transcript summary lines found — did the README format change?"


def test_the_install_paragraph_does_not_credit_the_run_to_the_release():
    """The release count and the RUN count are two numbers, one sentence apart.

    On 2026-08-31 the paragraph read "release 0.4.0 carries the 30 traps and 28
    families the results below were produced from". Every number in it was
    right and the sentence was false: the published run covers 29, because trap
    030 landed after it. The sibling guard below checks the release count
    against the tag and had nothing to say, because the defect was not in a
    number — it was in the word attaching one number to the other.

    A reader who installs the release, reruns, and gets a rate the table does
    not show has been told something untrue, which is the failure this suite
    exists to name in other people's work.
    """
    run_name, systems = latest_run()
    ran = max(r["traps_run"] for r in systems.values())
    carried = len([p for p in discover(ROOT) if p.population == "trap"])
    if ran == carried:
        return
    prose = (ROOT / "README.md").read_text(encoding="utf-8")
    assert re.search(rf"run over {ran} of them", prose), (
        f"the release carries {carried} traps and the published run ({run_name}) "
        f"covers {ran}. The install paragraph has to say the table is a run over "
        f"{ran} of them, or a reader who reruns gets a number the table does not "
        "show and no way to know why."
    )


def test_the_naive_score_quoted_in_prose_is_current():
    _, systems = latest_run()
    naive = next(r for r in systems.values() if r["adapter"] == "engine:naive")
    quoted = re.search(r"scores \*\*([\d.]+) / ([\d.]+)\*\*", README)
    assert quoted, "the README no longer quotes the naive score — update this test"
    assert float(quoted.group(1)) == naive["silent_error_rate"]
    assert float(quoted.group(2)) == naive["completion_rate"]


def test_the_family_counts_agree_everywhere():
    """Implemented and planned family counts appear in the README, FAMILIES.md
    and the site template. One source: the probes and FAMILIES.md's numbered
    rows. Everything else must match or be a build-time placeholder."""
    implemented = len({p.family for p in discover(ROOT) if p.population == "trap"})
    families_md = (ROOT / "docs" / "FAMILIES.md").read_text(encoding="utf-8")
    planned = len(set(re.findall(r"^\|\s*(\d+)\s*\|", families_md, re.MULTILINE)))

    # `[A-Za-z-]+`, with the hyphen: the count passed twenty and the words grew
    # one. A pattern that silently stops matching is a check that silently stops
    # checking, and this one would have gone quiet at exactly the moment the
    # number started being easy to get wrong.
    stated = re.search(r"\*\*([A-Za-z-]+) are implemented\.\*\*", families_md)
    assert stated, "FAMILIES.md no longer states how many families are implemented"
    assert NUMBER_WORDS[stated.group(1).lower()] == implemented, "FAMILIES.md implemented count"

    # The five families that are named and not yet built carry no number, on
    # purpose: a family is numbered when it has a probe pair. So "planned" is
    # the numbered rows plus the named-but-unbuilt ones, and nothing else may
    # add up differently. On 2026-09-02 they did: every numbered planned row had
    # been implemented, so `planned - implemented` was 0 and the published page
    # read "0 more are named" directly above a list of five.
    unbuilt = _unbuilt_families(families_md)
    assert unbuilt, "FAMILIES.md no longer names a family it has not built"
    assert not (unbuilt & {p.family for p in discover(ROOT)}), (
        f"{sorted(unbuilt & {p.family for p in discover(ROOT)})} are listed under "
        "Planned in FAMILIES.md and have probes in the repository. A family that "
        "shipped has to leave the planned list, or the page counts it twice and "
        "the roadmap advertises work already done."
    )

    # The head of FAMILIES.md states the total. It said twenty-seven for two
    # days under a table of twenty-eight, because the only guarded sentence was
    # the one below it.
    on_the_list = re.search(r"^([A-Za-z-]+) families are on the list", families_md, re.MULTILINE)
    assert on_the_list, "FAMILIES.md no longer states how many families are on the list"
    assert NUMBER_WORDS[on_the_list.group(1).lower()] == implemented + len(unbuilt), (
        "FAMILIES.md total: the head of the page must equal implemented plus "
        "the families named under Planned"
    )

    covered = re.search(r"([A-Za-z-]+) families of ([a-z-]+)", README)
    assert covered, "the README no longer states its coverage"
    assert NUMBER_WORDS[covered.group(1).lower()] == implemented, "README implemented count"
    assert NUMBER_WORDS[covered.group(2)] == planned + len(unbuilt), "README planned count"

    family_table = re.findall(r"^\| `([a-z-]+)` \|", README, re.MULTILINE)
    assert len(family_table) == implemented, "README family table row count"

    # A blank line inside a Markdown table ends the table, and the rows after it
    # render as literal pipes. The seven newest families spent three days that
    # way on the page that is meant to say what the suite covers.
    implemented_section = families_md.split("## Implemented", 1)[1].split(chr(10) + "## ", 1)[0]
    blocks, current = [], []
    for line in implemented_section.strip().split(chr(10)):
        if line.startswith("|"):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    assert len(blocks) == 1, (
        f"{len(blocks)} table blocks under ## Implemented in FAMILIES.md. A blank "
        "line inside a Markdown table ends it, and the rows after it render as "
        "literal pipes on the page that says what the suite covers."
    )
    assert len(blocks[0]) == implemented + 2, (
        f"{len(blocks[0]) - 2} rows in the Implemented table against {implemented} "
        "families with probes"
    )


def _unbuilt_families(families_md: str) -> set[str]:
    """The families FAMILIES.md names under Planned. Same parse as the build."""
    planned = families_md.split("## Planned", 1)[-1].split(chr(10) + "## ", 1)[0]
    return set(re.findall(r"^\|\s*`([a-z-]+)`\s*\|", planned, re.MULTILINE))


def test_the_site_template_has_no_hand_typed_count_and_no_orphan_placeholder():
    """Counts on the page come from placeholders the build fills; a literal
    number word in the template is the "nine more" defect waiting to recur."""
    template = (ROOT / "site" / "index.template.html").read_text(encoding="utf-8")
    build = (ROOT / "site" / "build.py").read_text(encoding="utf-8")
    placeholders = set(re.findall(r"\{\{[A-Z_]+\}\}", template))
    assert placeholders, "the template lost its placeholders"
    for placeholder in placeholders:
        assert placeholder in build, f"{placeholder} is in the template and not in build.py"
    for word in ("nine more", "seven more", "eight more"):
        assert word not in template.lower(), f"hand-typed count {word!r} in the template"

    # And ordinals, which this test did not look for. "bring a thirteenth"
    # survived seven family additions on the published page, two lines under
    # generated text reading "20 families of 25" — on a suite whose pitch is
    # numbers you can check. An ordinal is a count; the build computes it now.
    ORDINAL = (
        r"(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
        r"eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|"
        r"seventeenth|eighteenth|nineteenth|twentieth|twenty-[a-z]+)"
    )
    counted = re.findall(rf"bring a ({ORDINAL})|({ORDINAL}) famil", template.lower())
    flat = [word for pair in counted for word in pair if word]
    assert not flat, (
        f"hand-typed ordinal(s) {sorted(set(flat))} counting families in the "
        "template. Add a placeholder and let build.py count — `next_ordinal()` "
        "is there. 'first' and 'second' as ordinary prose are fine; an ordinal that "
        "names a position in the family list is a count."
    )


def test_the_results_headline_counts_the_run_and_not_the_checkout():
    """A figure about a run has to be read out of the run.

    Found by a reader of the live page on 2026-08-31: the heading over the
    results table said "30 traps, 28 families" while the published run had faced
    29 and 27. Both numbers came from `traps/` in the working tree, so every
    family added after a run silently inflated that run's coverage — on the one
    surface whose whole argument is that its numbers can be checked. Same class
    as the `sorted[-1]` defect that published the older of two runs: the fix is
    that the run is the only source for a claim about the run.

    So the results section may use `{{RUN_TRAPS}}` and `{{RUN_FAMILIES}}` and
    must not use the suite-wide counters, and the two placeholders must resolve
    to what the published run actually saw.
    """
    # Loaded by path: the directory is called `site`, which is a stdlib module
    # name, so an ordinary import would silently get the wrong thing.
    import importlib.util

    location = importlib.util.spec_from_file_location(
        "argleton_site_build", ROOT / "site" / "build.py"
    )
    builder = importlib.util.module_from_spec(location)
    location.loader.exec_module(builder)
    coverage_gap, run_coverage = builder.coverage_gap, builder.run_coverage

    _, data = latest_run()
    records = list(data.values())
    traps, families = run_coverage(records)

    assert traps == max(r["traps_run"] for r in records), "run trap count"
    covered = set()
    for record in records:
        covered |= set(record["by_family"])
    assert families == len(covered), "run family count"

    implemented = {p.family for p in discover(ROOT) if p.population == "trap"}
    assert families <= len(implemented), (
        "the published run reports more families than the suite implements, "
        "which means one of the two is being counted wrong"
    )

    template = (ROOT / "site" / "index.template.html").read_text(encoding="utf-8")
    results = template[template.index('<section id="results"'):]
    results = results[: results.index('<section id="families"')]
    for suite_wide in ("{{TRAPS}}", "{{FAMILIES}}"):
        assert suite_wide not in results, (
            f"{suite_wide} counts the checkout and appears in the results "
            "section, which describes one run of it. Use {{RUN_TRAPS}} / "
            "{{RUN_FAMILIES}}."
        )
    assert "{{RUN_TRAPS}}" in results and "{{RUN_FAMILIES}}" in results, (
        "the results section no longer states the coverage of the run it shows"
    )

    # And the caveat that keeps a 0.00 from being read as broader than it is:
    # present exactly when families were added after the run was published.
    gap = coverage_gap(
        [{"family": f, "population": "trap"} for f in implemented], families
    )
    assert bool(gap) == (len(implemented) > families), (
        "the coverage caveat is generated, and it disagrees with the counts: "
        f"{len(implemented)} implemented, {families} in the run, gap={gap!r}"
    )
    assert "{{COVERAGE_GAP}}" in results, (
        "the results section dropped the placeholder that names families the "
        "published run never saw"
    )


def test_every_live_family_count_in_public_markdown_is_current():
    """The stale-caveat defect, one directory over. `results/README.md` carried
    "three families of twelve" in the section the front page links as *what the
    numbers do not say* — four families after it stopped being true, and in the
    one paragraph whose whole job is to keep a reader from over-reading a 0.00.

    Present tense marks a live claim. A past-tense sentence about a superseded
    run is a record of what was claimed then and stays exactly as written.
    """
    implemented = len({p.family for p in discover(ROOT) if p.population == "trap"})
    # Numbered rows PLUS the ones named under Planned, which carry no number by
    # design — a family is numbered when it has a probe pair, so that a number
    # in a result always points at something that ran. Counting only the
    # numbered ones made the unbuilt families invisible, which is the same
    # blind spot that had the site caption saying "0 more are named" directly
    # above a list of five on 2026-09-02. Same parse as `site/build.py`, so the
    # page and this test cannot disagree about what the file says.
    families = (ROOT / "docs" / "FAMILIES.md").read_text(encoding="utf-8")
    numbered = set(re.findall(r"^\|\s*(\d+)\s*\|", families, re.MULTILINE))
    unbuilt = set(re.findall(
        r"^\|\s*`([a-z-]+)`\s*\|",
        families.split("## Planned", 1)[-1].split("\n## ", 1)[0],
        re.MULTILINE,
    ))
    planned = len(numbered) + len(unbuilt)
    live = re.compile(r"([A-Za-z-]+) families of ([a-z-]+) are implemented")
    checked = 0
    for page in public_markdown():
        for stated, out_of in live.findall(page.read_text(encoding="utf-8")):
            assert NUMBER_WORDS[stated.lower()] == implemented, f"{page.name}: implemented count"
            assert NUMBER_WORDS[out_of] == planned, f"{page.name}: planned count"
            checked += 1
    assert checked, (
        "no live family count found in public markdown — the caveat that stops a 0.00 "
        "being read as broader than it is has to state the coverage somewhere"
    )


def test_the_repository_and_its_site_point_at_each_other():
    """Found by a reader, not by a test: argleton.org was linked from the
    repository's `homepage` field — which nobody looks at — and from nowhere in
    the README. Each surface must name the other, and the README must do it on
    the first screen. The link to the system this suite measures is checked in
    the same breath, because hiding it would be the more tempting mistake."""
    template = (ROOT / "site" / "index.template.html").read_text(encoding="utf-8")
    first_screen = README.split("\n## ", 1)[0]
    assert "argleton.org" in first_screen, (
        "the README does not link the published site on its first screen"
    )
    assert "github.com/argleton/argleton" in template, (
        "argleton.org does not link the repository it renders"
    )
    # The conflict-of-interest disclosure has to exist and has to be findable.
    # Deliberately *not* required on the first screen, and not in either
    # navigation bar: a suite that leads with the name of the product whose
    # authors wrote it reads as that product's marketing, which is the one
    # criticism no amount of regenerable fixtures answers.
    assert "mapsmith" in README.lower(), (
        "the README no longer says who wrote this and which system it measures"
    )
    assert "mapsmith.dev" in template, (
        "the site no longer declares whose suite this is: stated, not hidden"
    )
    assert "mapsmith" not in template.split('<div class="lead">', 1)[0].lower(), (
        "MapSmith has reached the masthead of argleton.org — the disclosure belongs in "
        "'Who wrote this', not in the navigation of the suite that grades it"
    )


def test_the_published_run_directory_is_linked_from_the_results_index():
    """`results/README.md` is what GitHub renders for that directory, and it
    described four runs without linking any of them. The JSON records are the
    evidence — per-probe verdicts and the `by_family` breakdown — so the index
    has to reach them, not just summarise them."""
    run_name, _ = latest_run()
    text = (ROOT / "results" / "README.md").read_text(encoding="utf-8")
    assert f"]({run_name}/)" in text or f"]({run_name})" in text, (
        f"results/README.md never links {run_name}/, the run it publishes"
    )


def public_markdown() -> list[Path]:
    return [
        p for p in ROOT.rglob("*.md")
        if not any(part.startswith(".") or part == "__pycache__" for part in p.parts)
    ]


@pytest.mark.parametrize("page", public_markdown(), ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_links_resolve(page: Path):
    """Every relative link in public markdown points at a file that exists.
    Links that climb out of the repository resolve on GitHub's URL space
    (`../../../commit/…`) and are skipped, not checked."""
    text = page.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        resolved = (page.parent / target.split("#", 1)[0]).resolve()
        if not resolved.is_relative_to(ROOT):
            continue
        assert resolved.exists(), f"{page.name}: broken link {target}"


# Vendor names this project does not write in public, at all: no note, no
# provenance line, no comparison. A suite that measures systems has to be
# careful here in a way a product does not: naming a vendor next to a silent
# error reads as an accusation we have not made and cannot support, and the
# provenance blocks in `probe.toml` are the place where one slips in as a
# citation. Say what the documentation says without saying whose it is.
VENDOR_SILENCE = re.compile(r"esri|arcgis|arcpy|arcmap", re.IGNORECASE)


def _tracked_text_files() -> list[Path]:
    import subprocess

    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True
    ).stdout.split("\n")
    keep = {".md", ".py", ".html", ".yml", ".yaml", ".toml", ".json", ".cff", ".txt"}
    return [
        ROOT / name
        for name in out
        if name and (ROOT / name).suffix in keep and (ROOT / name).exists()
    ]


def test_no_vendor_is_named_in_public():
    """Silence about a named vendor is a decision, so it needs a check.

    Three mentions had already accumulated as citations in trap provenance,
    where they look like diligence rather than like a comparison. Nothing else
    in this suite looks at prose."""
    offenders = {}
    for page in _tracked_text_files():
        if page.resolve() == Path(__file__).resolve():
            continue  # this file names them in order to forbid them
        text = page.read_text(encoding="utf-8", errors="replace")
        found = sorted({m.group(0) for m in VENDOR_SILENCE.finditer(text)})
        if found:
            offenders[str(page.relative_to(ROOT)).replace("\\", "/")] = found
    assert not offenders, (
        f"these files name a vendor this project stays silent about: {offenders}. "
        "State what the documentation requires without naming whose documentation it is."
    )

def test_the_wheel_would_ship_the_probes():
    """A runner without probes is a command that finds nothing and exits 2.

    The first build of this package held 17 files and zero probes: `pip install
    argleton` would have installed a tool that looks like it works and does not,
    which is the failure mode this suite exists to measure. Checking the build
    configuration rather than building a wheel keeps the test fast, and the thing
    that would break is exactly a line disappearing from here.
    """
    import tomllib

    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    include = (
        config["tool"]["hatch"]["build"]["targets"]["wheel"]
        .get("force-include", {})
    )
    for source in ("traps", "clean", "schema"):
        assert source in include, (
            f"the wheel would not ship {source}/ — an installed argleton needs its probes"
        )
        assert include[source].startswith("argleton/"), (
            f"{source}/ would land at the top level of site-packages, not inside the package"
        )


def test_the_naive_breakdown_in_prose_matches_its_own_score():
    """"Falls into N of the M traps" is a number, and it aged like every other.

    The README carried "twenty of the twenty-one" while the published score was
    0.9545 — which is 21 of 22. `test_the_naive_score_quoted_in_prose_is_current`
    checked the rate and not the sentence explaining it, so the explanation drifted
    away from the number it explains, in the paragraph that makes the whole point
    about careless code being right until it is not.
    """
    _, systems = latest_run()
    naive = next(r for name, r in systems.items() if "naive" in name)
    traps = naive["traps_run"]
    fell = round(naive["silent_error_rate"] * traps)

    prose = (ROOT / "README.md").read_text(encoding="utf-8")
    found = re.findall(r"falls into ([a-z-]+) of the ([a-z-]+) traps", prose)
    assert found, (
        "the README no longer says how many traps the naive adapter falls into, "
        "which is the sentence that makes 0.9545 mean something"
    )
    for stated, out_of in found:
        assert NUMBER_WORDS[stated] == fell, (
            f"the README says the naive adapter falls into {stated} traps; its "
            f"score of {naive['silent_error_rate']} over {traps} says {fell}"
        )
        assert NUMBER_WORDS[out_of] == traps, (
            f"the README says {out_of} traps, the run has {traps}"
        )


def test_the_citation_and_the_package_agree_on_the_version():
    """A citation without a version points at a moving target.

    This project's whole argument is that a number is only checkable if you can
    say which code produced it — every run pins its `spec_commit` for exactly
    that reason. A CITATION.cff that names the repository and not the release
    asks a reader to cite whatever happens to be on main the day they look.
    """
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    shipped = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
    assert shipped, "pyproject.toml has no version"
    cited = re.search(r'^version: "?([^"\n]+)"?', citation, re.MULTILINE)
    assert cited, (
        "CITATION.cff carries no version, so it cites whatever is on main today"
    )
    assert cited.group(1) == shipped.group(1), (
        f"CITATION.cff cites {cited.group(1)} and the package is "
        f"{shipped.group(1)}"
    )


def test_the_readme_names_the_release_that_reproduces_the_results():
    """The install line and the results table have to describe the same artifact.

    On 2026-08-28 they did not: `pip install "argleton[fixtures]"` fetched 0.1.0
    with 21 traps while the table three screens down reported 22, so a reader who
    followed the first screen could not reproduce the first table. That is the
    failure this suite exists to name in other people's work — a number that
    looks checkable and is not.
    """
    prose = (ROOT / "README.md").read_text(encoding="utf-8")
    shipped = re.search(
        r'^version = "([^"]+)"',
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        re.MULTILINE,
    ).group(1)
    traps = len([p for p in discover(ROOT) if p.population == "trap"])

    stated = re.search(r"release ([0-9.]+) carries the\s+(\d+) traps", prose)
    assert stated, (
        "the README no longer says which release reproduces the results table. "
        "Without it the install line and the numbers can describe different "
        "artifacts, which they did once."
    )
    assert stated.group(1) == shipped, (
        f"the README says release {stated.group(1)} reproduces the table; the "
        f"package in this tree is {shipped}"
    )
    # The released count and the checkout's count are allowed to differ — a trap
    # lands before a release does — but the difference has to be DECLARED. The
    # paragraph promises exactly that ("when the checkout runs ahead of the
    # release this paragraph says so"), and until 2026-08-31 this check could
    # not express it: it demanded the two numbers match, which would have forced
    # either a stale README or a version number naming a release that does not
    # exist on PyPI. Both are the failure the test was written against.
    published = int(stated.group(2))
    if published == traps:
        return
    ahead = re.search(r"this checkout has\s+(\d+)\s+traps", prose)
    assert ahead, (
        f"the README says release {shipped} carries {published} traps and this "
        f"tree has {traps}, and nothing on the page says the checkout is ahead. "
        "A reader who installs the release and cannot reproduce the table has "
        "been told something untrue — which is the failure this suite names in "
        "other people's work."
    )
    assert int(ahead.group(1)) == traps, (
        f"the README says the checkout has {ahead.group(1)} traps; it has {traps}"
    )


def test_the_archive_metadata_uses_a_licence_identifier_zenodo_resolves():
    """SPDX and Zenodo disagree about case, and the disagreement is invisible.

    CFF requires SPDX identifiers, which are written `Apache-2.0`. Zenodo's
    licence vocabulary is keyed lowercase, and `Apache-2.0` returns 404 against
    it while `apache-2.0` resolves. So a CITATION.cff that is correct by its own
    standard produces an identifier the archive does not recognise.

    That is why `.zenodo.json` exists here at all: it is not extra metadata for
    its own sake, it is the one file that can say the licence in the form the
    archive reads. The sibling repository learned this by having a release fail
    with no DOI — a list of licences there, a capital letter here, the same
    class of defect.
    """
    import json

    metadata = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))

    licence = metadata.get("license")
    assert isinstance(licence, str), (
        f"license must be a single string, got {type(licence).__name__}: {licence!r}"
    )
    assert licence == licence.lower(), (
        f"Zenodo's licence identifiers are lowercase and it 404s on anything else; "
        f"{licence!r} would not resolve"
    )

    shipped = re.search(
        r'^version = "([^"]+)"',
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        re.MULTILINE,
    ).group(1)
    assert metadata["version"] == shipped, (
        f".zenodo.json archives {metadata['version']} while the package is {shipped}. "
        f"Zenodo reads this file from inside the tag, so a release cannot fix it after."
    )


def test_the_archive_metadata_does_not_contradict_the_citation_file():
    """Zenodo ignores CITATION.cff entirely when .zenodo.json is present, so the
    two hold the same facts twice and nothing at release time would notice them
    drifting apart. This is the cost of the previous test's fix, paid here."""
    import json

    metadata = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")

    title = re.search(r'^title:\s*"(.+)"', citation, re.MULTILINE)
    assert title, "CITATION.cff has no title"
    assert metadata["title"] == title.group(1), (
        f".zenodo.json titles the record {metadata['title']!r}; CITATION.cff says "
        f"{title.group(1)!r}"
    )
    for creator in (c["name"] for c in metadata["creators"]):
        assert creator in citation, (
            f".zenodo.json credits {creator!r}, absent from CITATION.cff"
        )


def traps_in_tag(tag: str) -> int | None:
    """How many traps the tagged commit actually carries, or None if unknowable.

    None means the tag is not in this checkout: either the release has not been
    cut yet, or somebody cloned shallow. Both are real, and neither is a defect
    in the README — so the caller must not treat None as a failure.
    """
    import subprocess

    try:
        listing = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", tag, "--", "traps/"],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if listing.returncode != 0:
        return None
    return len([line for line in listing.stdout.splitlines() if line.endswith("probe.toml")])


def families_in_tag(tag: str) -> int | None:
    """How many distinct families the tagged commit carries, or None if unknowable."""
    import subprocess

    try:
        found = subprocess.run(
            # The pathspec and the `=` both matter. Two trap READMEs open a line
            # with the word "family", and a looser pattern counted them: the
            # first version of this helper reported 30 families where there are
            # 28, which is a guard measuring something adjacent to the claim.
            ["git", "grep", "-h", "-E", "^family[[:space:]]*=", tag,
             "--", "traps/*/probe.toml"],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if found.returncode != 0:
        return None
    names = {
        line.split("=", 1)[1].strip().strip('"')
        for line in found.stdout.splitlines()
        if "=" in line
    }
    return len(names) or None


def test_the_trap_count_credited_to_a_release_is_the_count_that_release_carries():
    """The count attributed to the release was taken on faith, and it was wrong.

    Until 2026-08-31 the README said release 0.3.0 carried 29 traps. The tag
    carries 23, and so does the wheel on PyPI — a reader who installed it and
    counted would have found six probes missing, which is the 0.1.0 defect this
    file already has a test for, recurring under that test's nose.

    It recurred because the existing check verifies the *checkout* count and
    takes the *released* count as given: adding traps and bumping the released
    number instead of the ahead-of-release number passed cleanly. The released
    artifact cannot change, so its count is a fact with exactly one source —
    the commit the release was cut from.

    Skipped only when the tag is genuinely absent: between the release commit
    and the tag, and in a shallow clone. CI fetches tags so that this test runs
    there rather than quietly passing.
    """
    prose = README
    stated = re.search(
        r"release ([0-9.]+) carries the\s+(\d+) traps and (\d+) families", prose
    )
    assert stated, "the README no longer names the release that reproduces the table"
    version, credited = stated.group(1), int(stated.group(2))
    credited_families = int(stated.group(3))

    actual = traps_in_tag(f"v{version}")
    if actual is None:
        shipped = re.search(
            r'^version = "([^"]+)"',
            (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
            re.MULTILINE,
        ).group(1)
        assert version == shipped, (
            f"the README credits release {version}, which is neither tagged in this "
            f"checkout nor the version being prepared ({shipped}) — so nothing can "
            f"confirm the count it claims"
        )
        return

    assert credited == actual, (
        f"the README says release {version} carries {credited} traps; the tag "
        f"v{version} carries {actual}. The released artifact cannot change, so "
        f"this number cannot move — when the checkout gains traps, the sentence "
        f"that changes is the one saying the checkout is ahead."
    )

    # The sibling number in the same sentence, and it was wrong in the same way:
    # 0.3.0 was credited with 27 families and the tag carries 26. Guarding half
    # a sentence is how the other half drifts.
    actual_families = families_in_tag(f"v{version}")
    assert actual_families is not None, (
        f"the traps in tag v{version} could be counted but its families could not, "
        f"which means the two counts are being read in incompatible ways"
    )
    assert credited_families == actual_families, (
        f"the README says release {version} carries {credited_families} families; "
        f"the tag v{version} carries {actual_families}"
    )


def test_the_published_doi_is_the_concept_doi():
    """Two DOIs exist per release and only one is safe to write down.

    Zenodo mints a version DOI for each release and one concept DOI that always
    resolves to the newest. A version DOI hard-coded into a file nobody re-reads
    becomes a citation for a superseded release the moment the next one lands —
    the same defect as a stale trap count, in a field that looks permanent.
    """
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    # The site too: it is the surface a researcher reaches first, and it carried
    # no DOI at all for the whole morning after one was minted. A citation that
    # exists only in the repository is a citation the people who cite did not see.
    site = (ROOT / "site" / "index.template.html").read_text(encoding="utf-8")

    in_readme = set(re.findall(r"10\.5281/zenodo\.(\d+)", README))
    in_citation = set(re.findall(r"10\.5281/zenodo\.(\d+)", citation))
    in_site = set(re.findall(r"10\.5281/zenodo\.(\d+)", site))

    assert in_readme, "the README publishes no DOI"
    assert in_citation, "CITATION.cff carries no DOI"
    assert in_site, "argleton.org publishes no DOI, and it is where a citer lands"
    assert in_readme == in_citation == in_site, (
        f"the README cites zenodo.{sorted(in_readme)}, CITATION.cff cites "
        f"zenodo.{sorted(in_citation)} and the site cites zenodo.{sorted(in_site)}"
    )
    assert len(in_readme) == 1, (
        f"more than one DOI is published: {sorted(in_readme)}. Only the concept "
        f"DOI belongs in a file that is not rewritten at every release."
    )
