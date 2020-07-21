from typing import List
import sys

import pytest

from .utility import capture
from . import mimicry


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


@pytest.mark.parametrize("executable", EXECUTABLES)
def test_run_sched(executable: List[str]):
    output = capture(
        [*executable, "--interval", "0.1", "--sched", "runq 100"],
        num_lines=5,
        stderr=True,
    )
    assert output
    for line in output:
        *readings, total = line.split()
        assert len(readings) == 5
        for reading in readings:
            assert 0 <= int(reading) <= 100
        assert total == readings[0]


PAG_PLUGINS = ["num_sockets", "xrootd.io_wait", "xrootd.num_fds", "xrootd.num_threads"]


@mimicry.skipif_unsuported
@pytest.mark.parametrize("executable", EXECUTABLES)
@pytest.mark.parametrize("pag_plugin", PAG_PLUGINS)
def test_run_pag_plugin(executable: List[str], pag_plugin):
    with mimicry.Process(name="xrootd", threads=20, files=20):
        output = capture(
            [*executable, "--interval", "0.1", f"pag={pag_plugin}"], num_lines=5,
        )
        assert output
        for line in output:
            readings = line.split()
            assert len(readings) == 5
            for reading in readings:
                assert 0 <= int(reading) <= 100
