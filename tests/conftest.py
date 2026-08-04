import socket

import pandas as pd
import pytest

# One event that clears every downstream filter: deaths above 100, affected above 1000, and a start
# year inside both the 1970 and 1980 cutoffs. Tests override only the field under examination.
EMDAT_EVENT_DEFAULTS = {
    "DisNo.": "1990-0001-AAA",
    "Country": "Testland",
    "ISO": "AAA",
    "Region": "Asia",
    "Subregion": "South-eastern Asia",
    "Disaster Type": "Flood",
    "Start Year": 1990,
    "End Year": 1990,
    "Total Deaths": 500,
    "No. Injured": 10,
    "No. Affected": 5_000,
    "No. Homeless": 10,
    "Total Affected": 5_000,
    "Total Damage ('000 US$)": 100,
    "Total Damage, Adjusted ('000 US$)": 120,
    "Reconstruction Costs ('000 US$)": 1,
    "Reconstruction Costs, Adjusted ('000 US$)": 1,
    "Insured Damage ('000 US$)": 1,
    "Insured Damage, Adjusted ('000 US$)": 1,
    "Latitude": 18.0,
    "Longitude": 102.0,
    "River Basin": "Mekong",
    "Location": "Somewhere",
}


def emdat_event(overrides=None):
    return EMDAT_EVENT_DEFAULTS | (overrides or {})


class NetworkAccessError(RuntimeError):
    """Raised when a test that is not marked `network` opens a connection."""


@pytest.fixture
def write_emdat_cache(tmp_path):
    """Return a callable writing the given events to a synthetic EM-DAT workbook in the cache."""

    def write(events):
        with pd.ExcelWriter(tmp_path / "emdat.xlsx") as writer:
            pd.DataFrame(list(events)).to_excel(writer, sheet_name="EM-DAT Data", index=False)
        return tmp_path

    return write


OUTBOUND_SOCKET_METHODS = ("connect", "connect_ex", "sendto", "sendmsg")


def _describe_target(args):
    for arg in args:
        if isinstance(arg, tuple) and arg and isinstance(arg[0], str):
            return arg[0]
        if isinstance(arg, str):
            return arg
    return "an external host"


def _refuse_outbound(self, *args, **kwargs):
    target = _describe_target(args)

    # socket.create_connection only closes on OSError, so an unclosed socket would surface as a
    # ResourceWarning and, under filterwarnings=error, mask this exception.
    self.close()

    raise NetworkAccessError(
        f"network access to {target} in a test not marked `network`. Write the file the loader expects "
        f"into its cache directory, or mark the test `network` and run with --run-network."
    )


def _refuse_lookup(*args, **kwargs):
    raise NetworkAccessError(
        f"DNS lookup of {_describe_target(args)} in a test not marked `network`. Write the file the "
        f"loader expects into its cache directory, or mark the test `network` and run with --run-network."
    )


@pytest.fixture(autouse=True)
def block_network(request, monkeypatch):
    if "network" in request.keywords:
        return

    for method in OUTBOUND_SOCKET_METHODS:
        monkeypatch.setattr(socket.socket, method, _refuse_outbound)

    # Refusing name resolution turns an offline run's DNS timeout into an immediate error.
    monkeypatch.setattr(socket, "getaddrinfo", _refuse_lookup)


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
