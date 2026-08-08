from datetime import date

import polars as pl
import pytest

from climate_risk import load_emdat_data
from climate_risk.config.schema import EventFilters
from climate_risk.data_functions.emdat_processing import DISASTER_TYPES
from tests.conftest import emdat_event

WINDOW_START = date(1969, 1, 1)


def row(frame: pl.DataFrame, iso: str, year: str) -> dict:
    """The one row for a country and year, as a plain mapping."""
    match = frame.filter((pl.col("ISO") == iso) & (pl.col("Start_Year") == date.fromisoformat(year)))

    assert len(match) == 1, f"expected one row for {iso} {year}, got {len(match)}"
    return match.to_dicts()[0]


def test_missing_workbook_names_the_path_it_wants(tmp_path):
    """EM-DAT is licensed and hand-placed, so the error is the user's only instruction."""
    with pytest.raises(NotImplementedError, match=str(tmp_path / "emdat.xlsx")):
        load_emdat_data(tmp_path)


def test_empty_workbook_is_rejected(write_emdat_cache):
    with pytest.raises(ValueError, match="has no rows"):
        load_emdat_data(write_emdat_cache([]))


def test_workbook_missing_a_column_names_it(write_emdat_cache):
    """Nothing else detects upstream schema drift, so the loader has to."""
    event = emdat_event()
    del event["Total Affected"]

    with pytest.raises(ValueError, match=r"missing \['Total Affected'\]"):
        load_emdat_data(write_emdat_cache([event]))


def test_every_country_year_appears_even_without_events(write_emdat_cache):
    """Count models need zero-event country-years present as rows, not absent."""
    cache_dir = write_emdat_cache([emdat_event({"ISO": "AAA"}), emdat_event({"ISO": "BBB", "DisNo.": "1990-0002-BBB"})])

    events = load_emdat_data(cache_dir)["df_prob_filtered_adjusted"]
    years = range(WINDOW_START.year, 1991)

    assert events.columns[:2] == ["ISO", "Start_Year"]
    assert set(events["ISO"]) == {"AAA", "BBB"}
    assert events["Start_Year"].n_unique() == len(years)
    assert len(events) == 2 * len(years)


def test_window_start_can_be_overridden(write_emdat_cache):
    cache_dir = write_emdat_cache([emdat_event({"Start Year": 1990})])

    years = load_emdat_data(cache_dir, window_start=date(1985, 1, 1))["df_prob_filtered_adjusted"]

    assert years["Start_Year"].min() == date(1985, 1, 1)


def test_window_start_after_the_newest_event_is_rejected(write_emdat_cache):
    """An empty window would otherwise return every frame with zero rows and no error."""
    cache_dir = write_emdat_cache([emdat_event({"Start Year": 1990})])

    with pytest.raises(ValueError, match="every output frame would be empty"):
        load_emdat_data(cache_dir, window_start=date(2001, 1, 1))


def test_a_year_without_events_is_nan_not_zero(write_emdat_cache):
    """The replication panel relies on this to distinguish no-data from no-disasters."""
    cache_dir = write_emdat_cache(
        [emdat_event({"Start Year": 1990}), emdat_event({"DisNo.": "later", "Start Year": 1995})]
    )

    events = load_emdat_data(cache_dir)["df_prob_filtered_adjusted"]

    assert row(events, "AAA", "1990-01-01")["Flood"] == 1
    assert row(events, "AAA", "1991-01-01")["Flood"] is None


def test_region_metadata_survives_reindexing(write_emdat_cache):
    cache_dir = write_emdat_cache(
        [
            emdat_event({"Region": "Africa", "Subregion": "Eastern Africa"}),
            emdat_event({"DisNo.": "later", "Start Year": 2001, "Region": "Africa", "Subregion": "Eastern Africa"}),
        ]
    )

    events = load_emdat_data(cache_dir)["df_prob_filtered_adjusted"]
    quiet_year = row(events, "AAA", "1995-01-01")

    assert quiet_year["Region"] == "Africa"
    assert quiet_year["Subregion"] == "Eastern Africa"


@pytest.mark.parametrize(
    ("disaster_type", "expected_class"),
    [
        ("Flood", "Hydrometereological"),
        ("Storm", "Hydrometereological"),
        ("Drought", "Climatological"),
        ("Wildfire", "Climatological"),
        ("Extreme temperature", "Climatological"),
        ("Mass movement (wet)", "Hydrometereological"),
    ],
)
def test_disaster_types_map_to_their_class(write_emdat_cache, disaster_type, expected_class):
    """`Hydrometereological` is misspelled on purpose: it is the wire value in every cached CSV."""
    cache_dir = write_emdat_cache([emdat_event({"Disaster Type": disaster_type})])

    classes = load_emdat_data(cache_dir)["df_raw"]["disaster_class"]

    assert classes.to_list() == [expected_class]


def test_unadjusted_filter_drops_low_casualty_events(write_emdat_cache):
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "keep", "Total Deaths": 500, "Total Affected": 5_000}),
            emdat_event({"DisNo.": "few-deaths", "Total Deaths": 50, "Total Affected": 5_000}),
            emdat_event({"DisNo.": "few-affected", "Total Deaths": 500, "Total Affected": 100}),
        ]
    )

    kept = load_emdat_data(cache_dir)["df_raw_filtered"]["DisNo."]

    assert kept.to_list() == ["keep"]


