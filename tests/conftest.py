import socket

import pytest

_ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}

_real_connect = socket.socket.connect


class NetworkAccessError(RuntimeError):
    """Raised when a test that is not marked `network` opens a remote connection."""


def _guarded_connect(self, address):
    """Allow loopback and AF_UNIX, refuse everything else."""
    if self.family == socket.AF_UNIX:
        return _real_connect(self, address)

    host = address[0] if isinstance(address, tuple) else address
    if host in _ALLOWED_HOSTS:
        return _real_connect(self, address)

    # socket.create_connection only closes on OSError, so an unclosed socket would surface as a
    # ResourceWarning and, under filterwarnings=error, mask this exception.
    self.close()

    raise NetworkAccessError(
        f"network access to {host} in a test not marked `network`. Seed the cache_dir fixture instead, "
        f"or mark the test `network` and run with --run-network."
    )


@pytest.fixture(autouse=True)
def block_network(request, monkeypatch):
    if "network" in request.keywords:
        return
    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)


def pytest_addoption(parser):
    parser.addoption(
        "--run-network",
        action="store_true",
        default=False,
        help="Run tests marked `network`, which download from real upstream sources.",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-network"):
        return

    skip_network = pytest.mark.skip(reason="needs --run-network")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip_network)
