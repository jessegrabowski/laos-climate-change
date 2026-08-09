import re

import pandas as pd
import pytest

from climate_risk.data_functions.event_geography import (
    _load_disaster_point_data,
    load_data,
    load_disaster_point_data,
)
from tests.conftest import emdat_event

# A legacy cache spells longitude `long`; the value under `lon` is the one to keep.
STALE_LON = 9.9
CURRENT_LON = 102.5

# Points carry the distance features already, so the loader takes its warm path and needs no
# rivers or coastline. What is under test is the join, not the geometry.
GEOCODED_COLUMNS = {"distance_to_river": 1.0, "distance_to_coastline": 2.0, "is_island": False}


def test_missing_geocoded_locations_names_the_file_it_looked_for(tmp_path):
    """The message is the only guidance a fresh clone gets, so it has to say which file is absent."""
    with pytest.raises(ValueError, match=re.escape("disaster_locations_gpt_repaired_w_features.csv")):
        _load_disaster_point_data(tmp_path)


def test_points_follow_their_event_when_the_workbook_grows(tmp_path, write_emdat_cache):
    """EM-DAT inserts historical records on re-download, which moves every later row's position.

    Keyed on position, one inserted row shifts every point onto its neighbour's event and nothing
    raises — the failure this test exists for. The workbook is written with the inserted row first
    and the points in a third order, so only a join by id can pair them correctly.
    """
    write_emdat_cache(
        [
            emdat_event({"DisNo.": "1985-9999-ZZZ", "ISO": "ZZZ", "Start Year": 1985, "End Year": 1985}),
            emdat_event({"DisNo.": "1990-0001-AAA", "ISO": "AAA", "Start Year": 1990, "End Year": 1990}),
            emdat_event({"DisNo.": "1991-0002-BBB", "ISO": "BBB", "Start Year": 1991, "End Year": 1991}),
            emdat_event({"DisNo.": "1992-0003-CCC", "ISO": "CCC", "Start Year": 1992, "End Year": 1992}),
        ]
    )
    pd.DataFrame(
        [
            {"DisNo.": "1992-0003-CCC", "location_id": 0, "lon": 30.0, "lat": 0.5, **GEOCODED_COLUMNS},
            {"DisNo.": "1990-0001-AAA", "location_id": 0, "lon": 10.0, "lat": 0.5, **GEOCODED_COLUMNS},
            {"DisNo.": "1991-0002-BBB", "location_id": 0, "lon": 20.0, "lat": 0.5, **GEOCODED_COLUMNS},
        ]
    ).to_csv(tmp_path / "disaster_locations_gpt_repaired_w_features.csv", index=False)

    data = load_disaster_point_data(tmp_path).reset_index()

    attached = dict(zip(data["DisNo."], data["ISO"], strict=True))
    assert attached == {"1990-0001-AAA": "AAA", "1991-0002-BBB": "BBB", "1992-0003-CCC": "CCC"}

    # And the point itself travelled with its event, not just the label.
    longitudes = dict(zip(data["DisNo."], data.geometry.x, strict=True))
    assert longitudes == {"1990-0001-AAA": 10.0, "1991-0002-BBB": 20.0, "1992-0003-CCC": 30.0}


def test_a_positionally_keyed_point_file_is_refused(tmp_path, write_emdat_cache):
    """The file shipped in this repo is keyed on row number, and loading it silently mis-joins.

    Refusing is the whole point: the failure it replaces produced Peruvian coordinates for Lao
    events with no error at all.
    """
    write_emdat_cache([emdat_event()])
    pd.DataFrame({"emdat_index": [0], "location_id": [0], "lon": [10.0], "lat": [0.5]}).to_csv(
        tmp_path / "disaster_locations_gpt_repaired_w_features.csv", index=False
    )

    with pytest.raises(ValueError, match=re.escape("has no `DisNo.` column")):
        load_disaster_point_data(tmp_path)


