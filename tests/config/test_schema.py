import dataclasses

import pytest

from climate_risk.config.schema import CountryConfig, EventFilters, RegionConfig


@pytest.mark.parametrize("code", ["la", "LAOS", "lao", "L4O", ""], ids=repr)
def test_a_country_code_that_is_not_alpha_3_is_rejected(code):
    """Every frame keys countries on this, so a malformed code fails a join far from its cause."""
    with pytest.raises(ValueError, match="alpha-3"):
        CountryConfig(iso3=code, name="Somewhere")


def test_a_region_repeating_a_member_is_rejected():
    """A repeated member would sample and count that country twice."""
    with pytest.raises(ValueError, match="repeats"):
        RegionConfig(key="sea", name="Southeast Asia", members=("LAO", "THA", "LAO"))


def test_a_region_with_no_members_is_rejected():
    """An empty region silently produces an empty grid rather than an error."""
    with pytest.raises(ValueError, match="no members"):
        RegionConfig(key="empty", name="Nowhere", members=())


def test_a_region_member_that_is_not_alpha_3_is_rejected():
    with pytest.raises(ValueError, match="alpha-3"):
        RegionConfig(key="sea", name="Southeast Asia", members=("LAO", "Thailand"))


def test_a_window_ending_before_it_starts_is_rejected():
    """The filters read as a range; reversed, they select nothing and the panel comes back empty."""
    with pytest.raises(ValueError, match="ends before it starts"):
        EventFilters(start_year=2000, end_year=1990)


def test_a_place_cannot_be_edited_after_it_is_built():
    """Configs are read once and passed everywhere; a mutable one is action at a distance.

    mypy rejects the direct assignment, so the runtime guard is reached through `setattr` — dropping
    `frozen=True` would silence the type error and this is what would still catch it.
    """
    place = CountryConfig(iso3="LAO", name="Lao PDR")
    # Named indirectly: a literal assignment is a mypy error and a literal setattr is a ruff one,
    # and the point is to reach the runtime guard that survives if `frozen=True` is ever dropped.
    attribute = "iso3"

    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(place, attribute, "ZMB")
