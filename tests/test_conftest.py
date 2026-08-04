import socket

import pytest

from tests.conftest import NetworkAccessError

REMOTE_TCP = ("93.184.216.34", 80)
REMOTE_UDP = ("93.184.216.34", 53)


def _tcp():
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def _udp():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


@pytest.mark.parametrize(
    "attempt",
    [
        lambda: _tcp().connect(REMOTE_TCP),
        lambda: _tcp().connect_ex(REMOTE_TCP),
        lambda: _udp().sendto(b"probe", REMOTE_UDP),
        lambda: _udp().sendmsg([b"probe"], (), 0, REMOTE_UDP),
        lambda: socket.getaddrinfo("example.com", 80),
    ],
    ids=["connect", "connect_ex", "sendto", "sendmsg", "getaddrinfo"],
)
def test_every_outbound_path_is_refused(attempt):
    """connect_ex and sendto silently bypassed an earlier guard that patched only connect."""
    with pytest.raises(NetworkAccessError):
        attempt()
