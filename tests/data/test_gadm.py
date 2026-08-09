import re

import pytest

from climate_risk.data.gadm import GADM, gadm_dir, gadm_path
from climate_risk.data.source import ManualSource


def test_the_geopackage_is_looked_for_under_the_cache(tmp_path):
    assert gadm_dir(tmp_path) == tmp_path / "gadm"


def test_an_absent_geopackage_names_the_path_and_where_to_get_it(tmp_path):
    """The licence forbids fetching it, so the error is the user's only instruction."""
    with pytest.raises(NotImplementedError) as raised:
        gadm_path(tmp_path)

    message = str(raised.value)
    assert str(tmp_path / "gadm" / "gadm_410.gpkg") in message
    assert "https://gadm.org" in message


def test_a_placed_geopackage_is_returned(tmp_path):
    placed = tmp_path / "gadm" / "gadm_410.gpkg"
    placed.parent.mkdir()
    placed.touch()

    assert gadm_path(tmp_path) == placed


def test_the_declaration_states_its_licence_and_citation():
    """Non-commercial terms bind every figure built from these boundaries, so they are recorded here.

    Asserted on content rather than mere non-emptiness: a placeholder would satisfy `!= ""`.
    """
    assert "non-commercial" in GADM.licence.lower()
    assert "gadm.org" in GADM.citation
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", GADM.retrieved)


def test_gadm_is_not_a_fetchable_source():
    """Its terms forbid automated download, so it must not reach `fetch` or the reachability check.

    `ManualSource` carries no url, and this pins that: growing one would make the registry able to
    download a file the licence says a person must obtain.
    """
    assert isinstance(GADM, ManualSource)
    assert not hasattr(GADM, "url")
