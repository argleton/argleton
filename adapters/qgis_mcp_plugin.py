"""Adapter: `nkarasiak/qgis-mcp`, spoken to over its plugin socket.

The system is two pieces — a QGIS plugin that opens a TCP socket, and a separate
MCP server on stdio that forwards to it. **This adapter talks to the socket**, so
what it measures is the plugin: the thing that actually reaches QGIS. The MCP
server above it is a translator with no geoprocessing of its own, and going
through it would have added `uv`, a download at first run, and a second version
number to pin, for the same arithmetic. The distinction is stated here rather
than left to the label, because "measured the plugin" and "measured the MCP
server" are two different claims and only one of them is true of this row.

The chains come from `QgisChains`, shared with the headless engine adapter and
with the other QGIS MCP server, so a difference between those three rows can
only come from the system, never from a chain that drifted.

**Two things this surface cannot do, and both change what its numbers mean.**

- **The ellipsoid is not a parameter.** `execute_processing` forwards to
  `processing.run` inside a live QGIS, and `$area` there obeys the *project's*
  ellipsoid — `EPSG:7030` in a default project. A caller who wants a planar area
  has nowhere to say so. The headless row, running with no project at all, gets
  the planar answer instead: on 002-feet-as-metres that is 1000000.0 against
  92899.397, a factor of 10.8 between two systems that are the same QGIS.
- **Every reply is wrapped in `status: "success"`.** That is the envelope, not a
  claim about the answer, and it is the same shape this project reported to
  gis-mcp in its issue #45 — where four of twenty probes came back wrong under
  it. Recorded here so the row can be read against that one.
"""

from __future__ import annotations

import json
import socket
import struct
from pathlib import Path

from adapters.qgis_chains import QgisChains

HOST = "127.0.0.1"
PORT = 9876
# The plugin frames every message with a 4-byte big-endian length. Read from its
# own `wire.py` rather than guessed: a framing taken on faith would desynchronise
# the stream on the first long reply and look like the system hanging.
HEADER = struct.Struct(">I")
LIMIT = 10 * 1024 * 1024

# Values that name a file get made absolute before they leave. The plugin runs
# inside QGIS, whose working directory is not the probe's, so a relative name
# would resolve somewhere else entirely — and for an OUTPUT that failure is
# silent: the algorithm succeeds, the file lands elsewhere, and the next step
# reads a stale one or nothing.
DATA = (".gpkg", ".geojson", ".tif", ".tiff", ".csv", ".shp", ".json")


class Adapter(QgisChains):
    name = "qgis-mcp"

    def __init__(self) -> None:
        self._socket: socket.socket | None = None

    def _connect(self) -> socket.socket:
        if self._socket is None:
            try:
                self._socket = socket.create_connection((HOST, PORT), timeout=600)
            except OSError as failure:
                raise RuntimeError(
                    f"no qgis-mcp plugin listening on {HOST}:{PORT} ({failure}). "
                    "Start QGIS with the plugin's 'Run MCP' toggle on, or tick "
                    "'Auto-start on startup' once."
                ) from failure
        return self._socket

    def _send(self, kind: str, params: dict) -> dict:
        connection = self._connect()
        body = json.dumps({"type": kind, "params": params}).encode("utf-8")
        connection.sendall(HEADER.pack(len(body)) + body)
        head = self._exactly(connection, HEADER.size)
        (length,) = HEADER.unpack(head)
        if length > LIMIT:
            raise RuntimeError(f"{kind}: reply of {length} bytes exceeds the protocol limit")
        reply = json.loads(self._exactly(connection, length).decode("utf-8"))
        if reply.get("status") != "success":
            raise RuntimeError(f"{kind}: {json.dumps(reply, ensure_ascii=False)[:600]}")
        return reply.get("result") or {}

    @staticmethod
    def _exactly(connection: socket.socket, count: int) -> bytes:
        chunks = b""
        while len(chunks) < count:
            piece = connection.recv(count - len(chunks))
            if not piece:
                raise RuntimeError("the plugin closed the connection mid-message")
            chunks += piece
        return chunks

    def _call(
        self,
        algorithm: str,
        workdir: Path,
        ellipsoid: str | None = None,
        providers: str = "core",
        **parameters: object,
    ) -> tuple[dict, list[str]]:
        notes: list[str] = []
        if ellipsoid is not None:
            # Said out loud rather than silently dropped: the chain asked for a
            # frame this surface has no way to accept, so the answer is in
            # whatever frame the open project happens to be in.
            notes.append(
                f"the {ellipsoid} ellipsoid the question needs cannot be passed through "
                "execute_processing; the open project's ellipsoid applies instead"
            )
        result = self._send(
            "execute_processing",
            {"algorithm": algorithm, "parameters": _absolute(parameters, workdir)},
        )
        # The algorithm's own outputs sit one level down, under `result`, beside
        # the echoed algorithm id — read from a real reply rather than assumed.
        outputs = result.get("result") if isinstance(result.get("result"), dict) else result
        # And they come back as STRINGS: `"SUM": "92899.39700720413"`,
        # `"COUNT": "1"`. Numbers are numbers again here because the chains do
        # arithmetic on them, and because the difference is the plugin's, not
        # the engine's — recorded rather than papered over, since a consumer
        # that compares or adds without converting gets silence, not an error.
        return {key: _number(value) for key, value in outputs.items()}, notes


def _number(value):
    """A numeric string back to a number, anything else untouched."""
    if not isinstance(value, str):
        return value
    try:
        return float(value) if any(c in value for c in ".eE") else int(value)
    except ValueError:
        return value


def _absolute(parameters: dict, workdir: Path) -> dict:
    resolved = {}
    for key, value in parameters.items():
        if isinstance(value, str):
            head, _, tail = value.partition("|")
            if Path(head).suffix.lower() in DATA and not Path(head).is_absolute():
                value = str(workdir / head) + (f"|{tail}" if tail else "")
        resolved[key] = value
    return resolved
