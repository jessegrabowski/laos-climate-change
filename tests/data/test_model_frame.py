import datetime

import polars as pl
import pytest

from climate_risk.data.model_frame import event_windows
from climate_risk.exceptions import DataValidationError


def workbook(*disnos, year=1995, iso="LAO"):
    """The columns `event_windows` reads off the filtered workbook."""
    return pl.DataFrame(
        {
            "DisNo.": list(disnos),
            "ISO": [iso] * len(disnos),
            "Start_Year": [datetime.date(year, 6, 1)] * len(disnos),
        }
    )


def placements(*rows):
    """One row per event-unit, shaped like `event_geography` output."""
    return pl.DataFrame(
        {
            "DisNo.": [row[0] for row in rows],
            "gid": [row[1] for row in rows],
            "geometry_source": [row[2] for row in rows],
        },
        schema={"DisNo.": pl.String, "gid": pl.String, "geometry_source": pl.String},
    )


def test_units_at_different_levels_join_into_one_window():
    """The window is what the sources reached, so a district and the province beside it are one
    observation rather than two, and neither is normalized to the other's level."""
    windows = event_windows(
        workbook("mixed"),
        placements(("mixed", "LAO.1.2_1", "gadm"), ("mixed", "LAO.2_1", "location_text")),
    )

    assert windows["gids"].to_list() == [["LAO.1.2_1", "LAO.2_1"]]
    assert windows["n_units"].to_list() == [2]


def test_an_event_no_source_placed_keeps_a_whole_country_window():
    """Dropping it would discard an event that happened; an empty window says the country is all
    that is known, which is what the country tier means."""
    windows = event_windows(workbook("unplaced"), placements(("unplaced", None, "country")))

    assert windows["gids"].to_list() == [[]]
    assert windows["n_units"].to_list() == [0]
    assert windows["finest_level"].to_list() == [None]


def test_the_finest_level_reads_the_deepest_unit_in_the_window():
    """Window size drives the dispersion term the model needs, so a window holding one district is
    not described by the province it also names."""
    windows = event_windows(
        workbook("deep"),
        placements(("deep", "LAO.1_1", "gadm"), ("deep", "LAO.1.2.3_1", "gadm")),
    )

    assert windows["finest_level"].to_list() == [3]


def test_the_best_source_names_the_window_when_tiers_disagree():
    """`GEOMETRY_SOURCES` is best first and is not alphabetical, so the ranking has to come from the
    tuple rather than from sorting the strings."""
    windows = event_windows(
        workbook("two-tiers"),
        placements(("two-tiers", "LAO.1_1", "location_text"), ("two-tiers", "LAO.2_1", "emdat_point")),
    )

    assert windows["geometry_source"].to_list() == ["location_text"]


def test_a_repeated_event_unit_pair_counts_once():
    """A unit reached twice is still one unit of window, and counting it twice would inflate the
    extent the dispersion term reads."""
    windows = event_windows(
        workbook("repeat"),
        placements(("repeat", "LAO.1_1", "gadm"), ("repeat", "LAO.1_1", "gadm")),
    )

    assert windows["gids"].to_list() == [["LAO.1_1"]]


def test_an_event_with_no_geography_row_is_an_error():
    """`event_geography` emits every event, so a missing one means the two frames were built from
    different workbooks and every window after it would be silently wrong."""
    with pytest.raises(DataValidationError, match="no geography row"):
        event_windows(workbook("placed", "orphan"), placements(("placed", "LAO.1_1", "gadm")))


def test_a_source_the_precedence_does_not_rank_is_an_error():
    """Ranking is by declaration order, so a source missing from `GEOMETRY_SOURCES` has no place in
    it. Silently ranking it last would hide a new tier behind whichever one it was written beside."""
    with pytest.raises(pl.exceptions.InvalidOperationError):
        event_windows(workbook("new-tier"), placements(("new-tier", "LAO.1_1", "satellite")))
