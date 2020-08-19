"""
Sensor for network load
"""
import enum

import psutil

from .cli_parser import cli_domain, cli_call


@cli_domain(name="KIND")
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
    """Number of open sockets of a given kind"""
    return len(psutil.net_connections(kind=kind.name))
