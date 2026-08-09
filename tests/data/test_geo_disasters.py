from pathlib import Path

import pytest

from climate_risk.data.geo_disasters import (
    GEO_DISASTERS,
    geo_disasters_dir,
    geo_disasters_path,
    load_event_locations,
    unit_names,
)


def test_the_geopackage_is_looked_for_under_the_cache(tmp_path):
    assert geo_disasters_dir(tmp_path) == tmp_path / "geo_disasters"


def test_an_absent_geopackage_names_the_path_and_where_to_get_it(tmp_path):
    """Nothing may fetch this, so the error is the user's only instruction."""
    with pytest.raises(NotImplementedError) as raised:
        geo_disasters_path(tmp_path)

    message = str(raised.value)
    assert str(tmp_path / "geo_disasters" / "disaster_subnational_90_23.gpkg") in message
    assert "10.5281/zenodo.15487667" in message


def test_the_declaration_splits_the_licence_by_what_it_covers():
    """The geometry is non-commercial and the attributes are not; a figure built from one is
    constrained where the other is free, so both halves have to survive in the declaration."""
    licence = GEO_DISASTERS.licence.lower()

    assert "non-commercial" in licence
    assert "cc-by-4.0" in licence
    assert "zenodo.15487667" in GEO_DISASTERS.citation


def test_locations_come_back_keyed_on_the_em_dat_id(write_geo_disasters_cache):
    """`DisNo.` is the only key shared with EM-DAT, and one event spans several rows."""
    cache_dir = write_geo_disasters_cache()

    locations = load_event_locations(cache_dir)

    assert sorted(locations["DisNo."].unique()) == ["1991-0761-LAO", "2007-0225-ZMB", "2018-0339-LAO"]
    assert (locations["DisNo."] == "1991-0761-LAO").sum() == 2


def test_one_country_can_be_read_without_the_rest(write_geo_disasters_cache):
    """The real table is 45,000 rows across 206 countries, and a comparison wants one of them."""
    cache_dir = write_geo_disasters_cache()

    locations = load_event_locations(cache_dir, iso="LAO")

    assert set(locations["ISO"]) == {"LAO"}
    assert len(locations) == 3


def test_an_iso_the_table_does_not_hold_reads_back_empty(write_geo_disasters_cache):
    """A country with no geocoded events is the normal case, not an error."""
    cache_dir = write_geo_disasters_cache()

    locations = load_event_locations(cache_dir, iso="CRI")

    assert locations.empty
    assert list(locations.columns) == ["DisNo.", "ISO", "admin_level", "geocoding_q", "ADM1_NAME", "ADM2_NAME"]


def test_a_unit_is_named_at_the_level_it_was_geocoded_to(write_geo_disasters_cache):
    """A district row carries its province name too, so reading ADM1_NAME everywhere silently
    coarsens every level-2 location to the province containing it."""
    cache_dir = write_geo_disasters_cache()
    locations = load_event_locations(cache_dir, iso="LAO")

    named = unit_names(locations)

    by_event = dict(zip(locations["DisNo."], named, strict=True))
    assert by_event["2018-0339-LAO"] == "Sanamxay"
    assert set(named) == {"Savannakhet", "Khammouan", "Sanamxay"}


def test_geometry_is_left_on_disk(write_geo_disasters_cache):
    """The polygons are the non-commercial half of the licence, and nothing here needs them."""
    cache_dir = write_geo_disasters_cache()

    locations = load_event_locations(cache_dir)

    assert "geometry" not in locations.columns


# The GeoPackage is non-commercial and hand-placed, so it is absent on CI and on a fresh clone.
REAL_CACHE_DIR = Path(__file__).parents[2] / "data"
REAL_GEOPACKAGE = REAL_CACHE_DIR / "geo_disasters" / "disaster_subnational_90_23.gpkg"


@pytest.mark.requires_geo_disasters
@pytest.mark.skipif(not REAL_GEOPACKAGE.exists(), reason="needs the Geo-Disasters GeoPackage")
def test_the_published_table_is_the_one_the_loader_expects():
    """A synthetic fixture agrees with the loader by construction. This is the only check that the
    real archive still has the schema and the scale the paper describes."""
    locations = load_event_locations(REAL_CACHE_DIR)

    assert len(locations) == 45_121
    assert locations["DisNo."].nunique() == 9_217
    assert set(locations["admin_level"]) == {1, 2}
    assert locations["geocoding_q"].between(1, 4).all()
    assert unit_names(locations).notna().all(), "every location must be named at its own level"
