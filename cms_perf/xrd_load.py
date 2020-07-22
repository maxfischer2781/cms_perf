"""
P
"""
from typing import List
import time

import psutil


def rescan(interval):
    return min(interval * 10, 3600)


def prepare_iowait(interval: float):
    tracker = XrootdTracker(rescan_interval=rescan(interval))
    return lambda: 100.0 * tracker.io_wait()


def prepare_numfds(interval: float, max_core_fds: float):
    tracker = XrootdTracker(rescan_interval=rescan(interval))
    return lambda: 100.0 * tracker.num_fds() / max_core_fds / psutil.cpu_count()


def prepare_threads(interval: float, max_core_threads: float):
    tracker = XrootdTracker(rescan_interval=rescan(interval))
    return lambda: 100.0 * tracker.num_threads() / max_core_threads / psutil.cpu_count()


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
            self._next_scan = time.time() + self.rescan_interval
        return self._xrootd_procs

    def _refresh_xrootds(self):
        return (
            not self._xrootd_procs
            or time.time() > self._next_scan
            or not all(is_alive(proc) for proc in self._xrootd_procs)
        )

    def io_wait(self) -> float:
        return max(xrd.cpu_times().iowait for xrd in self.xrootds)

    def num_fds(self) -> int:
        return sum(xrd.num_fds() for xrd in self.xrootds)

    def num_threads(self) -> int:
        return sum(xrd.num_threads() for xrd in self.xrootds)
