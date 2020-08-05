import pytest

from cms_perf import cli_parser
from cms_perf import sensor as _mounted_sensors  # noqa


@cli_parser.cli_call()
def fake_sensor_factory(interval: int, value=1):
    return value


@cli_parser.cli_call(name="fake.sensor")
def fake_aliased_sensor_factory(interval: int, value=1):
    return value


SENSORS = ["runq", "loadq", "pcpu", "pmem", "pio"]


SOURCES = [
    "1.0",
    "1337",
    *SENSORS,
    "1.0 / 1337",
    "100.0*loadq/ncores",
    *(f"{sensor} / 20" for sensor in SENSORS),
]


@pytest.mark.parametrize("source", SOURCES)
def test_parse(source: str):
    factory = cli_parser.parse_sensor(source)
    assert callable(factory)
    (sensor,) = cli_parser.compile_sensors(0.01, factory)
    assert callable(sensor)
    assert 0 <= sensor()


KNOWN_SENSORS = [
    (1, "1"),
    (1.0 / 1337 / 12345, "1.0 / 1337 / 12345"),
    (1, "fake_sensor_factory"),
    (1, "fake.sensor"),
]


@pytest.mark.parametrize("expected, source", KNOWN_SENSORS)
def test_known_sensor(expected: float, source: str):
    factory = cli_parser.parse_sensor(source)
    (sensor,) = cli_parser.compile_sensors(0.01, factory)
    assert expected == sensor()


KNOWN_SENSOR_CALLS = [
    (2, "fake_sensor_factory(2)"),
    (6, "fake_sensor_factory(4) / fake_sensor_factory(2) * fake_sensor_factory(3)"),
]


@pytest.mark.parametrize("expected, source", KNOWN_SENSOR_CALLS)
def test_known_sensor_calls(expected: float, source: str):
    factory = cli_parser.parse_sensor(source)
    (sensor,) = cli_parser.compile_sensors(0.01, factory)
    assert expected == sensor()


KNOWN_TRANSFORMS = [
    (12.3, "max(1, 12.3)"),
    (2, "max(min(2, 4), 1)"),
    (2, "max(min(2, 4, 3), 1, 1.5)"),
]


@pytest.mark.parametrize("expected, source", KNOWN_TRANSFORMS)
def test_known_transforms(expected: float, source: str):
    factory = cli_parser.parse_sensor(source)
    (sensor,) = cli_parser.compile_sensors(0.01, factory)
    assert expected == sensor()
