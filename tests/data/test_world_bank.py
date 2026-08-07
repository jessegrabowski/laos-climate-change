import logging

import polars as pl
import pytest

from polars.testing import assert_frame_equal

from climate_risk.data import world_bank
from climate_risk.data.world_bank import (
    COUNTRIES_FILE,
    COUNTRY_CODE_BY_NAME,
    REQUESTED_COUNTRY_CODES,
    WB_INDICATORS,
    load_wb_data,
    transform_world_bank,
)

# The cache key is stated literally, so a wrong one fails rather than agreeing with itself.
CACHE_FILE = "world_bank.parquet"


def downloaded(rows) -> pl.DataFrame:
    """Indicators shaped as kuznets returns them tidy: flat columns under the raw indicator codes."""
    return pl.DataFrame(rows, schema=["country", "year", *WB_INDICATORS], orient="row")


@pytest.fixture
def serves(monkeypatch):
    """Answer wb.download from a frame instead of the network, recording the arguments used."""

    def serve(frame):
        calls = []

        def fake_download(**kwargs):
            calls.append(kwargs)
            return frame

        monkeypatch.setattr(world_bank.wb, "download", fake_download)
        return calls

    return serve


def test_indicators_are_keyed_by_iso_code_and_year():
    raw = downloaded([("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0)])

    frame = transform_world_bank(raw)

    assert frame.columns[:2] == ["country_code", "year"]
    assert frame.select("country_code", "year").rows() == [("ABW", 1990)]


def test_the_year_is_an_integer_whichever_way_it_arrives():
    """Upstream serves it as a string and the cache as an integer; the two paths must agree."""
    raw = downloaded([("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0)])

    frame = transform_world_bank(raw)

    assert frame.schema["year"] == pl.Int64


def test_indicator_codes_become_readable_names():
    raw = downloaded([("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0)])

    frame = transform_world_bank(raw)

    assert set(frame.columns) == {
        "country_code",
        "year",
        "population_density",
        "gdp_per_cap",
        "Population",
        "real_gdp",
        "surface_area_km2",
    }
    assert frame["gdp_per_cap"].to_list() == [1000.0]


def test_a_country_with_no_iso_code_is_dropped():
    """An unmatched name would otherwise key a row on a null and survive into the panel."""
    raw = downloaded(
        [
            ("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0),
            ("Not A Country", "1990", 1.0, 2.0, 3, 4.0, 5.0),
        ]
    )

    frame = transform_world_bank(raw)

    assert frame["country_code"].to_list() == ["ABW"]


def test_the_result_is_sorted_by_country_and_year():
    raw = downloaded(
        [
            ("Zimbabwe", "1991", 1.0, 1.0, 1, 1.0, 1.0),
            ("Aruba", "1991", 2.0, 2.0, 2, 2.0, 2.0),
            ("Aruba", "1990", 3.0, 3.0, 3, 3.0, 3.0),
        ]
    )

    frame = transform_world_bank(raw)

    assert frame.select("country_code", "year").rows() == [("ABW", 1990), ("ABW", 1991), ("ZWE", 1991)]


def test_a_warm_cache_does_not_download(tmp_path, serves):
    """The download is hundreds of requests; a present cache must not trigger it."""
    calls = serves(downloaded([("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0)]))
    pl.DataFrame(
        {
            "country_code": ["ABW"],
            "year": [1990],
            "population_density": [10.0],
            "gdp_per_cap": [1000.0],
            "Population": [100000],
            "real_gdp": [5.0],
            "surface_area_km2": [180.0],
        }
    ).write_parquet(tmp_path / CACHE_FILE)

    frame = load_wb_data(tmp_path)

    assert calls == []
    assert frame.select("country_code", "year").rows() == [("ABW", 1990)]


def test_the_cold_run_writes_the_cache_it_will_read(tmp_path, serves):
    """A key spelled one way on write and another on read is the bug this replaces."""
    serves(downloaded([("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0)]))

    load_wb_data(tmp_path)

    assert (tmp_path / CACHE_FILE).exists()


def test_the_cold_and_warm_frames_agree(tmp_path, serves):
    """The hand-rolled cache this replaces returned a string year cold and an integer year warm."""
    serves(downloaded([("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0)]))

    cold = load_wb_data(tmp_path)
    warm = load_wb_data(tmp_path)

    assert_frame_equal(cold, warm)


def test_forcing_a_reload_downloads_again(tmp_path, serves):
    calls = serves(downloaded([("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0)]))

    load_wb_data(tmp_path)
    load_wb_data(tmp_path, force_reload=True)

    assert len(calls) == 2


def test_the_download_reaches_back_before_any_indicator_starts(tmp_path, serves):
    """A later start year would silently shorten every series in the panel."""
    calls = serves(downloaded([("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0)]))

    load_wb_data(tmp_path)

    assert calls[0]["start"] == 1900


def test_the_download_tolerates_codes_kuznets_does_not_know(tmp_path, serves):
    """XKX postdates kuznets' code list, and its warning is an error in this suite."""
    calls = serves(downloaded([("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0)]))

    load_wb_data(tmp_path)

    assert calls[0]["errors"] == "ignore"
    assert "XKX" in calls[0]["country"]


def test_every_country_code_is_an_iso_alpha_3():
    """The table is hand-edited; a lower-case or truncated code would fail only on a cold run."""
    malformed = [code for code in COUNTRY_CODE_BY_NAME.values() if not (len(code) == 3 and code.isupper())]

    assert malformed == []


def test_no_two_countries_share_a_code():
    """Two names on one code would silently collapse rows when the download is keyed by code."""
    codes = list(COUNTRY_CODE_BY_NAME.values())

    assert len(codes) == len(set(codes))


def test_kosovo_is_requested_under_the_code_the_world_bank_uses():
    """XKX is not in kuznets' validation list, so it is the row most likely to be tidied away."""
    assert COUNTRY_CODE_BY_NAME["Kosovo"] == "XKX"
    assert "XKX" in REQUESTED_COUNTRY_CODES


def test_the_aggregates_are_not_requested():
    """The Bank returns regional and income aggregates; asking for them would double-count."""
    assert "ARB" not in REQUESTED_COUNTRY_CODES
    assert COUNTRY_CODE_BY_NAME["Arab World"] == "ARB"


def test_no_two_countries_share_a_name():
    """The mapping is built with dict(zip(...)), so a repeated name would quietly overwrite a code."""
    table = pl.read_csv(COUNTRIES_FILE)

    assert len(COUNTRY_CODE_BY_NAME) == len(table)


def test_dropping_an_unmatched_country_says_which_one(caplog):
    """Silent dropping is the failure mode; the warning is the only trace it leaves."""
    raw = downloaded(
        [
            ("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0),
            ("Not A Country", "1990", 1.0, 2.0, 3, 4.0, 5.0),
        ]
    )

    with caplog.at_level(logging.WARNING, logger="climate_risk.data.world_bank"):
        transform_world_bank(raw)

    assert "Not A Country" in caplog.text
