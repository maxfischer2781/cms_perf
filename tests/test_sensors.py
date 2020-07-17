from functools import partial

import pytest

from cms_perf import sensor

SENSORS = (
    partial(sensor.system_load, 0.01),
    partial(sensor.cpu_utilization, 0.01),
    sensor.memory_utilization,
    partial(sensor.network_utilization, 0.01),
)


@pytest.mark.parametrize("read_sensor", SENSORS)
def test_sensors(read_sensor):
    result = read_sensor()
    assert type(result) is float
    assert 0.0 <= result
