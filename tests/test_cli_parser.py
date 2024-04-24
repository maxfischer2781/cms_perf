import pytest

import platform

import psutil

from cms_perf.setup import cli_parser
from cms_perf.sensors import (  # noqa
    sensor as _mount_sensors,
    transform as _mount_transform,
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
    "100.0*nloadq/ncores",
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


class Almost:
    def __init__(self, value: float, err: float) -> None:
        self.value = value
        self.err = err

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, (float, int)):
            return NotImplemented
        return abs(value - self.value) <= self.err

    def __repr__(self) -> str:
        return f"{self.value} ± {self.err}"


KNOWN_TRANSFORMS = [
    # min/max transforms
    (12.3, "max(1, 12.3)"),
    (2, "max(min(2, 4), 1)"),
    (2, "max(min(2, 4, 3), 1, 1.5)"),
    # activation functions
    (100, "prelu(100, 5)"),
    (50, "prelu(75, 50)"),
    (75, "prelu(80, 20)"),
    (0, "prelu(5, 5)"),
    (0, "prelu(0, 50)"),
    (0, "psigmoid(0)"),
    (100, "psigmoid(100)"),
    (50, "psigmoid(50)"),
    (Almost(100, 0.05), "psigmoid(99)"),
    (Almost(90, 2.5), "psigmoid(75)"),
    (Almost(70, 2.5), "psigmoid(60)"),
    (Almost(30, 2.5), "psigmoid(40)"),
    (Almost(10, 2.5), "psigmoid(25)"),
    (Almost(0, 0.05), "psigmoid(1)"),
    # pure math precedence
    (1, "2*2-3"),
    (-1, "3-2*2"),
    (8, "3+2*2*2-3"),
]


@pytest.mark.parametrize("expected, source", KNOWN_TRANSFORMS)
def test_known_transforms(expected: "float | Almost", source: str):
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
