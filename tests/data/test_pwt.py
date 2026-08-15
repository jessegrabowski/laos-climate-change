import polars as pl
import pytest

from climate_risk.data.pwt import PWT, PWT_COLUMNS, transform_pwt

# The cache key is stated literally, so a wrong one fails rather than agreeing with itself.
CACHE_FILE = "penn_world_table.parquet"


def sheet(rows) -> pl.DataFrame:
    """The workbook columns the loader reads, in the order it names them."""
    return pl.DataFrame(rows, schema=["countrycode", "year", *PWT_COLUMNS], orient="row")


def test_the_quantity_series_are_national_accounts_not_purchasing_power():
    """The `o` and `e` families compare levels across countries; mixing families gives a growth
    rate neither family reports. A test on the renaming agrees with whatever code is listed, so
    the codes themselves are the claim.
    """
    assert PWT_COLUMNS["rgdpna"] == "pwt_real_gdp"
    assert PWT_COLUMNS["rkna"] == "capital"

    quantities = [code for code in PWT_COLUMNS if code.startswith(("rgdp", "rk"))]
    assert all(code.endswith("na") for code in quantities), quantities


def test_the_cross_country_productivity_level_is_the_ppp_series():
    """`rtfpna` is an index on a national base and reads 1.0 for every country in its base year, so
    a gap taken from it is an artefact. `ctfp` is the level with the United States at 1.
    """
    assert "rtfpna" not in PWT_COLUMNS
    assert PWT_COLUMNS["ctfp"] == "tfp_relative_to_usa"


def test_a_renamed_column_is_named_in_the_error():
    """A new release dropping or renaming a series must fail loudly, not yield a null column."""
    raw = sheet([("CRI", 1980, 22265.0, 0.213, 0.754, 2.39, 0.5755, 0.0567, 0.8727)]).drop("rkna")

    with pytest.raises(ValueError, match="rkna"):
        transform_pwt(raw)


def test_rows_are_keyed_by_iso_code_and_year():
    raw = sheet([("CRI", 1980, 22265.0, 0.213, 0.754, 2.39, 0.5755, 0.0567, 0.8727)])

    frame = transform_pwt(raw)

    assert frame.columns[:2] == ["country_code", "year"]
    assert frame.select("country_code", "year").rows() == [("CRI", 1980)]


def test_the_result_is_sorted_by_country_and_year():
    raw = sheet(
        [
            ("CRI", 1981, 1.0, 1.0, 1.0, 1.0, 0.5, 0.05, 0.9),
            ("ARG", 1981, 2.0, 2.0, 2.0, 2.0, 0.5, 0.05, 0.9),
            ("ARG", 1980, 3.0, 3.0, 3.0, 3.0, 0.5, 0.05, 0.9),
        ]
    )

    frame = transform_pwt(raw)

    assert frame.select("country_code", "year").rows() == [("ARG", 1980), ("ARG", 1981), ("CRI", 1981)]


def test_a_country_with_no_code_is_dropped():
    """An unkeyed row would survive into the panel and join against nothing."""
    raw = sheet(
        [
            ("CRI", 1980, 1.0, 1.0, 1.0, 1.0, 0.5, 0.05, 0.9),
            (None, 1980, 9.0, 9.0, 9.0, 9.0, 0.9, 0.09, 0.9),
        ]
    )

    frame = transform_pwt(raw)

    assert frame["country_code"].to_list() == ["CRI"]


def test_a_gap_in_a_series_stays_a_gap():
    """Coverage ends in 2019 while the panel runs later, and the model imputes the tail. A null
    silently filled here would be read as a measurement.
    """
    raw = sheet(
        [
            ("CRI", 2019, 94038.7, 1.062, 2.256, 5.048, 0.5798, 0.0487, 0.7445),
            ("CRI", 2020, None, None, None, 5.1, None, None, None),
        ]
    )

    frame = transform_pwt(raw)

    assert frame.filter(pl.col("year") == 2020)["capital"].to_list() == [None]


def test_the_workbook_must_be_placed_by_hand(tmp_path):
    """It is not fetchable, so the error has to say where to get it and where to put it."""
    with pytest.raises(NotImplementedError, match=r"pwt100\.xlsx"):
        PWT.require(tmp_path)
