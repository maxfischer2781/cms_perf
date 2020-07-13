from .utility import capture


def test_run_normal():
    output = capture(["cms_perf", "--interval", "0.1"], num_lines=5)
    assert output
    for line in output:
        readings = line.split()
        assert len(readings) == 5
        for reading in readings:
            assert 0 <= int(reading) <= 100
