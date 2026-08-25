"""Adapter: MapSmith, the system these probes were written next to.

Here on purpose and first, because a suite whose authors do not measure
themselves is not a suite. What it finds about MapSmith goes in `results/`
whatever it says.

Two things worth stating before the numbers.

**MapSmith exposes no `raster_mean` and no area operation.** It exposes
`zonal_statistics`, so that is what this adapter calls, with a zone covering the
raster's own extent — which is how you ask MapSmith the question. Composing a
system's real tools to answer the probe is the adapter's whole job; inventing an
operation it does not have would measure a system that does not exist. For
`planar_area_m2` there is nothing to compose, and the honest answer is
`unsupported`.

**There is no switch to turn MapSmith's verification off**, and adding one to a
product whose argument is that it verifies would be a footgun someone eventually
ships with. So this measures MapSmith as it is released. On the families
implemented so far that turns out not to matter, and the reason is worth reading
in `results/`.
"""

from __future__ import annotations

from pathlib import Path

from argleton.model import Outcome, Probe


class Adapter:
    name = "mapsmith"

    def run(self, probe: Probe, workdir: Path) -> Outcome:
        operation = getattr(self, f"op_{probe.operation}", None)
        if operation is None:
            return Outcome(unsupported=True)
        return operation(probe, workdir)

    def op_raster_mean(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        import rasterio
        from mapsmith.engines import raster
        from shapely.geometry import box

        source = workdir / probe.arguments[0]
        with rasterio.open(source) as ds:
            bounds, crs = ds.bounds, ds.crs
        if crs is None:
            return Outcome(refusal="the raster declares no CRS, so a zone cannot be placed on it")

        # A zone that is exactly the raster's extent. exactextract weights
        # partial pixels rather than counting or dropping them, so a zone on the
        # grid boundary is the whole grid and nothing is double-counted.
        zone = workdir / "_argleton_extent.gpkg"
        gpd.GeoDataFrame(
            {"zone": [1]}, geometry=[box(*bounds)], crs=crs
        ).to_file(zone, layer="zone", driver="GPKG")

        output = workdir / "_argleton_zonal.parquet"
        try:
            raster.zonal_statistics(str(source), str(zone), str(output), stats=["mean"])
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            text = str(exc)
            # MapSmith refuses rather than guesses in several places, and a
            # refusal that names its reason is a different result from a crash.
            if "has no CRS" in text or "Refusing" in text:
                return Outcome(refusal=text)
            return Outcome(error=f"{type(exc).__name__}: {text}")

        result = gpd.read_parquet(output)
        warns = self._warnings(output)
        return Outcome(answer=float(result["mean"].iloc[0]), warnings=warns)

    def op_feature_count(self, probe: Probe, workdir: Path) -> Outcome:
        from mapsmith.engines import dispatch

        # The composition that measured the 2026-08-25 silent error is one
        # line shorter than this: describe_dataset used to answer about the
        # container's default layer with no trace (MapSmith issue #29, caught
        # by this trap). Since the fix, describe returns a per-layer summary
        # for containers, and the composition picks the layer the question
        # names — which is now possible, which was the point.
        result = dispatch.describe_routed(str(workdir / probe.arguments[0]))
        if result.get("kind") == "vector-container":
            layer = probe.arguments[1].split("=", 1)[1]
            entry = next(e for e in result["layers"] if e["layer"] == layer)
            return Outcome(answer=int(entry["feature_count"]))
        return Outcome(answer=int(result["feature_count"]))

    def op_points_in_polygon_count(self, probe: Probe, workdir: Path) -> Outcome:
        from mapsmith.engines import vector

        output = workdir / "_argleton_join.parquet"
        try:
            # MapSmith exposes no point-in-polygon count; it exposes
            # `spatial_join`, so the composition is a within-join of the points
            # against the zone, counting the joined rows. There is exactly one
            # zone, so no point can be counted twice.
            result = vector.spatial_join(
                str(workdir / probe.arguments[0]),
                str(workdir / probe.arguments[1]),
                str(output),
                predicate="within",
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            text = str(exc)
            if "has no CRS" in text or "Refusing" in text:
                return Outcome(refusal=text)
            return Outcome(error=f"{type(exc).__name__}: {text}")
        return Outcome(answer=int(result["feature_count"]), warnings=self._warnings(output))

    def op_count_within_distance(self, probe: Probe, workdir: Path) -> Outcome:
        import geopandas as gpd
        from mapsmith.engines import vector

        source = workdir / probe.arguments[0]
        target_id = probe.arguments[1].split("=", 1)[1]
        distance = float(probe.arguments[2].split("=", 1)[1])

        # The composition a MapSmith client writes: select the target (glue),
        # buffer_layer — whose contract is METERS, with the UTM decision
        # recorded when the layer is geographic — then a within-join and a
        # count. The target sits inside its own buffer, hence the minus one.
        frame = gpd.read_file(source)
        target_path = workdir / "_argleton_target.gpkg"
        frame[frame["well_id"] == target_id].to_file(
            target_path, layer="target", driver="GPKG"
        )
        buffered = workdir / "_argleton_buffer.parquet"
        joined = workdir / "_argleton_within.parquet"
        try:
            vector.buffer(str(target_path), distance, str(buffered))
            result = vector.spatial_join(
                str(source), str(buffered), str(joined), predicate="within"
            )
        except Exception as exc:  # noqa: BLE001 — a refusal and a crash are different verdicts
            text = str(exc)
            if "has no CRS" in text or "Refusing" in text or "no layer was chosen" in text:
                return Outcome(refusal=text)
            return Outcome(error=f"{type(exc).__name__}: {text}")
        return Outcome(
            answer=int(result["feature_count"]) - 1, warnings=self._warnings(joined)
        )

    @staticmethod
    def _warnings(output: Path) -> list[str]:
        """Anything the manifest recorded that a reader should have seen.

        A check that failed non-critically, or a repair, is MapSmith telling the
        caller something. If it is there, the probe should be scored as
        `correct_with_warning` rather than plain `correct` — the suite is about
        what a system communicates, not only about the number.
        """
        import json

        manifest = Path(str(output) + ".provenance.json")
        if not manifest.exists():
            return ["no provenance manifest was written"]
        data = json.loads(manifest.read_text(encoding="utf-8"))
        note = [c["detail"] for c in data.get("verification", []) if not c.get("passed")]
        note += [r.get("detail", str(r)) for r in data.get("repairs", [])]
        return note
