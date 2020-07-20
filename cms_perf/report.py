"""
The main loop collecting and reporting values
"""
import sys
import time

from .cli import CLI
from .sensor import (
    system_load,
    cpu_utilization,
    memory_utilization,
    network_utilization,
)


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
    def from_directive(cls, directive: str):
        """Create an instance by parsing a ``cms.sched`` directive"""
        items = directive.split()
        policy = {
            word: int(value)
            for word, value in zip(items[:-1], items[1:])
            if word in {"cpu", "io", "mem", "pag", "runq", "maxload"}
        }
        return cls(**policy)

    def weight(self, runq: float, cpu: float, mem: float, paq, io: float):
        """
        Rate the total load by weighting each individual load value

        Returns the total load and whether the load exceeds the ``maxload``.
        """
        load = (cpu * self.cpu + io * self.io + mem * self.mem + runq * self.runq) / 100
        return int(load), load > self.maxload


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
    max_core_runq: float, interval: float, pag_sensor, sched: PseudoSched = None
):
    """Write sensor information to stdout every ``interval`` seconds"""
    try:
        for _ in every(interval):
            (*values,) = map(
                clamp_percentages,
                (
                    system_load(interval) / max_core_runq,
                    cpu_utilization(interval),
                    memory_utilization(),
                    pag_sensor(),
                    network_utilization(interval),
                ),
            )
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
    sched = PseudoSched.from_directive(options.sched) if options.sched else None
    pag_sensor = options.__make_pag__(options)
    run_forever(
        max_core_runq=options.max_core_runq,
        interval=options.interval,
        pag_sensor=pag_sensor,
        sched=sched,
    )
