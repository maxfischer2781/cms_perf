"""
Sensors for resources used by XRootD processes
"""

from typing import List
import time

import psutil

from ..setup.cli_parser import cli_call


@cli_call(name="xrd.piowait")
def xrd_piowait(interval: float) -> float:
    """Percentage of time waiting for IO by all XRootD processes"""
    tracker = cached_tracker(interval)
    return 100.0 * tracker.io_wait()


@cli_call(name="xrd.nfds")
def xrd_numfds(interval: float) -> float:
    """Number of file descriptors by all XRootD processes"""
    tracker = cached_tracker(interval)
    return tracker.num_fds()


@cli_call(name="xrd.nthreads")
def xrd_threads(interval: float) -> float:
    """Number of threads by all XRootD processes"""
    tracker = cached_tracker(interval)
    return tracker.num_threads()


def cached_tracker(interval: float):
    # how often the tracker scans for processes
    rescan_interval = max(
        60,
        int(min(interval * 10, 3600)) // 10 * 10,
    )
    try:
        return TRACKER_CACHE[rescan_interval]
    except KeyError:
        tracker = XrootdTracker(rescan_interval=rescan_interval)
        TRACKER_CACHE[rescan_interval] = tracker
        return tracker


TRACKER_CACHE: "dict[float, XrootdTracker]" = {}


def is_alive(proc: psutil.Process) -> bool:
    """Test that `proc` is running but not a zombie"""
    return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE


class XrootdTracker:
    def __init__(self, rescan_interval: float):
        self.rescan_interval = rescan_interval
        self._next_scan = 0.0
        self._xrootd_procs: List[psutil.Process] = []

    @property
    def xrootds(self) -> List[psutil.Process]:
        if self._refresh_xrootds():
            self._xrootd_procs = [
                proc
                for proc in psutil.process_iter()
                if proc.name() == "xrootd" and is_alive(proc)
            ]
            self._next_scan = time.monotonic() + self.rescan_interval
        return self._xrootd_procs

    def _refresh_xrootds(self) -> bool:
        return (
            not self._xrootd_procs
            or time.monotonic() > self._next_scan
            or not all(is_alive(proc) for proc in self._xrootd_procs)
        )

    def io_wait(self) -> float:
        return max(
            (xrd.cpu_times().iowait for xrd in self.xrootds),  # type: ignore
            default=0,
        )

    def num_fds(self) -> int:
        return sum(xrd.num_fds() for xrd in self.xrootds)

    def num_threads(self) -> int:
        return sum(xrd.num_threads() for xrd in self.xrootds)
