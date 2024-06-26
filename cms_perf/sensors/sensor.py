"""
Sensors for the canonical cms.perf and related measurements

.. note::

    The paging load has no canonical meaning anymore.
    It exists for backwards compatibility but is assumed 0.
"""

import time
import enum
import warnings

import psutil

from ..setup.cli_parser import cli_call, cli_domain


# individual sensors for system state
@cli_call(name="prunq")
def system_prunq(interval: float) -> float:
    """Percentage of system load per core, equivalent to ``100*nloadq/ncores``"""
    loadavg_index = 0 if interval <= 60 else 1 if interval <= 300 else 2
    return 100.0 * psutil.getloadavg()[loadavg_index] / psutil.cpu_count()


@cli_call(name="pcpu")
def cpu_utilization(interval: float) -> float:
    """Percentage of cpu utilisation"""
    sample_interval = min(interval / 4, 1)
    return psutil.cpu_percent(interval=sample_interval)


@cli_call(name="pmem")
def memory_utilization(interval: float) -> float:
    """Percentage of memory utilisation"""
    return psutil.virtual_memory().percent


def _get_sent_bytes():
    return {
        nic: stats.bytes_sent
        for nic, stats in psutil.net_io_counters(pernic=True).items()
    }


@cli_call(name="pio")
def network_utilization(interval: float) -> float:
    """Percentage of network I/O utilisation"""
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


# Individual sensor components
@cli_call(name="loadq")
def system_legacy_loadq(interval: float) -> float:
    """Deprecated alias of ``nloadq``"""
    warnings.warn(
        FutureWarning("the 'loadq' sensor is deprecated; use 'nloadq' instead"),
        stacklevel=1,
    )
    return system_loadq(interval)


@cli_call(name="nloadq")
def system_loadq(interval: float) -> float:
    """Absolute system load, the number of active processes"""
    loadavg_index = 0 if interval <= 60 else 1 if interval <= 300 else 2
    return psutil.getloadavg()[loadavg_index]


@cli_domain(name="CPU")
class CpuKind(enum.Enum):
    all = enum.auto()
    physical = enum.auto()


@cli_call(name="ncores")
def system_ncpu(kind: CpuKind = CpuKind.all) -> float:
    """
    Number of CPU cores, by default including logical cores as well

    ``kind`` selects which cores to count, and may be one of ``all`` or ``physical``.
    It defaults to ``all``.
    """
    return float(psutil.cpu_count(logical=kind is CpuKind.all))


@cli_call(name="pswap")
def system_pswap(interval: float) -> float:
    """Percentage of swap utilisation"""
    return psutil.swap_memory().percent


@cli_domain(name="NET")
class ConnectionKind(enum.Enum):
    inet = enum.auto()
    inet4 = enum.auto()
    inet6 = enum.auto()
    tcp = enum.auto()
    tcp4 = enum.auto()
    tcp6 = enum.auto()
    udp = enum.auto()
    udp4 = enum.auto()
    udp6 = enum.auto()
    unix = enum.auto()
    all = enum.auto()


@cli_call(name="nsockets")
def num_sockets(kind: ConnectionKind = ConnectionKind.tcp) -> float:
    """
    Number of open sockets across all processes

    ``kind`` selects which sockets to count, and may be one of
    ``inet``, ``inet4``, ``inet6``,
    ``tcp``, ``tcp4``, ``tcp6``,
    ``udp``, ``udp4``, ``udp6``,
    ``unix`` or ``all``.
    It defaults to ``tcp``.
    """
    return len(psutil.net_connections(kind=kind.name))
