import pytest

from cms_perf import cli_parser
from cms_perf import sensor


@cli_parser.cli_sensor
def fake_sensor_factory(interval: int, value=1):
    return value


@cli_parser.cli_sensor(name="fake.sensor")
def fake_aliased_sensor_factory(interval: int, value=1):
    return value


SOURCES = [
    "1.0",
    "1337",
    *cli_parser.SENSORS,
    "1.0 / 1337",
    *(f"{sensor} / 20" for sensor in cli_parser.SENSORS),
]


@pytest.mark.parametrize("source", SOURCES)
def test_parse(source: str):
    factory = cli_parser.prepare_sensor(source)
    assert callable(factory)
    (sensor,) = cli_parser.compile_sensors(0.01, factory)
    assert callable(sensor)
    assert 0 <= sensor()
