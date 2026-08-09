import re

import pytest

from climate_risk.data_functions.event_geography import _load_disaster_point_data, load_data

# A legacy cache spells longitude `long`; the value under `lon` is the one to keep.
STALE_LON = 9.9
CURRENT_LON = 102.5


def test_missing_geocoded_locations_names_the_file_it_looked_for(tmp_path):
    """The message is the only guidance a fresh clone gets, so it has to say which file is absent."""
    with pytest.raises(ValueError, match=re.escape("disaster_locations_gpt_repaired_w_features.csv")):
        _load_disaster_point_data(tmp_path)


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
