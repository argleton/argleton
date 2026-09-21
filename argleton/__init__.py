"""Argleton: probes whose right answer is known, and whose wrong answer looks fine."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _installed_version
from pathlib import Path


def _declared() -> str:
    """The one declaration of this package's version, `pyproject.toml`.

    It said `0.1.0.dev0` here while 0.4.0 was on PyPI, across four releases,
    because the number lived in two places and only one of them was on
    anybody's checklist. Nothing read it, so nothing caught it. A suite whose
    subject is whether software describes itself accurately does not get to
    ship a package that answers the wrong version when asked its own.

    Derived both ways, because this package is used both ways. Installed, the
    distribution metadata is authoritative -- it is what the user actually has.
    From a checkout, which is how the suite itself is run, there is no
    distribution to ask, so the declaration is read from the file beside the
    source. Either way there is one number, and it is not this line.
    """
    try:
        return _installed_version("argleton")
    except PackageNotFoundError:
        pass
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    try:
        import tomllib

        return tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
    except (OSError, KeyError, ValueError, ImportError):  # pragma: no cover
        # Neither installed nor beside its own pyproject: say so rather than
        # invent a number, which is the failure this whole function is about.
        return "0+unknown"


__version__ = _declared()