def test_a_stale_row_number_on_the_point_file_is_ignored(tmp_path, write_emdat_cache):
    """A file written before the re-key still carries `emdat_index`, which identifies nothing."""
    write_emdat_cache([emdat_event({"DisNo.": "1990-0001-AAA", "ISO": "AAA"})])
    pd.DataFrame(
        [
            {
                "DisNo.": "1990-0001-AAA",
                "emdat_index": 4321,
                "location_id": 0,
                "lon": 10.0,
                "lat": 0.5,
                **GEOCODED_COLUMNS,
            }
        ]
    ).to_csv(tmp_path / "disaster_locations_gpt_repaired_w_features.csv", index=False)

    data = load_disaster_point_data(tmp_path).reset_index()

    assert data["ISO"].tolist() == ["AAA"]
    assert "emdat_index" not in data.columns


def test_a_point_whose_event_is_absent_carries_no_event_columns(tmp_path, write_emdat_cache):
    """A file keyed on one workbook vintage holds events a later one has revised away.

    Such a point is kept with nulls rather than dropped or attached to something else, and the
    synthetic sampler is what discards it, on `Region`.
    """
    write_emdat_cache([emdat_event({"DisNo.": "1990-0001-AAA", "ISO": "AAA"})])
    pd.DataFrame(
        [
            {"DisNo.": "1990-0001-AAA", "location_id": 0, "lon": 10.0, "lat": 0.5, **GEOCODED_COLUMNS},
            {"DisNo.": "2099-9999-XXX", "location_id": 0, "lon": 20.0, "lat": 0.5, **GEOCODED_COLUMNS},
        ]
    ).to_csv(tmp_path / "disaster_locations_gpt_repaired_w_features.csv", index=False)

    data = load_disaster_point_data(tmp_path).reset_index()

    assert len(data) == 2
    orphan = data[data["DisNo."] == "2099-9999-XXX"]
    assert orphan["ISO"].isna().all()
    assert orphan["Region"].isna().all()
    # The point itself is intact, so the row is droppable downstream rather than corrupt.
    assert orphan.geometry.x.tolist() == [20.0]


def test_every_location_of_an_event_gets_that_event(tmp_path, write_emdat_cache):
    """Most located events name several units, so the join fans one event out over its points."""
    write_emdat_cache([emdat_event({"DisNo.": "1990-0001-AAA", "ISO": "AAA", "Total Affected": 7_000})])
    pd.DataFrame(
        [
            {"DisNo.": "1990-0001-AAA", "location_id": index, "lon": 10.0 + index, "lat": 0.5, **GEOCODED_COLUMNS}
            for index in range(3)
        ]
    ).to_csv(tmp_path / "disaster_locations_gpt_repaired_w_features.csv", index=False)

    data = load_disaster_point_data(tmp_path)

    assert data.index.names == ["DisNo.", "location_id"]
    assert data.index.get_level_values("location_id").tolist() == [0, 1, 2]
    assert data["Total_Affected"].tolist() == [7_000] * 3


def test_a_cache_may_spell_longitude_long(tmp_path):
    """A cache on disk may spell longitude `long`."""
    legacy = tmp_path / "points.csv"
    legacy.write_text(f"emdat_index,location_id,long,lat\n0,0,{CURRENT_LON},18.5\n")

    data = load_data(legacy)

    assert "lon" in data.columns
    assert "long" not in data.columns
    assert data.geometry.x.tolist() == [CURRENT_LON]


def test_a_cache_holding_both_spellings_keeps_one_lon(tmp_path):
    """Renaming unconditionally would give two columns named lon, and attribute lookup a frame."""
    half_migrated = tmp_path / "points.csv"
    half_migrated.write_text(f"emdat_index,location_id,long,lon,lat\n0,0,{STALE_LON},{CURRENT_LON},18.5\n")

    data = load_data(half_migrated)

    assert list(data.columns).count("lon") == 1
    assert data.geometry.x.tolist() == [CURRENT_LON]
    assert STALE_LON not in data.geometry.x.tolist()
