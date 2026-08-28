"""Build the Argleton site from the repository's own numbers.

Every figure on this page comes out of `results/`, which comes out of running
the suite. Nothing is typed in by hand — a benchmark whose front page is
maintained separately from its results will disagree with them, and the first
person to notice will be right to stop reading.

    python site/build.py [output-dir]
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
CANONICAL = "argleton.org"

# The share card. Rendered rather than drawn by hand, so it cannot drift from
# the probe it quotes: the numbers come from the same discover() the page uses.
CARD = (1200, 630)
# CI is where the published image is made, and CI is Linux with DejaVu — that
# is what makes the published bytes deterministic. A local build may pick a
# different face and produce a different (equally correct) picture; only the
# one CI uploads is served.
FONTS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
)

# The order systems appear in the table. Ours first, deliberately: a suite whose
# authors are not at the top of their own list is hiding something.
ORDER = ["MapSmith", "rasterio", "GeoPandas", "whitebox", "naive"]


def latest_run() -> tuple[str, list[dict]]:
    """The published run and everything in it (see `argleton.published`)."""
    # Runs from a checkout as well as from an install: the page must be
    # buildable without `pip install -e .` first.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from argleton.published import published_run

    latest = published_run(ROOT)
    data = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(latest.glob("*.json"))]
    data.sort(key=lambda d: next(
        (i for i, k in enumerate(ORDER) if d["system"].startswith(k)), len(ORDER)
    ))
    return latest.name, data


def planned_families() -> int:
    """Every family FAMILIES.md numbers, implemented or not.

    Counted from the document rather than hardcoded in the template: a
    hand-typed "nine more" survived two family additions on the published page
    before anyone noticed it had gone stale.
    """
    text = (ROOT / "docs" / "FAMILIES.md").read_text(encoding="utf-8")
    return len(set(re.findall(r"^\|\s*(\d+)\s*\|", text, re.MULTILINE)))


ORDINALS = {
    1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth",
    7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth", 11: "eleventh",
    12: "twelfth", 13: "thirteenth", 14: "fourteenth", 15: "fifteenth",
    16: "sixteenth", 17: "seventeenth", 18: "eighteenth", 19: "nineteenth",
    20: "twentieth", 21: "twenty-first", 22: "twenty-second",
    23: "twenty-third", 24: "twenty-fourth", 25: "twenty-fifth",
    26: "twenty-sixth", 27: "twenty-seventh", 28: "twenty-eighth",
}


def next_ordinal() -> str:
    """The word for the family after the last one named, spelled out.

    This exists because the sentence "bring a thirteenth" survived seven family
    additions on the published page, two lines under generated text reading
    "20 families of 25". `planned_families()` was written after the same mistake
    in the sentence above it, and the fix landed on one line and not the other.
    An ordinal is a count; a count on this site is computed.
    """
    following = planned_families() + 1
    return ORDINALS.get(following, f"{following}th")


def probes() -> list[dict]:
    sys.path.insert(0, str(ROOT))
    from argleton.model import discover

    return [
        {
            "id": p.id, "family": p.family, "population": p.population, "title": p.title,
            "truth": p.truth.value,
            "naive": p.naive_failure.observed_value if p.naive_failure else None,
            "why": (p.naive_failure.why_plausible.strip().split("\n\n")[0].replace("\n", " ")
                    if p.naive_failure else None),
        }
        for p in discover(ROOT)
    ]


def _number(value) -> str:
    if value is None:
        return "—"
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text if text else "0"


def results_table(data: list[dict]) -> str:
    rows = []
    for d in data:
        ours = d["system"].startswith("MapSmith")
        silent = d["silent_error_rate"]
        cls = "bad" if silent and silent > 0 else "good"
        rows.append(
            f'<tr{" class=ours" if ours else ""}>'
            f'<td class="sys">{html.escape(d["system"])}'
            f'{" <span class=tag>ours</span>" if ours else ""}</td>'
            f'<td class="num {cls}">{_number(silent)}</td>'
            f'<td class="num">{_number(d["completion_rate"])}</td>'
            f'<td class="num dim">{d["traps_run"]}</td>'
            f'<td class="num dim">{d["unsupported"]}</td></tr>'
        )
    return "\n".join(rows)


def families_table(probe_list: list[dict]) -> str:
    rows = []
    for p in sorted(probe_list, key=lambda p: p["id"]):
        if p["population"] != "trap":
            continue
        rows.append(
            "<tr>"
            f'<td class="mono">{html.escape(p["family"])}</td>'
            f'<td>{html.escape(p["title"])}</td>'
            f'<td class="num good">{p["truth"]}</td>'
            f'<td class="num bad">{p["naive"]}</td></tr>'
        )
    return "\n".join(rows)


def share_card(destination: Path, truth, naive) -> None:
    """The two numbers, 1200x630, for the card a link becomes on a social feed.

    A page whose argument is numerical shares badly as a text snippet, and this
    site had no `og:image` at all — so the artefact carrying the strongest thing
    the project has was the one that shared worst. The card is the argument:
    the right answer, the wrong one, and the line that makes it uncomfortable.
    """
    from PIL import Image, ImageDraw, ImageFont

    path = next((f for f in FONTS if Path(f).exists()), None)
    if path is None:
        raise RuntimeError(f"no usable font found; looked for {FONTS}")

    def font(size: int):
        return ImageFont.truetype(path, size)

    ink, background = (0xE6, 0xEA, 0xF0), (0x0C, 0x0E, 0x12)
    muted, good, bad = (0x7D, 0x88, 0x95), (0x35, 0xC6, 0x9B), (0xF0, 0x65, 0x5A)

    canvas = Image.new("RGB", CARD, background)
    draw = ImageDraw.Draw(canvas)
    draw.text((64, 54), "ARGLETON", font=font(28), fill=muted)
    draw.text((64, 96), "A correctness suite for geospatial systems",
                 font=font(34), fill=ink)
    draw.line([(64, 168), (CARD[0] - 64, 168)], fill=(0x24, 0x2A, 0x33), width=1)

    for x, value, color, label in (
        (64, truth, good, "THE ANSWER"),
        (620, naive, bad, "WHAT ONE LIBRARY RETURNS"),
    ):
        draw.text((x, 214), label, font=font(22), fill=muted)
        draw.text((x, 252), str(value), font=font(104), fill=color)

    draw.text((64, 408), "From the same file. No crash, no warning,",
                 font=font(32), fill=ink)
    draw.text((64, 452), "nothing in the log.", font=font(32), fill=ink)
    draw.text((64, 528), "Both are ordinary elevations.", font=font(30), fill=muted)
    draw.text((64, 566), CANONICAL, font=font(26), fill=bad)
    canvas.save(destination, format="PNG", optimize=True)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True, text=True, check=False,
    ).stdout.strip()


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    run_id, data = latest_run()
    probe_list = probes()
    traps = [p for p in probe_list if p["population"] == "trap"]
    zero = next(p for p in traps if p["id"].startswith("001"))

    replacements = {
        "{{RESULTS_ROWS}}": results_table(data),
        "{{FAMILY_ROWS}}": families_table(probe_list),
        "{{RUN}}": run_id,
        "{{SPEC_COMMIT}}": data[0]["spec_commit"],
        "{{TRUTH}}": str(zero["truth"]),
        "{{NAIVE}}": str(zero["naive"]),
        "{{TRAPS}}": str(len(traps)),
        "{{FAMILIES}}": str(len({p["family"] for p in traps})),
        "{{FAMILIES_PLANNED}}": str(planned_families()),
        "{{NEXT_ORDINAL}}": next_ordinal(),
        "{{FAMILIES_REMAINING}}": str(planned_families() - len({p["family"] for p in traps})),
        "{{PROBES}}": str(len(probe_list)),
        "{{SYSTEMS}}": str(len(data)),
        "{{COMMIT}}": _git("rev-parse", "--short", "HEAD") or "unknown",
        "{{CANONICAL}}": CANONICAL,
    }
    share_card(destination / "card.png", zero["truth"], zero["naive"])

    page = (Path(__file__).parent / "index.template.html").read_text(encoding="utf-8")
    for placeholder, value in replacements.items():
        page = page.replace(placeholder, value)
    if "{{" in page:
        raise RuntimeError(f"unreplaced placeholder: {page[page.index('{{'):][:50]}")

    (destination / "index.html").write_text(page, encoding="utf-8")
    (destination / ".nojekyll").write_text("", encoding="utf-8")
    (destination / "CNAME").write_text(CANONICAL + "\n", encoding="utf-8")
    print(
        f"index.html {(destination / 'index.html').stat().st_size // 1024} KB | "
        f"card.png {(destination / 'card.png').stat().st_size // 1024} KB | "
        f"{len(data)} systems, {len(traps)} traps, "
        f"{len({p['family'] for p in traps})} families | run {run_id}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "site" / "generated"))
    )
