import pytest

from climate_risk import process_ipcc_scenarios
from tests.conftest import NetworkAccessError


def test_force_reload_survives_an_existing_cache_dir(tmp_path):
    """force_reload once called mkdir on a directory that already existed."""
    with pytest.raises(NetworkAccessError):
        process_ipcc_scenarios(tmp_path, force_reload=True)
