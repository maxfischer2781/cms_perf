"""
The main loop collecting and reporting values
"""
from typing import Callable
import sys
import time

from .setup.cli import CLI
from .setup import cli_parser


class PseudoSched:
    """Imitation of the ``cms.sched`` directive to compute total load"""

    def __init__(self, cpu=0, io=0, mem=0, pag=0, runq=0, maxload=100):
        self.cpu = cpu
        self.io = io
        self.mem = mem
        self.pag = pag
        self.runq = runq
        self.maxload = maxload

    @classmethod
    def from_directive(cls, directive: str) -> "PseudoSched":
        """Create an instance by parsing a ``cms.sched`` directive"""
        items = directive.split()
        policy = {
            word: int(value)
            for word, value in zip(items[:-1], items[1:])
            if word in {"cpu", "io", "mem", "pag", "runq", "maxload"}
        }
        return cls(**policy)

    def weight(self, runq: int, cpu: int, mem: int, pag: int, io: int):
        """
        Rate the total load by weighting each individual load value

        Returns the total load and whether the load exceeds the ``maxload``.
        """
        load = (
            cpu * self.cpu
            + io * self.io
            + mem * self.mem
            + pag * self.pag
            + runq * self.runq
        ) // 100
        return load, load > self.maxload


def every(interval: float):
    """
    Iterable that wakes up roughly every ``interval`` seconds

    The iterable pauses so that the time spent between iterations
    plus the pause time equals ``interval`` as closely as possible.
    """
    while True:
        suspended = time.time()
        yield
        duration = time.time() - suspended
        time.sleep(max(0.1, interval - duration))


def clamp_percentages(value: float) -> int:
    """Restrict a percentage ``value`` to an integer between 0 and 100"""
    return 0 if value < 0.0 else 100 if value > 100.0 else int(value)


def run_forever(
    interval: float,
    prunq: Callable[[], float],
    pmem: Callable[[], float],
    pcpu: Callable[[], float],
    ppag: Callable[[], float],
    pio: Callable[[], float],
    sched: PseudoSched = None,
):
    """Write sensor information to stdout every ``interval`` seconds"""
    sensors = (prunq, pcpu, pmem, ppag, pio)
    try:
        for _ in every(interval):
            values = [clamp_percentages(sensor()) for sensor in sensors]
            print(*values, end="", flush=True)
            if sched is not None:
                load, rejected = sched.weight(*values)
                print(
                    f" {load}{'!' if rejected else ''}",
                    end="",
                    file=sys.stderr,
                    flush=True,
                )
            print(flush=True)
    except KeyboardInterrupt:
        pass


def main():
    """Run the sensor based on CLI arguments"""
    options = CLI.parse_args()
    prunq, pcpu, pmem, ppag, pio = cli_parser.compile_sensors(
        options.interval,
        options.prunq,
        options.pcpu,
        options.pmem,
        options.ppag,
        options.pio,
    )
    sched = PseudoSched.from_directive(options.sched) if options.sched else None
    run_forever(
        interval=options.interval,
        prunq=prunq,
        pcpu=pcpu,
        pmem=pmem,
        ppag=ppag,
        pio=pio,
        sched=sched,
    )
