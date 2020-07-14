"""
Sensors for the canonical cms.perf measurements

.. note::

    The paging load has no canonical meaning anymore.
    It exists for backwards compatibility but is assumed 0.
"""
import time

import psutil


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
