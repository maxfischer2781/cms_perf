"""
Helpers to mimic processes
"""
from typing import Optional
import os
import subprocess
import sys
import threading
import time
import tempfile
import contextlib
import signal
import platform

import setproctitle
import pytest


skipif_unsuported = pytest.mark.skipif(
    platform.system() != "Linux", reason="Cannot mimic on this OS"
)


class Process:
    """
    Mimic a process with a given name, number of threads/files and maximum lifetime

    This class must be used as a context manager. The process is created on entering
    the context and gracefully closed on exiting it.
    """

    def __init__(
        self, name: str, threads: int = 1, files: int = 0, lifetime: float = 1.0
    ):
        assert platform.system() == "Linux", "Not compatible with this OS"
        assert name and threads > 1 and files >= 0 and lifetime > 0
        self.name = name
        self.threads = threads
        self.files = files
        self.lifetime = lifetime
        self._process: Optional[subprocess.Popen] = None

    def __enter__(self):
        with tempfile.TemporaryDirectory() as rendezvous_dir:
            rendezvous = os.path.join(rendezvous_dir, "__it_lives__")
            os.mkfifo(rendezvous)
            self._process = subprocess.Popen(
                [
                    sys.executable,
                    __file__,
                    str(self.name),
                    str(self.threads),
                    str(self.files),
                    str(self.lifetime),
                    rendezvous,
                ]
            )
            with open(rendezvous, "r") as ready:
                ready.read()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._process.send_signal(signal.SIGINT)
        self._process.wait()


def add_thread():
    thread = threading.Thread(target=time.sleep, args=(10,), daemon=True)
    thread.start()
    return thread


def mimimain():
    name, threads, files, lifetime, rendezvous = sys.argv[-5:]
    setproctitle.setproctitle(name)
    threads = [add_thread() for _ in range(int(threads))]
    with contextlib.ExitStack() as es:
        for _ in range(int(files)):
            es.enter_context(tempfile.TemporaryFile())
        with open(rendezvous, "w") as ready:
            ready.write("ready")
        try:
            for _ in range(int((float(lifetime)) * 100)):
                time.sleep(0.01)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    mimimain()
