import argparse

from ..setup import cli_parser
from .. import __version__ as lib_version

# ensure sensors are loaded
from ..sensors import sensor, xrd_load, net_load  # noqa


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
    "--version", action="version", version=lib_version,
)
CLI.add_argument(
    "--interval",
    default=60,
    help="Interval between output; suffixed by s (default), m, or h",
    type=duration,
)
CLI.add_argument(
    "--prunq",
    default="100.0*loadq/ncores",
    type=cli_parser.parse_sensor,
    help="Expression to compute system load percentage",
)
CLI.add_argument(
    "--pcpu",
    default="pcpu",
    type=cli_parser.parse_sensor,
    help="Expression to compute cpu utilization percentage",
)
CLI.add_argument(
    "--pmem",
    default="pmem",
    type=cli_parser.parse_sensor,
    help="Expression to compute memory utilization percentage",
)
CLI.add_argument(
    "--ppag",
    default="0",
    type=cli_parser.parse_sensor,
    help="Expression to compute paging load percentage",
)
CLI.add_argument(
    "--pio",
    default="pio",
    type=cli_parser.parse_sensor,
    help="Expression to compute network utilization percentage",
)
CLI.add_argument(
    "--sched",
    help="cms.sched directive to report total load and maxload on stderr",
    type=str,
)
