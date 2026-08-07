import pytest
import requests

from climate_risk.data.fetch import USER_AGENT, fetch
from climate_risk.data.source import DataSource

PAYLOAD = b"Year,co2\n1990,354.4\n"


def make_source(**overrides) -> DataSource:
    fields = {
        "url": "https://example.org/co2.csv",
        "filename": "noaa_co2.csv",
        "licence": "public domain",
        "citation": "NOAA GML",
        "retrieved": "2026-08-03",
    }
    return DataSource(**(fields | overrides))


class FakeResponse:
    def __init__(self, payload: bytes, status_error: Exception | None = None):
        self.payload = payload
        self.status_error = status_error
        self.headers = {"Content-Length": str(len(payload))}

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def raise_for_status(self):
        if self.status_error is not None:
            raise self.status_error

    def iter_content(self, chunk_size):
        for start in range(0, len(self.payload), chunk_size):
            yield self.payload[start : start + chunk_size]


@pytest.fixture
def downloads(monkeypatch):
    """Record every request the code makes, and serve PAYLOAD without touching a socket."""
    calls = []

    def fake_get(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return FakeResponse(PAYLOAD)

    monkeypatch.setattr(requests, "get", fake_get)

    return calls


def test_the_file_lands_in_the_cache(tmp_path, downloads):
    path = fetch(make_source(), tmp_path)

    assert path == tmp_path / "noaa_co2.csv"
    assert path.read_bytes() == PAYLOAD


def test_a_present_file_is_not_downloaded_again(tmp_path, downloads):
    """Assert on what the caller gets, so this survives any change to how downloading works."""
    source = make_source()
    source.path(tmp_path).write_bytes(b"already here")

    assert fetch(source, tmp_path).read_bytes() == b"already here"


def test_force_downloads_over_a_present_file(tmp_path, downloads):
    fetch(make_source(), tmp_path)
    fetch(make_source(), tmp_path, force=True)

    assert len(downloads) == 2


def test_a_browser_agent_is_sent(tmp_path, downloads):
    """Hosts reject urllib's default agent; the World Bank archive answers 403 without one."""
    fetch(make_source(), tmp_path)

    assert downloads[0]["headers"]["User-Agent"] == USER_AGENT


def test_an_interrupted_download_is_not_mistaken_for_a_cache_hit(tmp_path, downloads):
    """A partial multi-GB archive left in the cache would otherwise be read as the real file."""
    leftover = tmp_path / "noaa_co2.csv.part"
    leftover.parent.mkdir(parents=True, exist_ok=True)
    leftover.write_bytes(b"half a giga")

    path = fetch(make_source(), tmp_path)

    assert path.read_bytes() == PAYLOAD
    assert not leftover.exists()


def test_an_http_error_propagates(tmp_path, monkeypatch):
    monkeypatch.setattr(
        requests, "get", lambda url, **kwargs: FakeResponse(b"", status_error=requests.HTTPError("404"))
    )

    with pytest.raises(requests.HTTPError):
        fetch(make_source(), tmp_path)

    assert not (tmp_path / "noaa_co2.csv").exists()


def test_a_cache_directory_that_does_not_exist_yet_is_created(tmp_path, downloads):
    """Loaders point at subdirectories of the cache, which nothing has made on a fresh clone."""
    nested = tmp_path / "gpcc" / "raw"

    assert fetch(make_source(), nested).read_bytes() == PAYLOAD