def test_adjusted_filter_ignores_deaths_but_starts_in_1981(write_emdat_cache):
    """1980 itself is excluded, so the boundary is pinned on both sides rather than approximately."""
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "kept-no-deaths", "Start Year": 1990, "Total Deaths": 0}),
            emdat_event({"DisNo.": "first-year", "Start Year": 1981}),
            emdat_event({"DisNo.": "boundary-year", "Start Year": 1980}),
            emdat_event({"DisNo.": "too-early", "Start Year": 1975}),
        ]
    )

    kept = load_emdat_data(cache_dir)["df_raw_filtered_adj"]["DisNo."]

    assert sorted(kept.to_list()) == ["first-year", "kept-no-deaths"]


def test_an_event_exactly_on_the_affected_threshold_does_not_count(write_emdat_cache):
    """The threshold is strict, and an event sitting on it is the only way to tell that apart."""
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "over", "Start Year": 1995, "Total Affected": 1_001}),
            emdat_event({"DisNo.": "exactly-on-it", "Start Year": 1995, "Total Affected": 1_000}),
        ]
    )

    kept = load_emdat_data(cache_dir)["df_raw_filtered_adj"]["DisNo."]

    assert kept.to_list() == ["over"]


def test_the_adjusted_view_follows_the_filters_it_is_given(write_emdat_cache):
    """The window is a place's setting, so a place with a shorter one must get a shorter panel."""
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "in-window", "Start Year": 1995}),
            emdat_event({"DisNo.": "before-window", "Start Year": 1985}),
        ]
    )

    kept = load_emdat_data(cache_dir, filters=EventFilters(start_year=1990))["df_raw_filtered_adj"]["DisNo."]

    assert kept.to_list() == ["in-window"]


def test_a_deaths_threshold_applies_only_when_a_place_sets_one(write_emdat_cache):
    """The default counts an event on reach alone, so a deadly-but-small event needs an explicit floor."""
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "deadly", "Start Year": 1995, "Total Deaths": 500}),
            emdat_event({"DisNo.": "harmless", "Start Year": 1995, "Total Deaths": 0}),
        ]
    )

    by_default = load_emdat_data(cache_dir)["df_raw_filtered_adj"]["DisNo."]
    with_a_floor = load_emdat_data(cache_dir, filters=EventFilters(min_deaths=100))["df_raw_filtered_adj"]["DisNo."]

    assert by_default.to_list() == ["deadly", "harmless"]
    assert with_a_floor.to_list() == ["deadly"]


def test_a_place_can_close_its_window_before_the_newest_event(write_emdat_cache):
    """`end_year` is the only filter that trims the recent end, and it counts its own year."""
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "in-window", "Start Year": 1995}),
            emdat_event({"DisNo.": "last-year", "Start Year": 2000}),
            emdat_event({"DisNo.": "after-window", "Start Year": 2005}),
        ]
    )

    kept = load_emdat_data(cache_dir, filters=EventFilters(end_year=2000))["df_raw_filtered_adj"]["DisNo."]

    assert kept.to_list() == ["in-window", "last-year"]


def test_the_window_extends_to_the_newest_event(write_emdat_cache):
    """A refreshed download must extend the panel, not silently lose its newest years."""
    cache_dir = write_emdat_cache([emdat_event({"Start Year": 2025})])

    years = load_emdat_data(cache_dir)["df_prob_filtered_adjusted"]["Start_Year"]

    assert years.max() == date(2025, 1, 1)
    assert years.min() == WINDOW_START


def test_mass_movement_events_reach_the_count_frames(write_emdat_cache):
    cache_dir = write_emdat_cache([emdat_event({"Disaster Type": "Mass movement (wet)"})])

    events = load_emdat_data(cache_dir)["df_prob_filtered_adjusted"]

    assert row(events, "AAA", "1990-01-01")["Mass movement (wet)"] == 1


def test_the_workbook_row_number_survives_filtering(write_emdat_cache):
    """disaster_point_data stores this number in its own cache, so it keys back into the workbook."""
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "too-early", "Start Year": 1975}),
            emdat_event({"DisNo.": "kept", "Start Year": 1990}),
        ]
    )

    result = load_emdat_data(cache_dir)

    assert result["df_raw"]["emdat_index"].to_list() == [0, 1]
    assert result["df_raw_filtered_adj"].filter(pl.col("DisNo.") == "kept")["emdat_index"].to_list() == [1]


def test_a_workbook_with_no_usable_year_is_rejected(write_emdat_cache):
    """A null Start_Year leaves the window with no end, which would otherwise fail deep in a join."""
    cache_dir = write_emdat_cache([emdat_event({"Start Year": None})])

    with pytest.raises(ValueError, match="Every Start_Year in the workbook is missing"):
        load_emdat_data(cache_dir)


def test_every_disaster_type_gets_a_column_in_a_stable_order(write_emdat_cache):
    """Downstream selects by name, and a column order that follows the data is not a contract."""
    cache_dir = write_emdat_cache([emdat_event({"Disaster Type": "Flood"})])

    events = load_emdat_data(cache_dir)["df_prob_filtered_adjusted"]

    assert events.columns == ["ISO", "Start_Year", "Region", "Subregion", *DISASTER_TYPES]
