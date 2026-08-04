import socket

import pytest

from tests.conftest import NetworkAccessError


def test_remote_connection_raises():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client, pytest.raises(NetworkAccessError):
        client.connect(("example.com", 80))


def test_remote_connection_by_ip_raises():
    """A bare IP bypasses DNS, so the guard cannot rely on hostname resolution to catch it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client, pytest.raises(NetworkAccessError):
        client.connect(("93.184.216.34", 80))


def test_loopback_still_connects():
    """PyTensor probes localhost for its compiledir lock, so blocking it would break sampling."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect(("127.0.0.1", port))


def test_unix_socket_still_connects(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind("probe.sock")
        server.listen(1)

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect("probe.sock")
