"""
P
"""
from typing import List
import time

import psutil


class XrootdTracker:
    def __init__(self, rescan_interval: float):
        self.rescan_interval = rescan_interval
        self._next_scan = 0.0
        self._xrootd_procs: List[psutil.Process] = []

    @property
    def xrootds(self) -> List[psutil.Process]:
        if self._refresh_xrootds():
            self._xrootd_procs = [
                proc for proc in psutil.process_iter() if proc.name() == "xrootd"
            ]
            self._next_scan = time.time() + self.rescan_interval
        return self._xrootd_procs

    def _refresh_xrootds(self):
        return (
            not self._xrootd_procs
            or time.time() > self.rescan_interval
            or not all(proc.is_running() for proc in self._xrootd_procs)
        )

    def io_wait(self) -> float:
        return max(xrd.cpu_times().iowait for xrd in self.xrootds)

    def num_fds(self) -> int:
        return sum(xrd.num_fds() for xrd in self.xrootds)

    def num_threads(self) -> int:
        return sum(xrd.num_threads() for xrd in self.xrootds)