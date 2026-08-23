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
    """The most recent results directory, and everything in it."""
    corse = sorted(p for p in RESULTS.iterdir() if p.is_dir())
    if not corse:
        raise RuntimeError("no results yet — run the suite before building the page")
    ultima = corse[-1]
    dati = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(ultima.glob("*.json"))]
    dati.sort(key=lambda d: next(
        (i for i, k in enumerate(ORDER) if d["system"].startswith(k)), len(ORDER)
    ))
    return ultima.name, dati


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


def _numero(valore) -> str:
    if valore is None:
        return "—"
    testo = f"{valore:.4f}".rstrip("0").rstrip(".")
    return testo if testo else "0"


def tabella_risultati(dati: list[dict]) -> str:
    righe = []
    for d in dati:
        nostro = d["system"].startswith("MapSmith")
        silent = d["silent_error_rate"]
        classe = "bad" if silent and silent > 0 else "good"
        righe.append(
            f'<tr{" class=ours" if nostro else ""}>'
            f'<td class="sys">{html.escape(d["system"])}'
            f'{" <span class=tag>ours</span>" if nostro else ""}</td>'
            f'<td class="num {classe}">{_numero(silent)}</td>'
            f'<td class="num">{_numero(d["completion_rate"])}</td>'
            f'<td class="num dim">{d["traps_run"]}</td>'
            f'<td class="num dim">{d["unsupported"]}</td></tr>'
        )
    return "\n".join(righe)


def tabella_famiglie(elenco: list[dict]) -> str:
    righe = []
    for p in sorted(elenco, key=lambda p: p["id"]):
        if p["population"] != "trap":
            continue
        righe.append(
            "<tr>"
            f'<td class="mono">{html.escape(p["family"])}</td>'
            f'<td>{html.escape(p["title"])}</td>'
            f'<td class="num good">{p["truth"]}</td>'
            f'<td class="num bad">{p["naive"]}</td></tr>'
        )
    return "\n".join(righe)


def share_card(destination: Path, truth, naive) -> None:
    """The two numbers, 1200x630, for the card a link becomes on a social feed.

    A page whose argument is numerical shares badly as a text snippet, and this
    site had no `og:image` at all — so the artefact carrying the strongest thing
    the project has was the one that shared worst. The card is the argument:
    the right answer, the wrong one, and the line that makes it uncomfortable.
    """
    from PIL import Image, ImageDraw, ImageFont

    percorso = next((f for f in FONTS if Path(f).exists()), None)
    if percorso is None:
        raise RuntimeError(f"no usable font found; looked for {FONTS}")

    def font(dimensione: int):
        return ImageFont.truetype(percorso, dimensione)

    inchiostro, sfondo = (0xE6, 0xEA, 0xF0), (0x0C, 0x0E, 0x12)
    tenue, giusto, sbagliato = (0x7D, 0x88, 0x95), (0x35, 0xC6, 0x9B), (0xF0, 0x65, 0x5A)

    tela = Image.new("RGB", CARD, sfondo)
    disegno = ImageDraw.Draw(tela)
    disegno.text((64, 54), "ARGLETON", font=font(28), fill=tenue)
    disegno.text((64, 96), "A correctness suite for geospatial systems",
                 font=font(34), fill=inchiostro)
    disegno.line([(64, 168), (CARD[0] - 64, 168)], fill=(0x24, 0x2A, 0x33), width=1)

    for x, valore, colore, etichetta in (
        (64, truth, giusto, "THE ANSWER"),
        (620, naive, sbagliato, "WHAT ONE LIBRARY RETURNS"),
    ):
        disegno.text((x, 214), etichetta, font=font(22), fill=tenue)
        disegno.text((x, 252), str(valore), font=font(104), fill=colore)

    disegno.text((64, 408), "From the same file. No crash, no warning,",
                 font=font(32), fill=inchiostro)
    disegno.text((64, 452), "nothing in the log.", font=font(32), fill=inchiostro)
    disegno.text((64, 528), "Both are ordinary elevations.", font=font(30), fill=tenue)
    disegno.text((64, 566), CANONICAL, font=font(26), fill=sbagliato)
    tela.save(destination, format="PNG", optimize=True)


def _git(*argomenti: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *argomenti],
        capture_output=True, text=True, check=False,
    ).stdout.strip()


def main(destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    corsa, dati = latest_run()
    elenco = probes()
    trappole = [p for p in elenco if p["population"] == "trap"]
    zero = next(p for p in trappole if p["id"].startswith("001"))

    sostituzioni = {
        "{{RESULTS_ROWS}}": tabella_risultati(dati),
        "{{FAMILY_ROWS}}": tabella_famiglie(elenco),
        "{{RUN}}": corsa,
        "{{SPEC_COMMIT}}": dati[0]["spec_commit"],
        "{{TRUTH}}": str(zero["truth"]),
        "{{NAIVE}}": str(zero["naive"]),
        "{{TRAPS}}": str(len(trappole)),
        "{{FAMILIES}}": str(len({p["family"] for p in trappole})),
        "{{PROBES}}": str(len(elenco)),
        "{{SYSTEMS}}": str(len(dati)),
        "{{COMMIT}}": _git("rev-parse", "--short", "HEAD") or "unknown",
        "{{CANONICAL}}": CANONICAL,
    }
    share_card(destination / "card.png", zero["truth"], zero["naive"])

    pagina = (Path(__file__).parent / "index.template.html").read_text(encoding="utf-8")
    for segnaposto, valore in sostituzioni.items():
        pagina = pagina.replace(segnaposto, valore)
    if "{{" in pagina:
        raise RuntimeError(f"unreplaced placeholder: {pagina[pagina.index('{{'):][:50]}")

    (destination / "index.html").write_text(pagina, encoding="utf-8")
    (destination / ".nojekyll").write_text("", encoding="utf-8")
    (destination / "CNAME").write_text(CANONICAL + "\n", encoding="utf-8")
    print(
        f"index.html {(destination / 'index.html').stat().st_size // 1024} KB | "
        f"card.png {(destination / 'card.png').stat().st_size // 1024} KB | "
        f"{len(dati)} systems, {len(trappole)} traps, "
        f"{len({p['family'] for p in trappole})} families | run {corsa}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "site" / "generated"))
    )
