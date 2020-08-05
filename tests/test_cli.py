from typing import List, Tuple
import sys

import pytest

from .utility import capture
from . import mimicry


EXECUTABLES = ["cms_perf"], [sys.executable, "-m", "coverage", "run", "-m", "cms_perf"]


@pytest.mark.parametrize("executable", EXECUTABLES)
def test_run_normal(executable: List[str]):
    output = capture([*executable, "--interval", "0.02"], num_lines=5)
    assert output
    for line in output:
        readings = line.split()
        assert len(readings) == 5
        for reading in readings:
            assert 0 <= int(reading) <= 100


@pytest.mark.parametrize("executable", EXECUTABLES)
def test_run_replaced(executable: List[str]):
    output = capture(
        [
            *executable,
            "--interval",
            "0.02",
            "--runq",
            "0",
            "--pcpu",
            "1",
            "--pmem",
            "2",
            "--pag",
            "3",
            "--pio",
            "4",
        ],
        num_lines=5,
    )
    assert output
    for line in output:
        readings = line.split()
        assert len(readings) == 5
        for idx, reading in enumerate(readings):
            assert idx == int(reading)


SCHED_FIELD = tuple(enumerate(("runq", "cpu", "mem", "pag", "io")))


@pytest.mark.parametrize("executable", EXECUTABLES)
@pytest.mark.parametrize("sched_field", SCHED_FIELD)
def test_run_sched(executable: List[str], sched_field: Tuple[int, str]):
    index, field = sched_field
    output = capture(
        [*executable, "--interval", "0.02", "--sched", f"{field} 100"],
        num_lines=5,
        stderr=True,
    )
    assert output
    for line in output:
        *readings, total = line.split()
        assert len(readings) == 5
        for reading in readings:
            assert 0 <= int(reading) <= 100
        assert total == readings[index]


PAG_PLUGINS = ["xrd.piowait", "xrd.nfds", "xrd.nthreads"]


@mimicry.skipif_unsuported
@pytest.mark.parametrize("executable", EXECUTABLES)
@pytest.mark.parametrize("pag_plugin", PAG_PLUGINS)
def test_run_pag_plugin(executable: List[str], pag_plugin):
    with mimicry.Process(name="xrootd", threads=20, files=20):
        output = capture(
            [*executable, "--interval", "0.1", f"--pag={pag_plugin}"], num_lines=5,
        )
        assert output
        for line in output:
            readings = line.split()
            assert len(readings) == 5
            for reading in readings:
                assert 0 <= int(reading) <= 100
