import pytest

import platform

import psutil

from cms_perf.setup import cli_parser
from cms_perf.sensors import (  # noqa
    sensor as _mount_sensors,
    net_load as _mount_net_load,
    xrd_load as _mount_xrd_load,
)


@cli_parser.cli_call()
def fake_sensor_factory(interval: int, value=1):
    return value


@cli_parser.cli_call(name="fake.sensor")
def fake_aliased_sensor_factory(interval: int, value=1):
    return value


SENSORS = ["prunq", "loadq", "pcpu", "pmem", "pio"]


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


PRIVILEGED_SENSORS = [
    "nsockets",
    "nsockets(inet6)",
    "nsockets(tcp4)",
    "xrd.piowait",
    "xrd.nfds",
    "xrd.nthreads",
]


@pytest.mark.parametrize(
    "source", [sensor for sensor in PRIVILEGED_SENSORS if "xrd" not in sensor]
)
@pytest.mark.skipif(platform.system() == "Linux", reason="Having privilege on this OS")
def test_privileged_unprivileged(source: str):
    (sensor,) = cli_parser.compile_sensors(0.01, cli_parser.parse_sensor(source))
    with pytest.raises(psutil.AccessDenied):
        sensor()


@pytest.mark.parametrize("source", PRIVILEGED_SENSORS)
@pytest.mark.skipif(platform.system() != "Linux", reason="Require privilege on this OS")
def test_privileged_privileged(source: str):
    (sensor,) = cli_parser.compile_sensors(0.01, cli_parser.parse_sensor(source))
    assert 0 <= sensor()
