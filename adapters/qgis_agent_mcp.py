"""Adapter: QGIS Agent MCP, spoken to over its local bridge.

Like `qgis_mcp_plugin`, this talks to the plugin rather than to the MCP server
above it: the server is a translator with no geoprocessing of its own, it is not
on PyPI, and it is reached through a launcher the plugin writes. The bridge is
the surface that reaches QGIS, and saying so is the honest form of the claim.

The chains come from `QgisChains`, shared with the headless engine adapter and
with the other QGIS MCP server, so whatever separates the three rows can only be
the system.

**This one discloses more than any other system in the suite, and the shape of
what it discloses is the interesting part.** Every operation comes back with:

- `live_verification` — named checks (`qgis.result.structured`,
  `result.validation.passed`), a `passed` flag, a count, and a `repair` block
  with `attempted` / `succeeded` / `actions`;
- `validation` — for each output, before and after: existence, size, `mtime_ns`
  and a `sample_sha256`.

That is not nothing, and this file carries it into the record rather than
dropping it. Two things about it are worth stating precisely, because they are
what a reader of this row will want to know. The digest is a **sample** — the
plugin's own `_file_fingerprint` hashes the first and last 64 KiB plus size and
mtime — so it does not identify the bytes of a GeoPackage whose features sit in
between, and a lineage walk that resolves a chain by content cannot be built on
it. And the two checks answer whether the result has the shape it should and
whether the file appeared, not whether the number is right: the same limit this
project published about its own manifests on 2026-08-23.

**The protocol has one trap worth naming.** The bridge pushes asynchronous
`bridge.event` notifications interleaved with replies, so a client that reads
one line per request will eventually take an event for an answer. It reads by
matching the request id instead. Measured 2026-09-14: the first draft did take
an event, and the failure looked like a malformed reply rather than like a
protocol misunderstanding.
"""

from __future__ import annotations

import json
import socket
import time
from pathlib import Path

from adapters.qgis_chains import QgisChains

CONNECTION = Path.home() / ".qgis-mcp" / "connection.json"
DATA = (".gpkg", ".geojson", ".tif", ".tiff", ".csv", ".shp", ".json")
# The states an operation can still LEAVE. Written this way round on purpose: a
# list of terminal states is a guess that goes stale silently, and it did —
# `interrupted` was missing from the first version and a failed Voronoi spun the
# poll for the whole deadline before anyone saw a result. Inverted, an unknown
# status ends the wait instead of hanging, which is the safe direction.
RUNNING = ("queued", "running", "pending")
# How long a non-terminal status is allowed to last before this adapter gives up
# and says so. Every operation in this suite that finishes at all finishes in
# tens of milliseconds, so this is not a performance threshold: it is the line
# past which "still working" stops being a plausible reading. It is a constant
# because the number appears in the record, and a number typed twice disagrees.
PATIENCE_SECONDS = 120


