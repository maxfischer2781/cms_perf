import pytest
import psutil

from cms_perf.sensors import xrd_load

from . import mimicry


def _any_xrootds():
    return any(True for proc in psutil.process_iter() if proc.name() == "xrootd")


@mimicry.skipif_unsuported
def test_tracker():
    tracker = xrd_load.XrootdTracker(rescan_interval=1)
    with mimicry.Process("xrootd", threads=20, files=20):
        assert tracker.num_threads() >= 20
        assert tracker.num_fds() >= 20
        assert type(tracker.io_wait()) is float


@mimicry.skipif_unsuported
@pytest.mark.skipif(_any_xrootds(), reason="Ambient xrootd processes present")
def test_tracker_cache_procs():
    tracker = xrd_load.XrootdTracker(rescan_interval=1)
    assert not tracker.xrootds
    # automatically rescan if there are no target processes
    assert tracker.xrootds is not tracker.xrootds
    with mimicry.Process("xrootd", threads=20, files=20):
        found_procs = tracker.xrootds
        assert len(found_procs) == 1
        assert found_procs is tracker.xrootds
    # automatically rescan if existing process died
    assert found_procs is not tracker.xrootds
