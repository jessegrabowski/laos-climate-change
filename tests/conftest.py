import gzip
import socket
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from shapely.geometry import LineString, box

from climate_risk.const_vars import BIG_RIVERS_FILENAME, GPCC_YEARS, MEDIUM_BIG_RIVERS_FILENAME

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


def toy_world():
    """Three square countries: two in Asia, one in Africa, with synthetic ISO codes."""
    return gpd.GeoDataFrame(
        {
            "ISO_A3": ["AAA", "BBB", "CCC"],
            "FORMAL_EN": ["Aland", "Beeland", "Ceeland"],
            "CONTINENT": ["Asia", "Asia", "Africa"],
            "REGION_UN": ["Asia", "Asia", "Africa"],
            "geometry": [box(0, 0, 1, 1), box(2, 0, 3, 1), box(4, 0, 5, 1)],
        },
        crs="EPSG:4326",
    )


def toy_rivers():
    """ORD_FLOW spans the thresholds both loaders filter on: < 5 is big, < 6 adds medium."""
    return gpd.GeoDataFrame(
        {
            "ORD_FLOW": [4, 5, 6],
            "HYRIV_ID": [1, 2, 3],
            "geometry": [
                LineString([(0, 0), (0, 1)]),
                LineString([(2, 0), (2, 1)]),
                LineString([(4, 0), (4, 1)]),
            ],
        },
        crs="EPSG:4326",
    )


# Archive and directory names as they appear upstream, stated independently of the loader so a
# change to either constant fails a test rather than silently agreeing with itself.
# Archive and directory names as they appear upstream, stated independently of the loader so a
# change to either constant fails a test rather than silently agreeing with itself.
UPSTREAM_SHAPEFILE_LAYOUT = {
    "world": ("wb_countries_admin0_10m.zip", "WB_countries_Admin0_10m/WB_countries_Admin0_10m.shp"),
}


def toy_precipitation(year_range):
    """A GPCC grid with one point inside each country of `toy_world`."""
    start = int(year_range.split("_")[0])
    return xr.Dataset(
        {"precip": (("time", "lat", "lon"), np.arange(3.0).reshape(1, 1, 3))},
        coords={
            "time": np.array([f"{start}-01-01"], dtype="datetime64[ns]"),
            "lat": [0.5],
            "lon": [0.5, 2.5, 4.5],
        },
    )


@pytest.fixture
def write_gpcc_archives(tmp_path):
    """Return a callable writing one gzipped archive per year range, some already extracted."""

    def write(extracted=()):
        gpcc_dir = tmp_path / "gpcc"
        gpcc_dir.mkdir(parents=True, exist_ok=True)
        for year_range in GPCC_YEARS:
            raw = bytes(toy_precipitation(year_range).to_netcdf())
            (gpcc_dir / f"gpcc_raw_{year_range}.nc.gz").write_bytes(gzip.compress(raw))
            if year_range in extracted:
                (gpcc_dir / f"gpcc_raw_{year_range}.nc").write_bytes(raw)
        return tmp_path

    return write


@pytest.fixture
def write_shapefile_cache(tmp_path):
    """Return a callable laying out a shapefile the way a completed download would have."""

    def write(which, gdf):
        archive_name, member = UPSTREAM_SHAPEFILE_LAYOUT[which]
        # The layout is stated literally, not derived from the loader, so a wrong cache path fails.
        shapefile = tmp_path / "shapefiles" / member
        shapefile.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_file(shapefile)

        archive = tmp_path / "shapefiles" / archive_name
        with zipfile.ZipFile(archive, "w") as bundle:
            for part in shapefile.parent.iterdir():
                bundle.write(part, str(part.relative_to(tmp_path / "shapefiles")))

        return tmp_path

    return write


@pytest.fixture
def write_rivers_cache(tmp_path):
    """Return a callable writing the processed river shapefiles a warm cache would hold."""

    def write(gdf, include_medium=False):
        rivers_dir = tmp_path / "rivers"
        rivers_dir.mkdir(parents=True, exist_ok=True)
        filename = MEDIUM_BIG_RIVERS_FILENAME if include_medium else BIG_RIVERS_FILENAME
        gdf.to_file(rivers_dir / filename)
        return tmp_path

    return write


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
