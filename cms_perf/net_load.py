"""
Sensor for network load
"""
import enum

import psutil


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


def prepare_num_sockets(kind: ConnectionKind, max_sockets):
    return lambda: 100.0 * num_sockets(kind) / max_sockets


def num_sockets(kind: ConnectionKind) -> float:
    return len(psutil.net_connections(kind=kind.name))
