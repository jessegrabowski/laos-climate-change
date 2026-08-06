import hashlib

import pytest
import requests

from climate_risk.data.fetch import USER_AGENT, ChecksumMismatchError, fetch, sha256_of
from climate_risk.data.source import DataSource

PAYLOAD = b"Year,co2\n1990,354.4\n"
PAYLOAD_SHA256 = hashlib.sha256(PAYLOAD).hexdigest()


def make_source(**overrides) -> DataSource:
    fields = {
        "url": "https://example.org/co2.csv",
        "filename": "noaa_co2.csv",
        "licence": "public domain",
        "citation": "NOAA GML",
        "retrieved": "2026-08-03",
        "sha256": None,
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
    fetch(make_source(), tmp_path)
    fetch(make_source(), tmp_path)

    assert len(downloads) == 1


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


def test_a_matching_digest_is_accepted(tmp_path, downloads):
    path = fetch(make_source(sha256=PAYLOAD_SHA256), tmp_path)

    assert path.read_bytes() == PAYLOAD


def test_a_mismatched_digest_raises_and_leaves_nothing_in_place(tmp_path, downloads):
    """Drift must not be silently cached, or every later run trusts the wrong bytes."""
    source = make_source(sha256="0" * 64)

    with pytest.raises(ChecksumMismatchError, match="expected sha256"):
        fetch(source, tmp_path)

    assert not source.path(tmp_path).exists()


def test_an_http_error_propagates(tmp_path, monkeypatch):
    monkeypatch.setattr(
        requests, "get", lambda url, **kwargs: FakeResponse(b"", status_error=requests.HTTPError("404"))
    )

    with pytest.raises(requests.HTTPError):
        fetch(make_source(), tmp_path)

    assert not (tmp_path / "noaa_co2.csv").exists()


def test_the_digest_is_of_the_file_contents(tmp_path):
    path = tmp_path / "payload"
    path.write_bytes(PAYLOAD)

    assert sha256_of(path) == PAYLOAD_SHA256
