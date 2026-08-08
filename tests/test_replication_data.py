from datetime import date

import numpy as np
import pandas as pd
import polars as pl
import pytest

from climate_risk.replication_data import create_replication_data
from tests.conftest import emdat_event

# Long enough that `iloc[1:-1]` still leaves an STL-able series: STL(period=3) needs 2*3+1 points.
# Longer than CLIMATOLOGY_YEARS, so the baseline window is a real subset of the record.
YEARS = tuple(range(1985, 2021))

# AAA and BBB appear everywhere. CCC is EM-DAT only and DDD World Bank only, so reconciliation has
# something to drop from each side. EEE has both but no precipitation; FFF has only precipitation.
EMDAT_COUNTRIES = ("AAA", "BBB", "CCC", "EEE")
WORLD_BANK_COUNTRIES = ("AAA", "BBB", "DDD", "EEE")
PRECIPITATION_COUNTRIES = ("AAA", "BBB", "FFF")

# Stated literally rather than imported, so a changed constant fails instead of moving with it.
TREND_BASE_YEAR = 1980
LOG_EPSILON = 1e-6

# The second year of the span, so the expected values below are the fixture's formulas at i = 1.
SAMPLE_YEAR = YEARS[1]

# The panel grid reaches back before the first event, so these carry no disasters at all.
QUIET_YEAR = 1975


@pytest.fixture
def wide_cache(tmp_path, write_emdat_cache):
    """A cache spanning enough years for the trend fit and the climatology to do anything.

    AAA gets a drought on top of its flood, so climatological and hydrological damage are both
    present for one country and only hydrological for the others.
    """
    events = [
        emdat_event({"ISO": iso, "DisNo.": f"{iso}-{year}", "Start Year": year, "End Year": year})
        for iso in EMDAT_COUNTRIES
        for year in YEARS
    ]
    events += [
        emdat_event(
            {
                "ISO": "AAA",
                "DisNo.": f"AAA-drought-{year}",
                "Start Year": year,
                "End Year": year,
                "Disaster Type": "Drought",
            }
        )
        for year in YEARS
    ]
    write_emdat_cache(events)

    world_bank = [
        (iso, year, 1000 + 100 * n + 10 * i, 10 + 10 * n + i, 1_000_000 + 100_000 * n + 1000 * i)
        for n, iso in enumerate(WORLD_BANK_COUNTRIES)
        for i, year in enumerate(YEARS)
    ]
    pl.DataFrame(
        world_bank,
        schema=["country_code", "year", "gdp_per_cap", "population_density", "Population"],
        orient="row",
    ).write_parquet(tmp_path / "world_bank.parquet")
    pl.DataFrame(
        {"Date": [date(year, 1, 1) for year in YEARS], "co2": [float(350 + i) for i in range(len(YEARS))]}
    ).write_parquet(tmp_path / "co2.parquet")
    # A wave rather than a ramp, so STL has a trend to separate a deviation from.
    pl.DataFrame(
        {"Date": [date(year, 1, 1) for year in YEARS], "Temp": [i + np.sin(i) for i in range(len(YEARS))]}
    ).write_parquet(tmp_path / "ocean_heat.parquet")
    precipitation = [
        (iso, pd.Timestamp(f"{year}-01-01"), 100.0 * (n + 1) + 5 * i)
        for n, iso in enumerate(PRECIPITATION_COUNTRIES)
        for i, year in enumerate(YEARS)
    ]
    pd.DataFrame(precipitation, columns=["country_code", "time", "precip"]).set_index(
        ["country_code", "time"]
    ).to_parquet(tmp_path / "gpcc__repaired_iso=True.parquet")
    return tmp_path


@pytest.fixture
def replication(wide_cache):
    return create_replication_data(wide_cache)


def row(frame: pl.DataFrame, iso: str, year: int) -> dict:
    """The one row for a country and year, as a plain mapping."""
    match = frame.filter((pl.col("ISO") == iso) & (pl.col("year") == date(year, 1, 1)))

    assert len(match) == 1, f"expected one row for {iso} {year}, got {len(match)}"
    return match.to_dicts()[0]


def test_the_frame_is_one_row_per_country_and_year(replication):
    assert not replication.select("ISO", "year").is_duplicated().any()


def test_only_countries_present_in_both_disaster_and_indicator_data_survive(replication):
    """CCC has no World Bank data and DDD no EM-DAT, so neither belongs in the panel."""
    assert sorted(replication["ISO"].unique()) == ["AAA", "BBB", "EEE"]


