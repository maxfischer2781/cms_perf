import platform

import pytest

from cms_perf import xrd_load

from .mimicry import Process


@pytest.mark.skipif(platform.system() != "Linux", reason="Cannot mimic xrootd")
def test_tracker():
    tracker = xrd_load.XrootdTracker(1)
    with Process("xrootd", threads=20, files=20):
        assert tracker.num_threads() >= 20
        assert tracker.num_fds() >= 20
