from datetime import date, datetime

import polars as pl
import pytest

from climate_risk import load_all_data
from climate_risk.data_functions.combine_data import _annual_precipitation
from tests.conftest import emdat_event, write_merge_cache


@pytest.fixture(scope="module")
def merged(tmp_path_factory):
    """Built once: every test here only reads the merge, and rebuilding it per test dominated them."""
    return load_all_data(write_merge_cache(tmp_path_factory.mktemp("merge")))


@pytest.mark.parametrize("frame", ["emdat_events", "emdat_damage", "wb_data"])
def test_a_country_missing_from_either_disaster_source_is_dropped(merged, frame):
    """CCC has no World Bank data and DDD no EM-DAT data, so neither belongs in the panel."""
    assert sorted(merged[frame]["ISO"].unique()) == ["AAA", "BBB", "EEE"]


def test_precipitation_is_reconciled_separately(merged):
    """EEE has no precipitation and FFF has nothing else, so each is dropped by a different pass."""
    assert sorted(merged["gpcc"]["ISO"].unique()) == ["AAA", "BBB"]
    assert "EEE" in merged["wb_data"]["ISO"].to_list()


def test_the_panel_spans_the_full_country_year_grid(merged):
    panel = merged["df_panel"]

    countries = panel["ISO"].n_unique()
    years = panel["Start_Year"].n_unique()

    assert len(panel) == countries * years
    assert not panel.select("ISO", "Start_Year").is_duplicated().any()


def test_a_country_year_with_no_indicators_still_reaches_the_panel(merged):
    """The panel is an outer join: EM-DAT reaches back to 1969, the indicators only cover 1990-91."""
    early = merged["df_panel"].filter(pl.col("Start_Year") == date(1970, 1, 1))

    assert len(early) > 0
    assert early["gdp_per_cap"].is_null().all()


def test_precipitation_is_totalled_over_the_year_not_averaged(merged):
    """GPCC publishes monthly; the panel wants the year's total rainfall, not a monthly mean."""
    annual = merged["gpcc"].filter((pl.col("ISO") == "AAA") & (pl.col("year") == date(1990, 1, 1)))

    # AAA's 1990 months run 101..112, totalling 1278 against a monthly mean of 106.5.
    assert annual["precip"].to_list() == [pytest.approx(1278.0)]


def test_a_year_the_record_only_partly_covers_is_dropped():
    """The near-real-time product ends mid-year, and a part-year total reads as a drought, not a gap."""
    monthly = pl.DataFrame(
        {
            "country_code": ["AAA"] * 15,
            "time": [datetime(2020, month, 1) for month in range(1, 13)]
            + [datetime(2021, month, 1) for month in range(1, 4)],
            "precip": [10.0] * 15,
        }
    )

    by_country, worldwide = _annual_precipitation(monthly)

    assert by_country["year"].to_list() == [date(2020, 1, 1)]
    assert worldwide["year"].to_list() == [date(2020, 1, 1)]


def test_the_worldwide_series_totals_every_country(merged):
    """It feeds a country-invariant regressor, so it sums across countries rather than averaging."""
    nineteen_ninety = merged["gpcc_agg"].filter(pl.col("year") == date(1990, 1, 1))

    assert nineteen_ninety["precip"].to_list() == [pytest.approx(1278.0 + 2478.0 + 3678.0)]


def test_the_time_series_carries_no_country(merged):
    """The aggregate series feed country-invariant regressors, so an ISO level would broadcast wrong."""
    assert merged["df_time_series"].columns[0] == "year"
    assert "ISO" not in merged["df_time_series"].columns
    assert {"co2", "Temp", "precip"} <= set(merged["df_time_series"].columns)


def test_country_constants_hold_one_row_per_country(merged):
    """Built before reconciliation, so it keeps CCC, which every reconciled frame drops."""
    constants = merged["country_constants"]

    assert sorted(constants["ISO"]) == ["AAA", "BBB", "CCC", "EEE"]
    assert not constants["ISO"].is_duplicated().any()
    assert "Start_Year" not in constants.columns


def test_every_disaster_type_gets_a_column_even_when_unobserved(write_emdat_cache, write_full_cache):
    """Unstacking yields a column per observed type, so downstream code naming all of them breaks."""
    cache_dir = write_full_cache()
    write_emdat_cache(
        emdat_event({"ISO": iso, "DisNo.": f"{iso}-{year}", "Start Year": year, "Disaster Type": "Drought"})
        for iso in ("AAA", "BBB")
        for year in (1990, 1991)
    )

    events = load_all_data(cache_dir)["emdat_events"]

    assert {"Drought", "Flood", "Storm", "Wildfire", "Extreme temperature"} <= set(events.columns)
    assert events["Wildfire"].is_null().all()


def test_damage_columns_survive_a_class_with_no_events(write_emdat_cache, write_full_cache):
    """An empty pivot emits no columns at all, so a country with only floods loses the clim split."""
    cache_dir = write_full_cache()
    write_emdat_cache(
        emdat_event({"ISO": iso, "DisNo.": f"{iso}-{year}", "Start Year": year, "Disaster Type": "Flood"})
        for iso in ("AAA", "BBB")
        for year in (1990, 1991)
    )

    damage = load_all_data(cache_dir)["emdat_damage"]

    assert "Total_Damage_Adjusted_clim" in damage.columns
    assert damage["Total_Damage_Adjusted_clim"].is_null().all()


def test_hydro_and_clim_damage_columns_are_suffixed(merged):
    """Both splits carry the same variable names, so they collide unless suffixed apart."""
    damage = merged["emdat_damage"]

    assert "Total_Damage_Adjusted_hydro" in damage.columns
    assert "Total_Damage_Adjusted_clim" in damage.columns


def test_world_bank_years_become_timestamps(merged):
    """The panel joins on Start_Year, which EM-DAT supplies as a timestamp."""
    assert merged["wb_data"].schema["Start_Year"] == pl.Date