def test_the_published_columns_are_all_present(replication):
    """Downstream models select by name, so a dropped column is a silent regression."""
    expected = {
        "ISO",
        "year",
        "climatological_disasters",
        "hydrological_disasters",
        "population",
        "ln_population_density",
        "ln_gdp_pc",
        "square_ln_gdp_pc",
        "dev_from_trend_ocean_temp",
        "co2",
        "precip_deviation",
        "Total_Damage_Adjusted_hydro",
        "Total_Damage_Adjusted_clim",
        "Total_Affected_hydro",
        "ln_population_density_squared",
        "time_period",
        "Total_Damage_Adjusted_all",
        "Total_Damage_Adjusted_hydro_millions",
        "damage_millions",
        "ln_damage_millions",
        "ln_Total_Damage_Adjusted_hydro_millions",
    }

    assert set(replication.columns) == expected


def test_population_is_reported_in_millions(replication):
    """The regressor is in millions; the World Bank supplies raw headcounts."""
    assert row(replication, "AAA", SAMPLE_YEAR)["population"] == pytest.approx(1.001)


def test_the_gdp_and_density_logs_are_natural(replication):
    entry = row(replication, "AAA", SAMPLE_YEAR)

    assert entry["ln_gdp_pc"] == pytest.approx(np.log(1010))
    assert entry["ln_population_density"] == pytest.approx(np.log(11))


def test_both_squared_terms_square_their_own_log(replication):
    """One is written as a product and the other as a power; both must hold for every row."""
    known = replication.drop_nulls(["ln_gdp_pc", "ln_population_density"])

    assert len(known) > 0
    assert (known["square_ln_gdp_pc"] - known["ln_gdp_pc"] ** 2).abs().max() < 1e-12
    assert (known["ln_population_density_squared"] - known["ln_population_density"] ** 2).abs().max() < 1e-12


def test_the_time_trend_counts_years_over_a_century(replication):
    """A raw year would dwarf every other regressor; the trend is rescaled."""
    assert row(replication, "AAA", SAMPLE_YEAR)["time_period"] == pytest.approx((SAMPLE_YEAR - TREND_BASE_YEAR) / 100)


def test_total_damage_adds_the_two_classes(replication):
    both = replication.drop_nulls(["Total_Damage_Adjusted_hydro", "Total_Damage_Adjusted_clim"])

    assert len(both) > 0
    expected = both["Total_Damage_Adjusted_hydro"] + both["Total_Damage_Adjusted_clim"]
    assert (both["Total_Damage_Adjusted_all"] - expected).abs().max() < 1e-9


def test_a_country_with_no_climatological_damage_totals_to_missing(replication):
    """pandas propagates the null through the sum; polars would sum it as zero and invent damage."""
    entry = row(replication, "BBB", SAMPLE_YEAR)

    assert entry["Total_Damage_Adjusted_clim"] is None
    assert entry["Total_Damage_Adjusted_all"] is None


def test_a_country_year_with_no_disasters_stays_missing(replication):
    """A country-year with no record stays missing; summing it as a zero would erase the distinction."""
    quiet = replication.filter(pl.col("year") == date(QUIET_YEAR, 1, 1))

    assert len(quiet) > 0
    assert quiet["hydrological_disasters"].is_null().all()


def test_damages_are_converted_to_millions(replication):
    entry = row(replication, "AAA", SAMPLE_YEAR)

    assert entry["damage_millions"] == pytest.approx(entry["Total_Damage_Adjusted_all"] * 1e-6)
    assert entry["Total_Damage_Adjusted_hydro_millions"] == pytest.approx(entry["Total_Damage_Adjusted_hydro"] * 1e-6)


def test_the_damage_logs_are_offset_so_a_zero_survives(replication):
    """Damage of zero is ordinary here, and log(0) is what this epsilon exists to avoid."""
    entry = row(replication, "AAA", SAMPLE_YEAR)

    assert entry["ln_damage_millions"] == pytest.approx(np.log(entry["damage_millions"] + LOG_EPSILON))


def test_precipitation_deviation_is_measured_against_the_opening_window(replication):
    """The baseline is the first years of the record, not the whole of it."""
    # AAA's precipitation runs 100 + 5i over 36 years: the first 30 average 172.5, all 36 average
    # 187.5. Only the opening window centres the first year on -72.5.
    opening = replication.filter((pl.col("ISO") == "AAA") & (pl.col("year") == date(YEARS[0], 1, 1)))

    assert opening["precip_deviation"].to_list() == [pytest.approx(-72.5)]


def test_the_ocean_temperature_deviation_is_residual_around_its_trend(replication):
    """It is the STL residual, so it is centred near zero and not the level of Temp itself."""
    deviations = replication["dev_from_trend_ocean_temp"].drop_nulls()

    assert deviations.mean() == pytest.approx(0.0, abs=0.5)
    assert deviations.abs().max() < 5.0
