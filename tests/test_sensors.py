import pytest

from cms_perf import sensor

SENSORS = (
    sensor.system_load,
    sensor.cpu_utilization,
    sensor.memory_utilization,
    sensor.network_utilization,
)


@pytest.mark.parametrize("read_sensor", SENSORS)
def test_sensors(read_sensor):
    result = read_sensor(interval=0.01)
    assert type(result) is float
    assert 0.0 <= result
