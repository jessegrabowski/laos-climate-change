import numpy as np
import pandas as pd
import pytest

from climate_risk.replication_data import create_replication_data
from tests.conftest import emdat_event

# Long enough that `iloc[1:-1]` still leaves an STL-able series: STL(period=3) needs 2*3+1 points.
YEARS = tuple(range(1985, 1997))

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
    pd.DataFrame(
        world_bank, columns=["country_code", "year", "gdp_per_cap", "population_density", "Population"]
    ).set_index(["country_code", "year"]).to_parquet(tmp_path / "world_bank.parquet")
    pd.DataFrame(
        {"co2": [float(350 + i) for i in range(len(YEARS))]},
        index=pd.DatetimeIndex([f"{year}-01-01" for year in YEARS], name="Date"),
    ).to_parquet(tmp_path / "co2.parquet")
    # A wave rather than a ramp, so STL has a trend to separate a deviation from.
    pd.DataFrame(
        {"Temp": [i + np.sin(i) for i in range(len(YEARS))]},
        index=pd.DatetimeIndex([f"{year}-01-01" for year in YEARS], name="Date"),
    ).to_parquet(tmp_path / "ocean_heat.parquet")
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


def row(frame, iso, year):
    return frame.set_index(["ISO", "year"]).loc[(iso, pd.Timestamp(f"{year}-01-01"))]


def test_the_frame_is_one_row_per_country_and_year(replication):
    assert not replication.duplicated(subset=["ISO", "year"]).any()


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
    known = replication.dropna(subset=["ln_gdp_pc", "ln_population_density"])

    assert len(known) > 0
    assert (known["square_ln_gdp_pc"] == known["ln_gdp_pc"] ** 2).all()
    assert (known["ln_population_density_squared"] == known["ln_population_density"] ** 2).all()


def test_the_time_trend_counts_years_over_a_century(replication):
    """A raw year would dwarf every other regressor; the trend is rescaled."""
    assert row(replication, "AAA", SAMPLE_YEAR)["time_period"] == pytest.approx((SAMPLE_YEAR - TREND_BASE_YEAR) / 100)


def test_total_damage_adds_the_two_classes(replication):
    both = replication.dropna(subset=["Total_Damage_Adjusted_hydro", "Total_Damage_Adjusted_clim"])

    assert len(both) > 0
    assert (
        both["Total_Damage_Adjusted_all"] == both["Total_Damage_Adjusted_hydro"] + both["Total_Damage_Adjusted_clim"]
    ).all()


def test_a_country_with_no_climatological_damage_totals_to_missing(replication):
    """pandas propagates the null through the sum; polars would sum it as zero and invent damage."""
    entry = row(replication, "BBB", SAMPLE_YEAR)

    assert np.isnan(entry["Total_Damage_Adjusted_clim"])
    assert np.isnan(entry["Total_Damage_Adjusted_all"])


def test_a_country_year_with_no_disasters_stays_missing(replication):
    """nan_or_sum keeps no-data distinct from no-disasters, which a zero would erase."""
    quiet = replication[replication["year"] == pd.Timestamp(f"{QUIET_YEAR}-01-01")]

    assert len(quiet) > 0
    assert quiet["hydrological_disasters"].isna().all()


def test_damages_are_converted_to_millions(replication):
    entry = row(replication, "AAA", SAMPLE_YEAR)

    assert entry["damage_millions"] == pytest.approx(entry["Total_Damage_Adjusted_all"] * 1e-6)
    assert entry["Total_Damage_Adjusted_hydro_millions"] == pytest.approx(entry["Total_Damage_Adjusted_hydro"] * 1e-6)


def test_the_damage_logs_are_offset_so_a_zero_survives(replication):
    """Damage of zero is ordinary here, and log(0) is what this epsilon exists to avoid."""
    entry = row(replication, "AAA", SAMPLE_YEAR)

    assert entry["ln_damage_millions"] == pytest.approx(np.log(entry["damage_millions"] + LOG_EPSILON))


def test_precipitation_deviation_is_measured_against_the_country_climatology(replication):
    """Each country is centred on its own mean, so the deviations over the span sum to zero."""
    for iso in ("AAA", "BBB"):
        deviations = replication.loc[replication["ISO"] == iso, "precip_deviation"].dropna()
        assert deviations.sum() == pytest.approx(0.0, abs=1e-9)


def test_the_ocean_temperature_deviation_is_residual_around_its_trend(replication):
    """It is the STL residual, so it is centred near zero and not the level of Temp itself."""
    deviations = replication["dev_from_trend_ocean_temp"].dropna()

    assert deviations.mean() == pytest.approx(0.0, abs=0.5)
    assert deviations.abs().max() < 5.0
