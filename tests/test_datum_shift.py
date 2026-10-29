from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import geopandas as gpd
import pytest
from shapely.geometry import Point

from adapters.engine_geopandas import Adapter

PARAMETERS = "-104.1,-49.1,-9.9,0.971,-2.917,0.714,-11.68"


def _station(path, parameters):
    gpd.GeoDataFrame(
        {"station_id": ["ST-1"]},
        geometry=[Point(8.952333333333333, 45.5)],
        crs=(
            "+proj=longlat +ellps=intl "
            f"+towgs84={parameters} +no_defs +type=crs"
        ),
    ).to_file(path, layer="stations", driver="GPKG")


def _run(path):
    probe = SimpleNamespace(operation="wgs84_latitude", arguments=("station.gpkg",))
    return Adapter().run(probe, path)


def test_declared_helmert_is_not_mistaken_for_a_ballpark(tmp_path):
    path = tmp_path / "station.gpkg"
    _station(path, PARAMETERS)

    result = _run(tmp_path)

    assert result.refusal is None
    assert result.answer == pytest.approx(45.500669073852286, abs=1e-9)


def test_declared_zero_shift_is_not_mistaken_for_a_ballpark(tmp_path):
    path = tmp_path / "station.gpkg"
    _station(path, "0,0,0")

    result = _run(tmp_path)

    assert result.refusal is None
    assert result.answer == pytest.approx(45.49917801907832, abs=1e-12)


def test_a_false_ballpark_refusal_is_scored_as_wrong():
    from argleton.model import Outcome, load_probe
    from argleton.score import judge

    probe = load_probe(
        Path(__file__).parent.parent / "traps/033-declared-datum-shift"
    )
    outcome = Outcome(
        refusal="every available transformation is a ballpark one, so no datum shift can be applied"
    )

    assert judge(probe, outcome).verdict == "refused_wrongly"


def test_real_ballpark_still_uses_the_published_alternative(tmp_path):
    path = tmp_path / "station.gpkg"
    gpd.GeoDataFrame(
        {"station_id": ["ST-1"]}, geometry=[Point(-3.5, 45.5)], crs="EPSG:4806"
    ).to_file(path, layer="stations", driver="GPKG")

    result = _run(tmp_path)

    assert result.refusal is None
    assert result.answer == pytest.approx(45.500669073852286, abs=0.00009)
    assert any("ballpark" in warning for warning in result.warnings)


def test_published_operation_with_stated_accuracy_stays_direct(tmp_path):
    path = tmp_path / "station.gpkg"
    gpd.GeoDataFrame(
        {"station_id": ["ST-1"]},
        geometry=[Point(8.952333333333333, 45.5)], crs="EPSG:4265",
    ).to_file(path, layer="stations", driver="GPKG")

    result = _run(tmp_path)

    assert result.refusal is None
    assert result.answer == pytest.approx(45.500669073852286, abs=1e-9)
    assert result.warnings == []
