from typing import List
import sys

import pytest

from .utility import capture


EXECUTABLES = ["cms_perf"], [sys.executable, "-m", "coverage", "run", "-m", "cms_perf"]


@pytest.mark.parametrize("executable", EXECUTABLES)
def test_run_normal(executable: List[str]):
    output = capture([*executable, "--interval", "0.1"], num_lines=5)
    assert output
    for line in output:
        readings = line.split()
        assert len(readings) == 5
        for reading in readings:
            assert 0 <= int(reading) <= 100
