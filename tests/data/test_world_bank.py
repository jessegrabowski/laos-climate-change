import logging

import polars as pl
import pytest

from polars.testing import assert_frame_equal

from climate_risk.data import world_bank
from climate_risk.data.world_bank import (
    COUNTRIES_FILE,
    COUNTRY_CODE_BY_NAME,
    INDICATOR_NAMES,
    MACRO_INDICATOR_NAMES,
    REQUESTED_COUNTRY_CODES,
    WB_INDICATORS,
    WB_MACRO_INDICATORS,
    load_wb_data,
    load_wb_macro_data,
    transform_world_bank,
)

# The cache key is stated literally, so a wrong one fails rather than agreeing with itself.
CACHE_FILE = "world_bank.parquet"


def downloaded(rows) -> pl.DataFrame:
    """Indicators shaped as kuznets returns them tidy, with the year dated rather than numbered."""
    frame = pl.DataFrame(rows, schema=["country", "year", *WB_INDICATORS], orient="row")

    return frame.with_columns(pl.col("year").str.to_datetime("%Y"))


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

    frame = transform_world_bank(raw, INDICATOR_NAMES)

    assert frame.columns[:2] == ["country_code", "year"]
    assert frame.select("country_code", "year").rows() == [("ABW", 1990)]


def test_the_dated_year_becomes_an_integer():
    """Upstream dates the year; casting that date rather than reading it yields microseconds."""
    raw = downloaded([("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0)])

    frame = transform_world_bank(raw, INDICATOR_NAMES)

    assert frame.schema["year"] == pl.Int64


def test_indicator_codes_become_readable_names():
    raw = downloaded([("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0)])

    frame = transform_world_bank(raw, INDICATOR_NAMES)

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


def test_the_gdp_series_are_both_constant_price():
    """`downloaded` builds its columns from WB_INDICATORS, so a renaming test agrees with whatever
    code is listed and cannot see a wrong one. The codes carry the units: KD is constant 2015 US$,
    CD is current US$ and moves with domestic inflation and the exchange rate. Mixing them makes
    `real_gdp / Population` disagree with the published `gdp_per_cap`.
    """
    assert INDICATOR_NAMES["NY.GDP.MKTP.KD"] == "real_gdp"
    assert INDICATOR_NAMES["NY.GDP.PCAP.KD"] == "gdp_per_cap"

    priced = [code for code in WB_INDICATORS if code.startswith("NY.GDP")]
    assert all(code.endswith(".KD") for code in priced), priced


def test_a_country_with_no_iso_code_is_dropped():
    """An unmatched name would otherwise key a row on a null and survive into the panel."""
    raw = downloaded(
        [
            ("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0),
            ("Not A Country", "1990", 1.0, 2.0, 3, 4.0, 5.0),
        ]
    )

    frame = transform_world_bank(raw, INDICATOR_NAMES)

    assert frame["country_code"].to_list() == ["ABW"]


def test_the_result_is_sorted_by_country_and_year():
    raw = downloaded(
        [
            ("Zimbabwe", "1991", 1.0, 1.0, 1, 1.0, 1.0),
            ("Aruba", "1991", 2.0, 2.0, 2, 2.0, 2.0),
            ("Aruba", "1990", 3.0, 3.0, 3, 3.0, 3.0),
        ]
    )

    frame = transform_world_bank(raw, INDICATOR_NAMES)

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


def test_every_country_code_is_an_iso_alpha_3():
    """The table is hand-edited; a lower-case or truncated code would fail only on a cold run."""
    malformed = [code for code in COUNTRY_CODE_BY_NAME.values() if not (len(code) == 3 and code.isupper())]

    assert malformed == []


def test_no_two_countries_share_a_code():
    """Two names on one code would silently collapse rows when the download is keyed by code."""
    codes = list(COUNTRY_CODE_BY_NAME.values())

    assert len(codes) == len(set(codes))


def test_kosovo_is_requested_under_the_code_the_world_bank_uses():
    """The World Bank serves Kosovo under a code no ISO 3166-1 standard assigns."""
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
        transform_world_bank(raw, INDICATOR_NAMES)

    assert "Not A Country" in caplog.text


def test_a_backend_other_than_polars_is_rejected(tmp_path, monkeypatch):
    """The transform is polars-only, so a frame from another backend must fail here, not in a select."""
    monkeypatch.setattr(world_bank.wb, "download", lambda **kwargs: object())

    with pytest.raises(TypeError, match="output_type='polars'"):
        load_wb_data(tmp_path)


def macro_downloaded(rows) -> pl.DataFrame:
    """The macro indicators shaped as kuznets returns them tidy."""
    frame = pl.DataFrame(rows, schema=["country", "year", *WB_MACRO_INDICATORS], orient="row")

    return frame.with_columns(pl.col("year").str.to_datetime("%Y"))


def macro_row(country: str = "Aruba", year: str = "1990"):
    return (country, year, *range(len(WB_MACRO_INDICATORS)))


def test_the_macro_panel_is_keyed_the_same_way_as_the_indicator_panel():
    """Both panels key on country_code and year so they can be joined without restating either."""
    frame = transform_world_bank(macro_downloaded([macro_row()]), MACRO_INDICATOR_NAMES)

    assert frame.columns[:2] == ["country_code", "year"]
    assert frame.select("country_code", "year").rows() == [("ABW", 1990)]


def test_the_real_quantities_and_the_local_currency_codes_are_the_same_set():
    """The model's ratios are formed within a country, so its real quantities must share one unit. A
    KD series among them converts at a market exchange rate, moving every ratio built from it. The
    check runs both ways: a `.KN` code named without the suffix is as wrong as the reverse.
    """
    suffixed = {code for code, name in MACRO_INDICATOR_NAMES.items() if name.endswith("_lcu")}
    local_currency = {code for code in MACRO_INDICATOR_NAMES if code.endswith(".KN")}

    assert local_currency, "no constant-local-currency indicators found"
    assert suffixed == local_currency


def test_the_two_panels_share_no_column_name():
    """`real_gdp` is constant US$ in one panel. A name carrying two units across the two frames is a
    silent unit mix on any join between them.
    """
    assert set(INDICATOR_NAMES.values()).isdisjoint(MACRO_INDICATOR_NAMES.values())


def test_no_two_macro_indicators_share_a_name():
    """The names become columns, so a repeated one would silently drop an indicator from the panel."""
    names = list(MACRO_INDICATOR_NAMES.values())

    assert len(names) == len(set(names))


def test_the_macro_panel_caches_apart_from_the_indicator_panel(tmp_path, serves):
    """One cache key for both would serve whichever panel was downloaded first to both callers."""
    serves(macro_downloaded([macro_row()]))

    load_wb_macro_data(tmp_path)

    assert (tmp_path / "world_bank_macro.parquet").exists()
    assert not (tmp_path / CACHE_FILE).exists()


def test_the_macro_download_asks_for_the_macro_indicators(tmp_path, serves):
    calls = serves(macro_downloaded([macro_row()]))

    load_wb_macro_data(tmp_path)

    assert calls[0]["indicator"] == WB_MACRO_INDICATORS


def test_the_macro_panel_covers_every_requested_country(tmp_path, serves):
    """The model is estimated per country, so the panel must not be narrowed to any one of them."""
    calls = serves(macro_downloaded([macro_row()]))

    load_wb_macro_data(tmp_path)

    assert calls[0]["country"] == REQUESTED_COUNTRY_CODES


def test_an_indicator_the_bank_no_longer_serves_is_named():
    """kuznets warns and omits the column rather than raising, so without this the failure surfaces
    from the select as a polars error naming a column, after the whole panel has been downloaded.
    """
    retired = downloaded([("Aruba", "1990", 10.0, 1000.0, 100000, 5.0, 180.0)]).drop("AG.SRF.TOTL.K2")

    with pytest.raises(ValueError, match=r"AG\.SRF\.TOTL\.K2"):
        transform_world_bank(retired, INDICATOR_NAMES)
