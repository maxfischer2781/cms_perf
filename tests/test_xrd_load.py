import platform

import pytest
import psutil

from cms_perf import xrd_load

from .mimicry import Process


def _any_xrootds():
    return any(True for proc in psutil.process_iter() if proc.name() == "xrootd")


@pytest.mark.skipif(platform.system() != "Linux", reason="Cannot mimic xrootd")
def test_tracker():
    tracker = xrd_load.XrootdTracker(rescan_interval=1)
    with Process("xrootd", threads=20, files=20):
        assert tracker.num_threads() >= 20
        assert tracker.num_fds() >= 20
        assert type(tracker.io_wait()) is float


@pytest.mark.skipif(platform.system() != "Linux", reason="Cannot mimic xrootd")
@pytest.mark.skipif(_any_xrootds(), reason="Ambient xrootd processes present")
def test_tracker_cache_procs():
    tracker = xrd_load.XrootdTracker(rescan_interval=1)
    # automatically rescan if there are no target processes
    assert tracker.xrootds is not tracker.xrootds
    with Process("xrootd", threads=20, files=20):
        found_procs = tracker.xrootds
        assert len(found_procs) == 1
        assert found_procs is tracker.xrootds
    # automatically rescan if existing process died
    assert found_procs is not tracker.xrootds
