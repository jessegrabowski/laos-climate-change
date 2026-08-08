import pytest

from climate_risk.config.registry import CONFIG_ROOT, load_place, read_place, resolve_isos
from climate_risk.config.schema import CountryConfig, EventFilters, GeometrySpec, RegionConfig
from climate_risk.data.world_bank import COUNTRY_CODE_BY_NAME
from climate_risk.data_functions.disaster_point_data import REGION_ISO_CODES
from climate_risk.data_functions.rivers_damage import LAOS_LOCATION_DICTIONARY
from climate_risk.data_functions.shapefiles_data_loader import SHAPEFILE_ARCHIVES

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


def test_laos_carries_the_boundary_the_loader_hardcodes():
    """The config has to reproduce current behaviour exactly, or Laos results move when it is adopted."""
    place = load_place("lao")

    assert isinstance(place, CountryConfig)
    assert place.boundary == SHAPEFILE_ARCHIVES["laos"]


def test_laos_carries_the_coordinate_overrides_the_loader_hardcodes():
    """Same reason, and these six are the ones currently applied to every country."""
    place = load_place("lao")

    assert isinstance(place, CountryConfig)
    expected = {
        event: (coordinates["Longitude"], coordinates["Latitude"])
        for event, coordinates in LAOS_LOCATION_DICTIONARY.items()
    }
    assert place.event_location_overrides == expected


def test_laos_takes_the_project_defaults_it_does_not_override():
    """Compared against the schema, not against literals, which would freeze the defaults here too."""
    place = load_place("lao")

    assert place.geometry == GeometrySpec()
    assert place.events == EventFilters()


def test_southeast_asia_matches_the_region_table_the_loader_hardcodes():
    place = load_place("sea")

    assert isinstance(place, RegionConfig)
    assert place.members == REGION_ISO_CODES["sea"]


@pytest.mark.parametrize("path", SHIPPED_PLACES, ids=lambda path: f"{path.parent.name}/{path.name}")
def test_every_place_names_codes_the_world_bank_knows(path):
    """A well-formed code for a country that does not exist slices an empty world and yields no points.

    Checked against the World Bank country table rather than the project's own region lists, which
    is where these codes were copied from and so cannot disagree with them.
    """
    place = read_place(path)

    unknown = sorted(set(resolve_isos(place)) - set(COUNTRY_CODE_BY_NAME.values()))

    assert not unknown, f"{path.name} names {unknown}"
