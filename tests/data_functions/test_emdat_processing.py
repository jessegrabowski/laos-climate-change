import pandas as pd
import pytest

from climate_risk import load_emdat_data
from tests.conftest import emdat_event

WINDOW_START = pd.Timestamp("1969-01-01")
WINDOW_END = pd.Timestamp("2024-01-01")


def test_missing_workbook_names_the_path_it_wants(tmp_path):
    """EM-DAT is licensed and hand-placed, so the error is the user's only instruction."""
    with pytest.raises(NotImplementedError, match=str(tmp_path / "emdat.xlsx")):
        load_emdat_data(tmp_path)


def test_every_country_year_appears_even_without_events(write_emdat_cache):
    """Count models need zero-event country-years present as rows, not absent."""
    cache_dir = write_emdat_cache([emdat_event({"ISO": "AAA"}), emdat_event({"ISO": "BBB", "DisNo.": "1990-0002-BBB"})])

    events = load_emdat_data(cache_dir)["df_prob_filtered_adjusted"]
    years = pd.date_range(WINDOW_START, WINDOW_END, freq="YS-JAN")

    assert events.index.names == ["ISO", "Start_Year"]
    assert set(events.index.get_level_values("ISO")) == {"AAA", "BBB"}
    assert events.index.get_level_values("Start_Year").nunique() == len(years)
    assert len(events) == 2 * len(years)


def test_a_year_without_events_is_nan_not_zero(write_emdat_cache):
    """replication_data's nan_or_sum relies on this to distinguish no-data from no-disasters."""
    cache_dir = write_emdat_cache([emdat_event({"Start Year": 1990})])

    events = load_emdat_data(cache_dir)["df_prob_filtered_adjusted"]

    assert events.loc[("AAA", pd.Timestamp("1990-01-01")), "Flood"] == 1
    assert pd.isna(events.loc[("AAA", pd.Timestamp("1991-01-01")), "Flood"])


def test_region_metadata_survives_reindexing(write_emdat_cache):
    cache_dir = write_emdat_cache([emdat_event({"Region": "Africa", "Subregion": "Eastern Africa"})])

    events = load_emdat_data(cache_dir)["df_prob_filtered_adjusted"]
    quiet_year = events.loc[("AAA", pd.Timestamp("2001-01-01"))]

    assert quiet_year["Region"] == "Africa"
    assert quiet_year["Subregion"] == "Eastern Africa"


def test_hydrometeorological_class_keeps_its_misspelling(write_emdat_cache):
    """The misspelling is the wire value written to every cached CSV. Correcting it breaks them all."""
    cache_dir = write_emdat_cache([emdat_event({"Disaster Type": "Flood"})])

    classes = load_emdat_data(cache_dir)["df_raw"]["disaster_class"]

    assert classes.tolist() == ["Hydrometereological"]


@pytest.mark.parametrize(
    ("disaster_type", "expected_class"),
    [
        ("Flood", "Hydrometereological"),
        ("Storm", "Hydrometereological"),
        ("Drought", "Climatological"),
        ("Wildfire", "Climatological"),
        ("Extreme temperature", "Climatological"),
    ],
)
def test_disaster_types_map_to_their_class(write_emdat_cache, disaster_type, expected_class):
    cache_dir = write_emdat_cache([emdat_event({"Disaster Type": disaster_type})])

    classes = load_emdat_data(cache_dir)["df_raw"]["disaster_class"]

    assert classes.tolist() == [expected_class]


def test_unadjusted_filter_drops_low_casualty_events(write_emdat_cache):
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "keep", "Total Deaths": 500, "Total Affected": 5_000}),
            emdat_event({"DisNo.": "few-deaths", "Total Deaths": 50, "Total Affected": 5_000}),
            emdat_event({"DisNo.": "few-affected", "Total Deaths": 500, "Total Affected": 100}),
        ]
    )

    kept = load_emdat_data(cache_dir)["df_raw_filtered"]["DisNo."]

    assert kept.tolist() == ["keep"]


def test_adjusted_filter_ignores_deaths_but_starts_in_1981(write_emdat_cache):
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "kept-no-deaths", "Start Year": 1990, "Total Deaths": 0}),
            emdat_event({"DisNo.": "too-early", "Start Year": 1975}),
        ]
    )

    kept = load_emdat_data(cache_dir)["df_raw_filtered_adj"]["DisNo."]

    assert kept.tolist() == ["kept-no-deaths"]


@pytest.mark.xfail(
    reason="the 1969-2024 window is hardcoded, so refreshed EM-DAT downloads lose their newest years",
    raises=AssertionError,
)
def test_events_after_the_window_are_not_discarded(write_emdat_cache):
    cache_dir = write_emdat_cache([emdat_event({"Start Year": 2025})])

    events = load_emdat_data(cache_dir)["df_prob_filtered_adjusted"]

    assert pd.Timestamp("2025-01-01") in events.index.get_level_values("Start_Year")


@pytest.mark.xfail(
    reason="disaster_class_dict says 'Mass movement (wet)' but PROB_COLS says 'Mass Movement (Wet)'",
    raises=KeyError,
)
def test_mass_movement_events_reach_the_count_frames(write_emdat_cache):
    """The row is classed Hydrometereological, then dropped by a case-sensitive query."""
    cache_dir = write_emdat_cache([emdat_event({"Disaster Type": "Mass movement (wet)"})])

    events = load_emdat_data(cache_dir)["df_prob_filtered_adjusted"]

    assert events.loc[("AAA", pd.Timestamp("1990-01-01")), "Mass movement (wet)"] == 1
