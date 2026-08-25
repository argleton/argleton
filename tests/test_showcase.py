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
    "thirteen": 13, "fourteen": 14, "fifteen": 15,
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

    covered = re.search(r"([A-Za-z]+) families of ([a-z]+)", README)
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
