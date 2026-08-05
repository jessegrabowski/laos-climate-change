import pandas as pd
import pytest

from climate_risk import load_all_data
from tests.conftest import emdat_event


@pytest.fixture
def merged(write_full_cache):
    return load_all_data(write_full_cache())


@pytest.mark.parametrize("frame", ["emdat_events", "emdat_damage", "wb_data"])
def test_a_country_missing_from_either_disaster_source_is_dropped(merged, frame):
    """CCC has no World Bank data and DDD no EM-DAT data, so neither belongs in the panel."""
    assert sorted(set(merged[frame].index.get_level_values("ISO"))) == ["AAA", "BBB", "EEE"]


def test_precipitation_is_reconciled_separately(merged):
    """EEE has no precipitation and FFF has nothing else, so each is dropped by a different pass."""
    countries_with_precipitation = set(merged["gpcc"].index.get_level_values("ISO"))

    assert sorted(countries_with_precipitation) == ["AAA", "BBB"]
    assert "EEE" in set(merged["wb_data"].index.get_level_values("ISO"))


def test_the_panel_spans_the_full_country_year_grid(merged):
    panel = merged["df_panel"]

    countries = panel.index.get_level_values("ISO").nunique()
    years = panel.index.get_level_values("Start_Year").nunique()

    assert len(panel) == countries * years
    assert panel.index.is_unique


def test_the_time_series_carries_no_country(merged):
    """The aggregate series feed country-invariant regressors, so an ISO level would broadcast wrong."""
    assert merged["df_time_series"].index.names == ["year"]
    assert {"co2", "Temp", "precip"} <= set(merged["df_time_series"].columns)


def test_country_constants_hold_one_row_per_country(merged):
    """Built before reconciliation, so it keeps CCC, which every reconciled frame drops."""
    constants = merged["country_constants"]

    assert sorted(constants.index) == ["AAA", "BBB", "CCC", "EEE"]
    assert constants.index.is_unique
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
    assert events["Wildfire"].isna().all()


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
    assert damage["Total_Damage_Adjusted_clim"].isna().all()


def test_hydro_and_clim_damage_columns_are_suffixed(merged):
    """Both splits carry the same variable names, so they collide unless suffixed apart."""
    damage = merged["emdat_damage"]

    assert "Total_Damage_Adjusted_hydro" in damage.columns
    assert "Total_Damage_Adjusted_clim" in damage.columns


def test_world_bank_years_become_timestamps(merged):
    """The panel joins on Start_Year, which EM-DAT supplies as a timestamp."""
    assert isinstance(merged["wb_data"].index.get_level_values("Start_Year"), pd.DatetimeIndex)
