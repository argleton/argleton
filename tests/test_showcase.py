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
    "twenty-four": 24, "twenty-five": 25,
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

    stated = re.search(r"\*\*([A-Za-z]+) are implemented\.\*\*", families_md)
    assert stated, "FAMILIES.md no longer states how many families are implemented"
    assert NUMBER_WORDS[stated.group(1).lower()] == implemented, "FAMILIES.md implemented count"

    covered = re.search(r"([A-Za-z-]+) families of ([a-z-]+)", README)
    assert covered, "the README no longer states its coverage"
    assert NUMBER_WORDS[covered.group(1).lower()] == implemented, "README implemented count"
    assert NUMBER_WORDS[covered.group(2)] == planned, "README planned count"

    family_table = re.findall(r"^\| `([a-z-]+)` \|", README, re.MULTILINE)
    assert len(family_table) == implemented, "README family table row count"


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


def test_every_live_family_count_in_public_markdown_is_current():
    """The stale-caveat defect, one directory over. `results/README.md` carried
    "three families of twelve" in the section the front page links as *what the
    numbers do not say* — four families after it stopped being true, and in the
    one paragraph whose whole job is to keep a reader from over-reading a 0.00.

    Present tense marks a live claim. A past-tense sentence about a superseded
    run is a record of what was claimed then and stays exactly as written.
    """
    implemented = len({p.family for p in discover(ROOT) if p.population == "trap"})
    planned = len(set(re.findall(
        r"^\|\s*(\d+)\s*\|",
        (ROOT / "docs" / "FAMILIES.md").read_text(encoding="utf-8"),
        re.MULTILINE,
    )))
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
