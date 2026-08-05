import re

from climate_risk.geo.island_countries import ISLAND_COUNTRY_ISO3

LANDLOCKED = {"BOL", "PRY", "AUT", "CHE", "MNG", "NPL", "ZWE", "UGA", "LAO"}
UNAMBIGUOUS_ISLANDS = {"JPN", "PHL", "IDN", "NZL", "ISL", "CUB", "MDG", "LKA", "MDV", "FJI"}
CONTINENTAL = {"ARG", "BEL", "CHN", "HND", "MOZ", "SOM", "URY", "USA", "IND", "FRA"}


def test_no_landlocked_country_is_an_island():
    """The scrape this set replaced flagged Bolivia and Paraguay, which have no coast at all."""
    assert not ISLAND_COUNTRY_ISO3 & LANDLOCKED


def test_no_country_with_a_continental_border_is_an_island():
    assert not ISLAND_COUNTRY_ISO3 & CONTINENTAL


def test_the_unambiguous_island_countries_are_present():
    assert UNAMBIGUOUS_ISLANDS <= ISLAND_COUNTRY_ISO3


def test_every_entry_is_a_well_formed_iso3_code():
    """The set is hand-maintained, and a typo silently reclassifies a country."""
    malformed = {code for code in ISLAND_COUNTRY_ISO3 if not re.fullmatch(r"[A-Z]{3}", code)}

    assert not malformed
