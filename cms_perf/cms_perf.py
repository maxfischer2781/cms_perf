#!/usr/bin/env python3
"""Sensor for the XRootD cms.perf directive"""
#   See the https://xrootd.slac.stanford.edu/doc/dev410/cms_config.htm#_Toc8247264
# The specified program must write 5 white-space separated numbers to standard out.
# The last number must be terminated by a new-line character ("\n"). Each number must
# be normalized to 100, with 0 indicating no load and 100 indicating saturation. The
# numbers are in the order:
# 1.      system load
# 2.      cpu utilization
# 3.      memory utilization
# 4.      paging load, and
# 5.      network utilization.
import argparse
import time
import sys

import psutil

__version__ = "0.2.1"


INTERVAL_UNITS = {"": 1, "s": 1, "m": 60, "h": 60 * 60}


def duration(literal: str) -> float:
    """
    Parse an XRootD duration literal as a float representing seconds

    A literal consists of a float literal, e.g. ``12`` or ``17.5``,
    and an optional unit ``s`` (for seconds), ``m`` (for minutes),
    or ``h`` (for hours). If no unit is given, ``s`` is assumed.
    """
    literal = literal.strip()
    value, unit = (
        (literal, "") if literal[-1].isdigit() else (literal[:-1], literal[-1])
    )
    try:
        scale = INTERVAL_UNITS[unit]
    except KeyError:
        expected = ", ".join(map(repr, INTERVAL_UNITS))
        raise argparse.ArgumentTypeError(
            f"{unit!r} is not a valid time unit – expected one of {expected}"
        )
    return float(value) * scale


CLI = argparse.ArgumentParser(
    description="Performance Sensor for XRootD cms.perf directive",
    epilog=(
        "In regular intervals, outputs a single line with percentages of: "
        "system load, "
        "cpu utilization, "
        "memory utilizaion, "
        "paging load, and "
        "network utilization. "
        "The paging load exists for historical reasons; "
        "it cannot be reliably computed."
    ),
)
CLI.add_argument(
    "--max-core-runq",
    default=1,
    help="Maximum runq/loadavg per core considered 100%%",
    type=float,
)
CLI.add_argument(
    "--interval",
    default=60,
    help="Interval between output; suffixed by s (default), m, or h",
    type=duration,
)
CLI.add_argument(
    "--sched",
    help="cms.sched directive to report total load and maxload on stderr",
    type=str,
)


# individual sensors for system state
def system_load(interval: float) -> float:
    """Get the current system load sample most closely matching ``interval``"""
    loadavg_index = 0 if interval <= 60 else 1 if interval <= 300 else 2
    return 100.0 * psutil.getloadavg()[loadavg_index] / psutil.cpu_count()


def cpu_utilization(interval: float) -> float:
    """Get the current cpu utilisation relative to ``interval``"""
    sample_interval = min(interval / 4, 1)
    return psutil.cpu_percent(interval=sample_interval)


def memory_utilization() -> float:
    """Get the current memory utilisation"""
    return psutil.virtual_memory().percent


def _get_sent_bytes():
    return {
        nic: stats.bytes_sent
        for nic, stats in psutil.net_io_counters(pernic=True).items()
    }


def network_utilization(interval: float) -> float:
    """Get the current network utilisation relative to ``interval``"""
    sample_interval = min(interval / 4, 1)
    interface_speed = {
        # speed: the NIC speed expressed in mega *bits* per second
        nic: stats.speed * 125000 * sample_interval
        for nic, stats in psutil.net_if_stats().items()
        if stats.isup and stats.speed > 0
    }
    sent_old = _get_sent_bytes()
    time.sleep(sample_interval)
    sent_new = _get_sent_bytes()
    interface_utilization = {
        nic: (sent_new[nic] - sent_old[nic]) / interface_speed[nic]
        for nic in interface_speed.keys() & sent_old.keys() & sent_new.keys()
    }
    return 100.0 * max(interface_utilization.values())


# sensor data reporting
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


def run_forever(max_core_runq: float, interval: float, sched: PseudoSched = None):
    """Write sensor information to stdout every ``interval`` seconds"""
    try:
        for _ in every(interval):
            (*values,) = map(
                clamp_percentages,
                (
                    system_load(interval) / max_core_runq,
                    cpu_utilization(interval),
                    memory_utilization(),
                    0,
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
    run_forever(
        max_core_runq=options.max_core_runq, interval=options.interval, sched=sched
    )


if __name__ == "__main__":
    main()
