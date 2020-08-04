import pytest

from cms_perf import cli_parser
from cms_perf import sensor


@cli_parser.cli_sensor
def fake_sensor_factory(interval: int, value=1):
    return lambda: value


@cli_parser.cli_sensor(name="fake.sensor")
def fake_aliased_sensor_factory(interval: int, value=1):
    return lambda: value


SOURCES = [
    "1.0",
    "1337",
    *(sensor.cli_name for sensor in cli_parser.SENSORS.values()),
    "1.0 / 1337",
    *(f"{sensor.cli_name} / 20" for sensor in cli_parser.SENSORS.values()),
]


@pytest.mark.parametrize("source", SOURCES)
def test_parse(source: str):
    factory = cli_parser.prepare_sensor(source)
    assert callable(factory)
    (sensor,) = cli_parser.compile_sensors(0.01, factory)
    assert callable(sensor)
    assert 0 <= sensor()
