from datetime import date
from pathlib import Path

import polars as pl
import pytest

from climate_risk.config.registry import CONFIG_ROOT, load_place, resolve_isos
from climate_risk.config.schema import EventFilters
from climate_risk.data_functions.emdat_processing import (
    DISASTER_TYPES,
    EMDAT_WINDOW_START,
    count_events_by_type,
    country_year_grid,
    event_filter,
    load_emdat_events,
    total_damage,
)
from tests.conftest import emdat_event


def selected_events(cache_dir, *, filters=None):
    """The events a place's thresholds keep."""
    return load_emdat_events(cache_dir).filter(event_filter(filters or EventFilters()))


def count_panel(cache_dir, *, filters=None, window_start=EMDAT_WINDOW_START):
    """Those events counted over the full country-year grid, which is what the panel is built on."""
    raw = load_emdat_events(cache_dir)
    events = raw.filter(event_filter(filters or EventFilters()))

    return count_events_by_type(events, country_year_grid(raw, window_start=window_start))


WINDOW_START = date(1969, 1, 1)


def row(frame: pl.DataFrame, iso: str, year: str) -> dict:
    """The one row for a country and year, as a plain mapping."""
    match = frame.filter((pl.col("ISO") == iso) & (pl.col("Start_Year") == date.fromisoformat(year)))

    assert len(match) == 1, f"expected one row for {iso} {year}, got {len(match)}"
    return match.to_dicts()[0]


def test_missing_workbook_names_the_path_it_wants(tmp_path):
    """EM-DAT is licensed and hand-placed, so the error is the user's only instruction."""
    with pytest.raises(NotImplementedError, match=str(tmp_path / "emdat.xlsx")):
        load_emdat_events(tmp_path)


def test_empty_workbook_is_rejected(write_emdat_cache):
    with pytest.raises(ValueError, match="has no rows"):
        load_emdat_events(write_emdat_cache([]))


def test_workbook_missing_a_column_names_it(write_emdat_cache):
    """Nothing else detects upstream schema drift, so the loader has to."""
    event = emdat_event()
    del event["Total Affected"]

    with pytest.raises(ValueError, match=r"missing \['Total Affected'\]"):
        load_emdat_events(write_emdat_cache([event]))


def test_every_country_year_appears_even_without_events(write_emdat_cache):
    """Count models need zero-event country-years present as rows, not absent."""
    cache_dir = write_emdat_cache([emdat_event({"ISO": "AAA"}), emdat_event({"ISO": "BBB", "DisNo.": "1990-0002-BBB"})])

    events = count_panel(cache_dir)
    years = range(WINDOW_START.year, 1991)

    assert events.columns[:2] == ["ISO", "Start_Year"]
    assert set(events["ISO"]) == {"AAA", "BBB"}
    assert events["Start_Year"].n_unique() == len(years)
    assert len(events) == 2 * len(years)


def test_window_start_can_be_overridden(write_emdat_cache):
    cache_dir = write_emdat_cache([emdat_event({"Start Year": 1990})])

    years = count_panel(cache_dir, window_start=date(1985, 1, 1))

    assert years["Start_Year"].min() == date(1985, 1, 1)


def test_window_start_after_the_newest_event_is_rejected(write_emdat_cache):
    """An empty window would otherwise return every frame with zero rows and no error."""
    cache_dir = write_emdat_cache([emdat_event({"Start Year": 1990})])

    with pytest.raises(ValueError, match="every output frame would be empty"):
        count_panel(cache_dir, window_start=date(2001, 1, 1))


def test_a_year_without_events_is_nan_not_zero(write_emdat_cache):
    """The replication panel relies on this to distinguish no-data from no-disasters."""
    cache_dir = write_emdat_cache(
        [emdat_event({"Start Year": 1990}), emdat_event({"DisNo.": "later", "Start Year": 1995})]
    )

    events = count_panel(cache_dir)

    assert row(events, "AAA", "1990-01-01")["Flood"] == 1
    assert row(events, "AAA", "1991-01-01")["Flood"] is None


def test_region_metadata_survives_reindexing(write_emdat_cache):
    cache_dir = write_emdat_cache(
        [
            emdat_event({"Region": "Africa", "Subregion": "Eastern Africa"}),
            emdat_event({"DisNo.": "later", "Start Year": 2001, "Region": "Africa", "Subregion": "Eastern Africa"}),
        ]
    )

    events = count_panel(cache_dir)
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

    classes = load_emdat_events(cache_dir)["disaster_class"]

    assert classes.to_list() == [expected_class]


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

    kept = selected_events(cache_dir)["DisNo."]

    assert sorted(kept.to_list()) == ["first-year", "kept-no-deaths"]


def test_an_event_exactly_on_the_affected_threshold_does_not_count(write_emdat_cache):
    """The threshold is strict, and an event sitting on it is the only way to tell that apart."""
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "over", "Start Year": 1995, "Total Affected": 1_001}),
            emdat_event({"DisNo.": "exactly-on-it", "Start Year": 1995, "Total Affected": 1_000}),
        ]
    )

    kept = selected_events(cache_dir)["DisNo."]

    assert kept.to_list() == ["over"]


