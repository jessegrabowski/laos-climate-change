import pytest

from climate_risk.config.registry import CONFIG_ROOT, load_place, read_place, resolve_isos
from climate_risk.config.schema import CountryConfig, EventFilters, GeometrySpec, RegionConfig
from climate_risk.data.world_bank import COUNTRY_CODE_BY_NAME

# Walked rather than listed, so a place file that ships without a test still has to parse.
SHIPPED_PLACES = sorted(CONFIG_ROOT.glob("*/*.toml"))


def test_at_least_one_place_ships():
    """The conformance test below is parameterised over a glob, and an empty glob asserts nothing."""
    assert SHIPPED_PLACES


@pytest.mark.parametrize("path", SHIPPED_PLACES, ids=lambda path: f"{path.parent.name}/{path.name}")
def test_every_shipped_place_parses(path):
    """A place file is data, so nothing else would catch a typo in it until someone ran that country."""
    place = read_place(path)

    assert place.name
    assert resolve_isos(place)


@pytest.mark.parametrize("path", SHIPPED_PLACES, ids=lambda path: f"{path.parent.name}/{path.name}")
def test_a_place_is_filed_under_the_key_it_declares(path):
    """`load_place` finds files by stem, so a mismatch makes a place unreachable by its own name."""
    place = read_place(path)
    declared = place.iso3.lower() if isinstance(place, CountryConfig) else place.key

    assert path.stem == declared


def test_laos_carries_its_own_boundary_archive():
    """Stated literally, because this file is the only record of the archive and the layer to read."""
    place = load_place("lao")

    assert isinstance(place, CountryConfig)
    assert place.boundary is not None
    assert place.boundary.source.filename == "lao_admin_boundaries.shp.zip"
    assert place.boundary.member == "lao_admin2.shp"


def test_laos_carries_its_six_coordinate_overrides():
    """Stated literally, because this file is the only record of which events are mispositioned."""
    place = load_place("lao")

    assert isinstance(place, CountryConfig)
    assert place.event_location_overrides == {
        "1971-0048-LAO": (102.6331, 17.9757),
        "2000-0583-LAO": (102.0, 19.0),
        "2013-0338-LAO": (103.5, 19.5),
        "2013-0417-LAO": (106.0, 16.5),
        "2015-0324-LAO": (104.0, 19.0),
        "2016-0316-LAO": (102.1, 19.9),
    }


def test_laos_takes_the_project_defaults_it_does_not_override():
    """Compared against the schema, not against literals, which would freeze the defaults here too."""
    place = load_place("lao")

    assert place.geometry == GeometrySpec()
    assert place.events == EventFilters()


def test_southeast_asia_holds_its_nine_members():
    """Stated literally, because this file is the only record of the list, so a silent edit must fail."""
    place = load_place("sea")

    assert isinstance(place, RegionConfig)
    assert place.members == ("MMR", "THA", "LAO", "KHM", "VNM", "IDN", "MYS", "PHL", "TLS")


def test_laos_sits_inside_southeast_asia():
    """A sea grid that did not contain Laos would cover the wrong place."""
    assert set(resolve_isos(load_place("lao"))) < set(resolve_isos(load_place("sea")))


@pytest.mark.parametrize("path", SHIPPED_PLACES, ids=lambda path: f"{path.parent.name}/{path.name}")
def test_every_place_names_codes_the_world_bank_knows(path):
    """A well-formed code for a country that does not exist slices an empty world and yields no points.

    Checked against the World Bank country table rather than the project's own region lists, which
    is where these codes were copied from and so cannot disagree with them.
    """
    place = read_place(path)

    unknown = sorted(set(resolve_isos(place)) - set(COUNTRY_CODE_BY_NAME.values()))

    assert not unknown, f"{path.name} names {unknown}"
