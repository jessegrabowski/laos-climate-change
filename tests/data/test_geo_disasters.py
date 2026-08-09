from pathlib import Path

import pytest

from climate_risk.data.geo_disasters import (
    AGREEMENT_LEVELS,
    GEO_DISASTERS,
    compare_event_units,
    event_unit_names,
    geo_disasters_dir,
    geo_disasters_path,
    load_event_locations,
    normalise_unit_name,
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


@pytest.mark.parametrize(
    ("published", "other"),
    [("Attapu", "attapu"), ("Bolikhamxai", "Bolikhamxai "), ("Xekong", "Xékong"), ("Xai-somboun", "Xaisomboun")],
    ids=["casing", "whitespace", "accent", "hyphen"],
)
def test_the_same_unit_spelled_two_ways_normalises_alike(published, other):
    """GADM and GAUL differ in casing, spacing, accents and hyphens for units that are the same one,
    and a literal comparison would report every one of these as the sources disagreeing."""
    assert normalise_unit_name(published) == normalise_unit_name(other)


def test_units_that_are_genuinely_different_stay_different():
    """Normalisation that collapses too far reports agreement everywhere and validates nothing."""
    assert normalise_unit_name("Savannakhet") != normalise_unit_name("Khammouan")


def test_a_different_romanisation_is_not_reconciled():
    """Normalisation handles typography, not spelling. `Xiangkhouang` and `Xiangkhoang` are one
    province under two romanisations, and they compare as different units — so a `partial` in the
    report is an upper bound on real disagreement, not a measurement of it."""
    assert normalise_unit_name("Xiangkhouang") != normalise_unit_name("Xiangkhoang")


def test_geo_disasters_names_are_collected_per_event(write_geo_disasters_cache):
    cache_dir = write_geo_disasters_cache()

    names = event_unit_names(load_event_locations(cache_dir, iso="LAO"))

    assert names == {"1991-0761-LAO": {"Savannakhet", "Khammouan"}, "2018-0339-LAO": {"Sanamxay"}}


@pytest.mark.parametrize(
    ("em_dat", "geo_disasters", "expected"),
    [
        ({"Savannakhet", "Khammouan"}, {"Savannakhet", "Khammouan"}, "exact"),
        ({"Vientiane", "Xaisomboun"}, {"Vientiane"}, "partial"),
        ({"Vientiane"}, {"Attapu"}, "disjoint"),
        (set(), {"Xekong", "Attapu"}, "gained"),
        ({"Bokeo"}, set(), "unmatched"),
    ],
    ids=["exact", "partial", "disjoint", "gained", "unmatched"],
)
def test_an_event_is_classified_by_how_the_two_geocodings_overlap(em_dat, geo_disasters, expected):
    report = compare_event_units({"E": em_dat}, {"E": geo_disasters})

    assert report["agreement"].tolist() == [expected]


def test_an_event_neither_source_geocoded_is_left_out():
    """Two thirds of EM-DAT carries no units at all; reporting them would bury the comparison."""
    report = compare_event_units({"E": set()}, {"E": set()})

    assert report.empty
    assert list(report.columns) == ["DisNo.", "agreement", "em_dat_units", "geo_disasters_units", "shared_units"]


def test_agreement_is_judged_after_normalisation():
    """The whole point of normalising: Xekong and Xékong are one province, not a disjoint pair."""
    report = compare_event_units({"E": {"Xékong"}}, {"E": {"Xekong"}})

    assert report["agreement"].tolist() == ["exact"]
    assert report["shared_units"].tolist() == [1]


def test_the_counts_describe_each_side_and_the_overlap():
    report = compare_event_units({"E": {"Vientiane", "Xaisomboun"}}, {"E": {"Vientiane", "Attapu"}})

    assert report.loc[0, "em_dat_units"] == 2
    assert report.loc[0, "geo_disasters_units"] == 2
    assert report.loc[0, "shared_units"] == 1


def test_every_event_either_source_geocoded_appears_once():
    """A join done the wrong way round silently drops whichever side is absent."""
    report = compare_event_units({"A": {"x"}, "B": {"y"}}, {"B": {"y"}, "C": {"z"}})

    assert report["DisNo."].tolist() == ["A", "B", "C"]


# The GeoPackage is non-commercial and hand-placed, so it is absent on CI and on a fresh clone.
REAL_CACHE_DIR = Path(__file__).parents[2] / "data"
REAL_GEOPACKAGE = REAL_CACHE_DIR / "geo_disasters" / "disaster_subnational_90_23.gpkg"


def test_every_classification_is_one_of_the_declared_levels():
    """`AGREEMENT_LEVELS` is the published vocabulary; a verdict outside it is one no caller can
    branch on."""
    report = compare_event_units(
        {"exact": {"a"}, "partial": {"a", "b"}, "disjoint": {"a"}, "unmatched": {"a"}},
        {"exact": {"a"}, "partial": {"a"}, "disjoint": {"z"}, "gained": {"a"}},
    )

    assert set(report["agreement"]) == set(AGREEMENT_LEVELS)


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
