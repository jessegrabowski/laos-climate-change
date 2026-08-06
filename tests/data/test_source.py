import re

import pytest

from climate_risk.data.source import DataSource

FIELDS = {
    "url": "https://example.org/co2.csv",
    "filename": "noaa_co2.csv",
    "licence": "public domain",
    "citation": "NOAA GML",
    "retrieved": "2026-08-03",
    "sha256": None,
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


@pytest.mark.parametrize("digest", ["abc123", "A" * 64, "g" * 64, "a" * 63], ids=["short", "upper", "non-hex", "63"])
def test_a_malformed_digest_is_rejected(digest):
    """A typo here surfaces only after the download it was meant to verify."""
    with pytest.raises(ValueError, match="64 lower-case hex"):
        source(sha256=digest)


def test_a_well_formed_digest_is_accepted():
    assert source(sha256="a" * 64).sha256 == "a" * 64


def test_an_unparseable_retrieved_date_is_rejected():
    """Sources are import-time literals, so the error must name the one that failed."""
    with pytest.raises(ValueError, match=re.escape("noaa_co2.csv: retrieved must be an ISO date")):
        source(retrieved="03-08-2026")


def test_omitting_the_digest_is_a_decision_not_an_oversight():
    """Every other field is required; the one that disables a check must be written out too."""
    with pytest.raises(TypeError, match="sha256"):
        DataSource(
            url="https://example.org/f.csv",
            filename="f.csv",
            licence="public domain",
            citation="Someone",
            retrieved="2026-08-03",
        )


def test_a_source_cannot_be_mutated():
    """Sources are module-level literals; a caller reassigning one would affect every later caller."""
    with pytest.raises(AttributeError):
        source().url = "https://elsewhere.example/f.csv"
