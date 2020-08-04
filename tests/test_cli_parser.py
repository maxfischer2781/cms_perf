import pytest

from cms_perf import cli_parser
from cms_perf import sensor


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
