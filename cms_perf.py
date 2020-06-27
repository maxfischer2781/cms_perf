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

import psutil

__version__ = '0.1.1'


INTERVAL_UNITS = {"": 1, "s": 1, "m": 60, "h": 60 * 60}


def duration(literal: str) -> float:
    literal = literal.strip()
    value, unit = (literal, "") if literal.isdigit() else (literal[:-1], literal[-1])
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


def system_load(max_core_runq: float, interval: float) -> int:
    loadavg_index = 0 if interval <= 60 else 1 if interval <= 300 else 2
    return int(psutil.getloadavg()[loadavg_index] / psutil.cpu_count() / max_core_runq)


def cpu_utilization(interval: float) -> int:
    sample_interval = min(interval / 4, 1)
    return int(psutil.cpu_percent(interval=sample_interval))


def memory_utilization() -> int:
    return int(psutil.virtual_memory().percent)


def _get_sent_bytes():
    return {
        nic: stats.bytes_sent
        for nic, stats in psutil.net_io_counters(pernic=True).items()
    }


def network_utilization(interval: float) -> int:
    interface_speed = {
        # speed: the NIC speed expressed in mega *bits*
        nic: stats.speed * 125000
        for nic, stats in psutil.net_if_stats().items()
        if stats.isup and stats.speed > 0
    }
    sample_interval = min(interval / 4, 1)
    sent_old = _get_sent_bytes()
    time.sleep(sample_interval)
    sent_new = _get_sent_bytes()
    interface_utilization = {
        nic: (sent_new[nic] - sent_old[nic]) / interface_speed[nic]
        for nic in interface_speed.keys() & sent_old.keys() & sent_new.keys()
    }
    return int(max(interface_utilization.values()) * 100)


def every(interval: float):
    while True:
        suspended = time.time()
        yield
        duration = time.time() - suspended
        time.sleep(max(0.1, interval - duration))


def cap_percentages(value):
    return 0 if value < 0 else 100 if value > 100 else value


def run_forever(max_core_runq: float, interval: float):
    try:
        for _ in every(interval):
            values = map(
                cap_percentages,
                (
                    system_load(max_core_runq, interval),
                    cpu_utilization(interval),
                    memory_utilization(),
                    0,
                    network_utilization(interval),
                ),
            )
            print(*values)
    except KeyboardInterrupt:
        pass


def main():
    options = CLI.parse_args()
    run_forever(max_core_runq=options.max_core_runq, interval=options.interval)


if __name__ == "__main__":
    main()
