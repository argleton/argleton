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
        f"{len(dati)} systems, {len(trappole)} traps, "
        f"{len({p['family'] for p in trappole})} families | run {corsa}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "site" / "generated"))
    )