class Adapter(QgisChains):
    name = "qgis-agent-mcp"

    def __init__(self) -> None:
        self._file = None
        self._socket: socket.socket | None = None
        self._id = 0

    def run(self, probe, workdir):
        """The chain, then a fresh session for the next probe.

        One connection per probe so that no state carries from one measurement
        into the next. It does *not* release files, and the first version of
        this docstring said it did — see `_unload`.
        """
        try:
            return super().run(probe, workdir)
        finally:
            self._unload()

    def _unload(self) -> None:
        """End the session. What this does NOT fix is worth more than what it does.

        An earlier version claimed this system holds every input open after an
        operation. **That is false, and the clean-room check is what caught it**:
        from a freshly started QGIS, a file passed to `native:centroids` deletes
        fine the moment the call returns. What actually happens is narrower and
        is one defect, not two — an operation that never reaches a terminal
        status keeps its input layer alive forever, so the file behind it stays
        locked on Windows. The lock is a symptom of the hang (see `_await`), and
        closing the session does not clear it.
        """
        for closeable in (self._file, self._socket):
            try:
                if closeable is not None:
                    closeable.close()
            except OSError:
                pass
        self._file = None
        self._socket = None

    def _connect(self):
        if self._file is None:
            if not CONNECTION.exists():
                raise RuntimeError(
                    f"no QGIS Agent MCP bridge announced at {CONNECTION}. Start QGIS "
                    "with the plugin enabled; the bridge writes this file on load."
                )
            info = json.loads(CONNECTION.read_text(encoding="utf-8"))
            self._socket = socket.create_connection((info["host"], info["port"]), timeout=600)
            self._file = self._socket.makefile("rw", encoding="utf-8", newline="\n")
            self._rpc(
                "bridge.hello",
                {
                    "token": info["token"],
                    "protocol": info["protocol"],
                    "client": "qgis-agent-mcp",
                },
            )
        return self._file

    def _rpc(self, method: str, params: dict) -> dict:
        stream = self._file if self._file is not None else self._connect()
        self._id += 1
        mine = self._id
        stream.write(
            json.dumps({"jsonrpc": "2.0", "id": mine, "method": method, "params": params}) + "\n"
        )
        stream.flush()
        while True:
            line = stream.readline()
            if not line:
                raise RuntimeError(f"{method}: the bridge closed the connection")
            message = json.loads(line)
            # Notifications carry no id. Skipping them by id rather than by
            # shape is what keeps a long operation's progress events from being
            # mistaken for its result.
            if message.get("id") != mine:
                continue
            if "error" in message:
                raise RuntimeError(f"{method}: {json.dumps(message['error'], ensure_ascii=False)}")
            return message["result"]

    def _call(
        self,
        algorithm: str,
        workdir: Path,
        ellipsoid: str | None = None,
        providers: str = "core",
        **parameters: object,
    ) -> tuple[dict, list[str]]:
        self._connect()
        notes: list[str] = []
        if ellipsoid is not None:
            notes.append(
                f"the {ellipsoid} ellipsoid the question needs cannot be passed through "
                "processing.start; the open project's ellipsoid applies instead"
            )
        # `retain_outputs` defaults to true and keeps every output registered
        # inside QGIS, which on Windows holds the file open: the probe's own
        # temporary directory then cannot be removed and the run dies on
        # cleanup, not on the measurement. Turned off because a batch has no use
        # for the handles — and it is not a thumb on the scale: the algorithm,
        # its parameters and its answer are identical either way.
        started = self._rpc(
            "processing.start",
            {
                "algorithm": algorithm,
                "parameters": _absolute(parameters, workdir),
                "retain_outputs": False,
            },
        )
        record = self._await(started["id"], algorithm)
        notes += _disclosures(record)
        if record["status"] != "succeeded":
            raise RuntimeError(f"{algorithm}: {record['status']} — {record.get('error', '')}")
        outputs = record.get("result")
        return (outputs if isinstance(outputs, dict) else {}), notes

    def _await(self, operation: str, algorithm: str) -> dict:
        # The key is `status`, not `state`, and it goes from queued to succeeded
        # in tens of milliseconds. Polling `state` — which does not exist — made
        # every operation look like a timeout on 2026-09-14.
        #
        # The message is BUILT from the same constant it waited on, and it names
        # the last status seen. Written out by hand it said 600 seconds while
        # this loop waited 120, and that sentence reached a published record and
        # an issue filed against somebody else's project: a claim about a third
        # party, five times larger than the observation behind it. A number that
        # appears twice gets to disagree with itself exactly once.
        ultimo = None
        deadline = time.time() + PATIENCE_SECONDS
        while time.time() < deadline:
            record = self._rpc("operation.control", {"operation_id": operation, "action": "status"})
            ultimo = record.get("status")
            if ultimo not in RUNNING:
                return record
            time.sleep(0.05)
        raise RuntimeError(
            f"{algorithm}: still {ultimo!r} after {PATIENCE_SECONDS} seconds, "
            "which is not a terminal status and not an error"
        )


def _disclosures(record: dict) -> list[str]:
    """What the system said about its own result, kept only when it said something.

    A passing check is not a warning and does not belong in a row's warnings — it
    would turn every probe into a `correct_with_warning` and make the column
    meaningless. A failed check, an attempted repair, or a validation issue is
    exactly what this column is for.
    """
    notes = []
    verification = record.get("live_verification") or {}
    if verification and not verification.get("passed", True):
        failed = [c.get("name") for c in verification.get("checks", []) if not c.get("passed")]
        notes.append(f"live_verification did not pass: {', '.join(filter(None, failed))}")
    repair = verification.get("repair") or {}
    if repair.get("attempted"):
        notes.append(
            f"the system repaired its own result (succeeded={repair.get('succeeded')}): "
            f"{repair.get('actions')}"
        )
    validation = record.get("validation") or {}
    for issue in validation.get("issues", []):
        notes.append(f"validation issue: {issue}")
    return notes


def _absolute(parameters: dict, workdir: Path) -> dict:
    resolved = {}
    for key, value in parameters.items():
        if isinstance(value, str):
            head, _, tail = value.partition("|")
            if Path(head).suffix.lower() in DATA and not Path(head).is_absolute():
                value = str(workdir / head) + (f"|{tail}" if tail else "")
        resolved[key] = value
    return resolved