def test_the_adjusted_view_follows_the_filters_it_is_given(write_emdat_cache):
    """The window is a place's setting, so a place with a shorter one must get a shorter panel."""
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "in-window", "Start Year": 1995}),
            emdat_event({"DisNo.": "before-window", "Start Year": 1985}),
        ]
    )

    kept = selected_events(cache_dir, filters=EventFilters(start_year=1990))["DisNo."]

    assert kept.to_list() == ["in-window"]


def test_a_deaths_threshold_applies_only_when_a_place_sets_one(write_emdat_cache):
    """The default counts an event on reach alone, so a deadly-but-small event needs an explicit floor."""
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "deadly", "Start Year": 1995, "Total Deaths": 500}),
            emdat_event({"DisNo.": "harmless", "Start Year": 1995, "Total Deaths": 0}),
        ]
    )

    by_default = selected_events(cache_dir)["DisNo."]
    with_a_floor = selected_events(cache_dir, filters=EventFilters(min_deaths=100))["DisNo."]

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

    kept = selected_events(cache_dir, filters=EventFilters(end_year=2000))["DisNo."]

    assert kept.to_list() == ["in-window", "last-year"]


def test_damage_totals_sum_within_a_country_year_and_leave_empty_ones_null(write_emdat_cache):
    """A country-year with no events reads as null, which is what the panel's outer joins rely on.

    Zero would be a claim that nothing happened; null is the absence of a record.
    """
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "first", "Start Year": 1995, "Total Deaths": 10}),
            emdat_event({"DisNo.": "second", "Start Year": 1995, "Total Deaths": 5}),
        ]
    )
    raw = load_emdat_events(cache_dir)

    damage = total_damage(raw.filter(event_filter(EventFilters())), country_year_grid(raw))

    assert damage.filter(pl.col("Start_Year") == date(1995, 1, 1))["Deaths"].to_list() == [15.0]

    # Asserted to exist first: `is_null().all()` is vacuously true on a row the grid dropped.
    quiet_year = damage.filter(pl.col("Start_Year") == date(1994, 1, 1))
    assert len(quiet_year) == 1
    assert quiet_year["Deaths"].is_null().all()


def test_the_window_extends_to_the_newest_event(write_emdat_cache):
    """A refreshed download must extend the panel, not silently lose its newest years."""
    cache_dir = write_emdat_cache([emdat_event({"Start Year": 2025})])

    years = count_panel(cache_dir)["Start_Year"]

    assert years.max() == date(2025, 1, 1)
    assert years.min() == WINDOW_START


def test_mass_movement_events_reach_the_count_frames(write_emdat_cache):
    cache_dir = write_emdat_cache([emdat_event({"Disaster Type": "Mass movement (wet)"})])

    events = count_panel(cache_dir)

    assert row(events, "AAA", "1990-01-01")["Mass movement (wet)"] == 1


def test_the_workbook_row_number_survives_filtering(write_emdat_cache):
    """disaster_point_data stores this number in its own cache, so it keys back into the workbook."""
    cache_dir = write_emdat_cache(
        [
            emdat_event({"DisNo.": "too-early", "Start Year": 1975}),
            emdat_event({"DisNo.": "kept", "Start Year": 1990}),
        ]
    )

    assert load_emdat_events(cache_dir)["emdat_index"].to_list() == [0, 1]
    assert selected_events(cache_dir).filter(pl.col("DisNo.") == "kept")["emdat_index"].to_list() == [1]


def test_a_workbook_with_no_usable_year_is_rejected(write_emdat_cache):
    """A null Start_Year leaves the window with no end, which would otherwise fail deep in a join."""
    cache_dir = write_emdat_cache([emdat_event({"Start Year": None})])

    with pytest.raises(ValueError, match="Every Start_Year in the workbook is missing"):
        country_year_grid(load_emdat_events(cache_dir))


def test_every_disaster_type_gets_a_column_in_a_stable_order(write_emdat_cache):
    """Downstream selects by name, and a column order that follows the data is not a contract."""
    cache_dir = write_emdat_cache([emdat_event({"Disaster Type": "Flood"})])

    events = count_panel(cache_dir)

    assert events.columns == ["ISO", "Start_Year", "Region", "Subregion", *DISASTER_TYPES]


# The licensed workbook, which cannot be committed or fetched. Absent on CI and on a fresh clone.
REAL_CACHE_DIR = Path(__file__).parents[2] / "data"

SHIPPED_PLACE_KEYS = sorted(path.stem for path in (CONFIG_ROOT / "places").glob("*.toml"))


@pytest.mark.requires_emdat
@pytest.mark.skipif(not (REAL_CACHE_DIR / "emdat.xlsx").exists(), reason="needs the licensed EM-DAT workbook")
@pytest.mark.parametrize("key", SHIPPED_PLACE_KEYS)
def test_every_shipped_country_has_events_clearing_its_own_filters(key):
    """A country whose filters admit nothing yields an empty panel, and every later test passes on it.

    Synthetic fixtures cannot catch this: they contain whatever events the fixture author wrote.
    """
    place = load_place(key)
    events = selected_events(REAL_CACHE_DIR, filters=place.events)

    assert len(events.filter(pl.col("ISO").is_in(resolve_isos(place)))) > 0
