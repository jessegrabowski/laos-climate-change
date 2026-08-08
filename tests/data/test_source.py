import re

import pytest
import requests

from climate_risk.data.co2 import CO2
from climate_risk.data.fetch import USER_AGENT
from climate_risk.data.gpcc import FULL_DATA, MONITORING
from climate_risk.data.hadcrut import HADCRUT
from climate_risk.data.ocean_heat import OCEAN_HEAT
from climate_risk.data.source import DataSource

FIELDS = {
    "url": "https://example.org/co2.csv",
    "filename": "noaa_co2.csv",
    "licence": "public domain",
    "citation": "NOAA GML",
    "retrieved": "2026-08-03",
}


def source(**overrides) -> DataSource:
    return DataSource(**(FIELDS | overrides))


def test_a_source_is_stored_under_its_filename(tmp_path):
    assert source().path(tmp_path) == tmp_path / "noaa_co2.csv"


@pytest.mark.parametrize("filename", ["../escape.csv", "nested/file.csv", "/absolute.csv", ""], ids=repr)
def test_a_filename_carrying_a_path_is_rejected(filename):
    """`path()` joins onto the cache directory, so a directory component writes outside it."""
    with pytest.raises(ValueError, match="bare name"):
        source(filename=filename)


@pytest.mark.parametrize("url", ["ftp://example.org/f.csv", "example.org/f.csv", "file:///etc/passwd"], ids=repr)
def test_a_non_http_url_is_rejected(url):
    with pytest.raises(ValueError, match="http"):
        source(url=url)


def test_an_unparseable_retrieved_date_is_rejected():
    """Sources are import-time literals, so the error must name the one that failed."""
    with pytest.raises(ValueError, match=re.escape("noaa_co2.csv: retrieved must be an ISO date")):
        source(retrieved="03-08-2026")


# Every source the library downloads. A new one is added here so the reachability check covers it.
# The monitoring archives all share one URL pattern, so its ends are checked rather than every month.
SOURCES = (
    {"CO2": CO2, "OCEAN_HEAT": OCEAN_HEAT, "HADCRUT": HADCRUT}
    | {archive.filename: archive for archive in FULL_DATA.sources}
    | {archive.filename: archive for archive in (MONITORING.sources[0], MONITORING.sources[-1])}
)


@pytest.mark.network
@pytest.mark.parametrize("declared", SOURCES.values(), ids=SOURCES.keys())
def test_every_declared_source_is_still_published(declared):
    """Upstream reorganises without notice, and a dead URL surfaces as a failed run months later."""
    # Hosts vary their answer by agent, so the check has to send the one fetch will send.
    headers = {"User-Agent": USER_AGENT}
    response = requests.head(declared.url, timeout=30, allow_redirects=True, headers=headers)
    if response.status_code >= 400:
        # Some hosts refuse HEAD; ask for one byte instead of downloading the archive.
        response = requests.get(declared.url, timeout=30, headers=headers | {"Range": "bytes=0-0"}, stream=True)
        response.close()

    assert response.status_code < 400
